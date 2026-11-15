"""
FastAPI Server for MovieTap Web
Provides REST API endpoints, multi-provider search (MovieBox, Dramachi, 4KHDHub),
high-performance video streaming proxy with HTTP Range support, and direct in-browser downloads.
"""

import os
import re
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Query, Header, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx

import urllib.parse
from app.client import MovieBoxClient, STREAM_REFERER
from app.providers import SearchAggregator, DramachiProvider, FourKHdHubProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("movietap.server")

app = FastAPI(title="MovieTap Web Streamer", version="3.0.0")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Content-Length", "Accept-Ranges", "Content-Type", "Content-Disposition"]
)

# Initialize MovieBox client & multi-provider aggregator
client = MovieBoxClient()
try:
    client.ensure_session()
except Exception as e:
    logger.warning(f"Initial login deferred: {e}")

aggregator = SearchAggregator(client)

# Base directories
STATIC_DIR = Path(__file__).parent.parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Shared HTTP client for streaming proxy
http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    global http_client
    if http_client is None or http_client.is_closed:
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=60.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
        )
    return http_client

@app.on_event("startup")
async def startup_event():
    get_http_client()
    logger.info("MovieTap Web Server started")

@app.on_event("shutdown")
async def shutdown_event():
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None
        await http_client.aclose()

# ----------------- API Endpoints -----------------

@app.get("/api/homepage")
async def get_homepage(tab: str = "2", page: int = 1):
    """Fetch featured trending titles from MovieBox homepage"""
    try:
        items = client.get_homepage(tab_id=tab, page=page)
        return {"success": True, "count": len(items), "items": items}
    except Exception as e:
        logger.error(f"Homepage error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/search")
async def search_titles(q: str = Query(..., min_length=1), provider: str = "all", page: int = 1):
    """Search for movies, TV series, anime across MovieBox, Dramachi, and 4KHDHub"""
    try:
        items = await aggregator.multi_search(get_http_client(), q, provider=provider)
        return {"success": True, "query": q, "provider": provider, "count": len(items), "items": items}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/suggest")
async def get_suggestions(q: str = Query(..., min_length=1), provider: str = "all"):
    """Search autocomplete suggestions with poster images, title, year, and type"""
    try:
        items = await aggregator.multi_search(get_http_client(), q, provider=provider)
        suggestions = []
        for it in items[:8]:
            suggestions.append({
                "id": it["id"],
                "title": it["title"],
                "poster_url": it.get("poster_url", ""),
                "year": it.get("year", ""),
                "rating": it.get("rating", "8.5"),
                "is_series": it.get("is_series", False),
                "provider": it.get("provider", "MovieBox")
            })
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Suggest error: {e}")
        return {"success": False, "suggestions": []}

@app.get("/api/details")
async def get_details(id: str = Query(...)):
    """Fetch complete metadata for movie or series (synopsis, cast, seasons, dubs)"""
    try:
        if id.startswith("dramachi_"):
            dramachi = DramachiProvider(get_http_client())
            details = await dramachi.get_details(id)
            if details:
                return {"success": True, "details": details}
        
        details = client.get_details(id)
        return {"success": True, "details": details}
    except Exception as e:
        logger.error(f"Details error for ID {id}: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/streams")
async def get_streams(id: str = Query(...), season: int = 0, episode: int = 0):
    """
    Get all playable streams (1080p, 720p, 480p, 360p) for a movie or TV episode.
    Each stream includes a ready-to-play proxy URL that the web player can use.
    """
    try:
        if id.startswith("dramachi_"):
            dramachi = DramachiProvider(get_http_client())
            raw_streams = await dramachi.get_streams(id, season=season, episode=episode)
        else:
            raw_streams = client.get_streams(id, season=season, episode=episode)
        
        streams = []
        for s in raw_streams:
            stream_url = s["url"]
            proxied_url = f"/api/stream?url={urllib.parse.quote(stream_url, safe='')}"
            if s.get("sign_cookie"):
                proxied_url += f"&cookie={urllib.parse.quote(s['sign_cookie'], safe='')}"
            streams.append({
                **s,
                "proxy_url": proxied_url
            })
            
        return {
            "success": True,
            "id": id,
            "season": season,
            "episode": episode,
            "count": len(streams),
            "streams": streams
        }
    except Exception as e:
        logger.error(f"Streams error for ID {id} s{season}e{episode}: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/captions")
async def get_captions(id: str = Query(...), rid: Optional[str] = Query(None)):
    """Fetch subtitles and return WebVTT proxy links for HTML5 <track> elements"""
    try:
        if id.startswith("dramachi_"):
            return {"success": True, "captions": []}
            
        raw_captions = client.get_captions(id, rid or "")
        captions = []
        for cap in raw_captions:
            vtt_proxy_url = f"/api/subtitles/vtt?url={urllib.parse.quote(cap['url'], safe='')}"
            captions.append({
                **cap,
                "vtt_url": vtt_proxy_url
            })
        return {"success": True, "captions": captions}
    except Exception as e:
        logger.error(f"Captions error: {e}")
        return {"success": False, "captions": []}

@app.get("/api/subtitles/vtt")
async def get_vtt_subtitle(url: str = Query(...)):
    """
    Download SRT subtitle from upstream CDN and convert to standard WebVTT
    so modern web browsers can display subtitles natively in <video>.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as fetcher:
            resp = await fetcher.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch subtitle")
            
            content_bytes = resp.content
            try:
                text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content_bytes.decode('latin-1')
                except Exception:
                    text = content_bytes.decode('utf-8', errors='ignore')

        # Convert SRT timestamps (00:01:20,500) to WebVTT timestamps (00:01:20.500)
        vtt_lines = ["WEBVTT\n"]
        for line in text.splitlines():
            # Match timestamp line: 00:00:01,000 --> 00:00:04,000
            m = re.match(r"(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})", line)
            if m:
                vtt_lines.append(f"{m.group(1)}.{m.group(2)} --> {m.group(3)}.{m.group(4)}")
            else:
                vtt_lines.append(line)

        vtt_output = "\n".join(vtt_lines)
        return Response(content=vtt_output, media_type="text/vtt")
    except Exception as e:
        logger.error(f"Error converting subtitles to WebVTT: {e}")
        return Response(content="WEBVTT\n\n00:00:00.000 --> 00:00:05.000\n[Subtitles unavailable]", media_type="text/vtt")

@app.get("/api/download")
async def download_media(
    request: Request,
    url: str = Query(...),
    filename: Optional[str] = Query("MovieTap_Video"),
    subtitle_url: Optional[str] = Query(None),
    cookie: Optional[str] = Query(None)
):
    """
    Stream video with Content-Disposition attachment so the browser downloads
    the file directly to the user's Downloads directory.
    If subtitle_url is provided, ffmpeg muxes the subtitles directly into the MP4 file on the fly!
    """
    clean_fn = "".join(c for c in (filename or "MovieTap_Video") if c.isalnum() or c in " ._-").strip()
    if not clean_fn.lower().endswith(".mp4") and not clean_fn.lower().endswith(".mkv"):
        clean_fn += ".mp4"

    # If subtitle URL is provided, mux directly into the MP4 container via ffmpeg
    if subtitle_url and subtitle_url.strip() and not subtitle_url.strip().lower().startswith("none"):
        try:
            async with httpx.AsyncClient(timeout=15.0) as sub_client:
                sub_res = await sub_client.get(subtitle_url)
                sub_data = sub_res.text if sub_res.status_code == 200 else ""
            
            if sub_data and len(sub_data.strip()) > 10:
                with tempfile.NamedTemporaryFile(suffix=".vtt", delete=False, mode="w", encoding="utf-8") as tf:
                    tf.write(sub_data)
                    temp_sub_path = tf.name

                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-headers", f"User-Agent: {client.user_agent}\r\n",
                    "-i", url,
                    "-i", temp_sub_path,
                    "-c:v", "copy",
                    "-c:a", "copy",
                    "-c:s", "mov_text",
                    "-movflags", "frag_keyframe+empty_moov+default_base_moof",
                    "-f", "mp4",
                    "pipe:1"
                ]

                proc = await asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                async def ffmpeg_stream():
                    try:
                        while True:
                            chunk = await proc.stdout.read(128 * 1024)
                            if not chunk:
                                break
                            yield chunk
                    finally:
                        try:
                            if proc.returncode is None:
                                proc.terminate()
                                await proc.wait()
                        except Exception:
                            pass
                        try:
                            if os.path.exists(temp_sub_path):
                                os.unlink(temp_sub_path)
                        except Exception:
                            pass

                return StreamingResponse(
                    ffmpeg_stream(),
                    status_code=200,
                    headers={
                        "Content-Disposition": f'attachment; filename="{clean_fn}"',
                        "Content-Type": "video/mp4",
                    },
                    media_type="video/mp4"
                )
        except Exception as e:
            logger.warning(f"FFmpeg subtitle muxing error, falling back to direct stream: {e}")

    # Direct streaming fallback / single video file download
    try:
        req_headers = {
            "User-Agent": client.user_agent,
            "Accept": "*/*",
        }
        if ".mpd" in url.lower() or "dash" in url.lower():
            req_headers["Referer"] = STREAM_REFERER
        if cookie:
            req_headers["Cookie"] = cookie
        range_header = request.headers.get("range")
        if range_header:
            req_headers["Range"] = range_header

        h_client = get_http_client()
        upstream_req = h_client.build_request("GET", url, headers=req_headers)
        upstream_resp = await h_client.send(upstream_req, stream=True)

        if upstream_resp.status_code == 429 and "Referer" in req_headers:
            await upstream_resp.aclose()
            del req_headers["Referer"]
            upstream_req = h_client.build_request("GET", url, headers=req_headers)
            upstream_resp = await h_client.send(upstream_req, stream=True)

        response_headers = {
            "Content-Disposition": f'attachment; filename="{clean_fn}"',
            "Content-Type": "video/mp4",
            "Accept-Ranges": "bytes",
        }
        if "content-range" in upstream_resp.headers:
            response_headers["Content-Range"] = upstream_resp.headers["content-range"]
        if "content-length" in upstream_resp.headers:
            response_headers["Content-Length"] = upstream_resp.headers["content-length"]

        status_code = upstream_resp.status_code
        if range_header and status_code == 200:
            status_code = 206

        async def stream_generator():
            try:
                async for chunk in upstream_resp.aiter_bytes(chunk_size=128 * 1024):
                    yield chunk
            finally:
                await upstream_resp.aclose()

        return StreamingResponse(
            stream_generator(),
            status_code=status_code,
            headers=response_headers,
            media_type="video/mp4"
        )
    except Exception as e:
        logger.error(f"Download stream error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/download/subtitle")
async def download_subtitle(url: str = Query(...), filename: Optional[str] = Query("subtitle.srt")):
    """Directly download subtitle file into browser"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as fetcher:
            resp = await fetcher.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch subtitle")
            
            clean_fn = "".join(c for c in (filename or "subtitle.srt") if c.isalnum() or c in " ._-").strip()
            if not clean_fn.endswith(".srt") and not clean_fn.endswith(".vtt"):
                clean_fn += ".srt"

            return Response(
                content=resp.content,
                media_type="application/x-subrip",
                headers={"Content-Disposition": f'attachment; filename="{clean_fn}"'}
            )
    except Exception as e:
        logger.error(f"Subtitle download error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------------- Streaming Proxy (HTTP Range Support) -----------------

@app.get("/api/stream")
async def stream_proxy(
    request: Request,
    url: str = Query(...),
    cookie: Optional[str] = Query(None)
):
    """
    Streaming proxy with full HTTP 206 Partial Content byte-range support.
    Enables native HTML5 <video> seeking, buffering, and scrub without CORS/428 errors.
    """
    h_client = get_http_client()

    # Forward Range header from browser
    req_headers = {
        "User-Agent": client.user_agent,
        "Accept": "*/*",
    }
    # Direct media CDN rejects STREAM_REFERER with 429 (as documented in MovieBox-TUI adapt.rs line 597)
    if ".mpd" in url.lower() or "dash" in url.lower():
        req_headers["Referer"] = STREAM_REFERER
    
    range_header = request.headers.get("range")
    if range_header:
        req_headers["Range"] = range_header

    if cookie:
        req_headers["Cookie"] = cookie

    try:
        h_client = get_http_client()
        upstream_req = h_client.build_request("GET", url, headers=req_headers)
        upstream_resp = await h_client.send(upstream_req, stream=True)

        # If CDN returns 429 or 403, toggle Referer and retry
        if upstream_resp.status_code == 429 and "Referer" in req_headers:
            await upstream_resp.aclose()
            del req_headers["Referer"]
            upstream_req = h_client.build_request("GET", url, headers=req_headers)
            upstream_resp = await h_client.send(upstream_req, stream=True)
        elif upstream_resp.status_code in (403, 429) and "Referer" not in req_headers:
            await upstream_resp.aclose()
            req_headers["Referer"] = STREAM_REFERER
            upstream_req = h_client.build_request("GET", url, headers=req_headers)
            upstream_resp = await h_client.send(upstream_req, stream=True)

        # Build response headers matching upstream
        response_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": upstream_resp.headers.get("content-type", "video/mp4"),
            "Access-Control-Allow-Origin": "*",
        }

        if "content-range" in upstream_resp.headers:
            response_headers["Content-Range"] = upstream_resp.headers["content-range"]
        if "content-length" in upstream_resp.headers:
            response_headers["Content-Length"] = upstream_resp.headers["content-length"]

        status_code = upstream_resp.status_code
        if range_header and status_code == 200:
            status_code = 206

        async def stream_generator():
            try:
                async for chunk in upstream_resp.aiter_bytes(chunk_size=64 * 1024):
                    yield chunk
            finally:
                await upstream_resp.aclose()

        return StreamingResponse(
            stream_generator(),
            status_code=status_code,
            headers=response_headers,
            media_type=response_headers["Content-Type"]
        )

    except Exception as e:
        logger.error(f"Stream proxy error for {url}: {e}")
        return JSONResponse(status_code=502, content={"error": "Failed to stream media source", "details": str(e)})

# ----------------- Static Files & Frontend -----------------

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>MovieTap Frontend is building...</h1>")
    return FileResponse(index_file)
