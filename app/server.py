"""
FastAPI Server for MovieTap Web
Provides REST API endpoints, multi-provider search (MovieBox, Dramachi, 4KHDHub),
high-performance video streaming proxy with HTTP Range support, and direct in-browser downloads.
"""

import os
import re
import time
import base64
import asyncio
import tempfile
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

app = FastAPI(title="Room 206 Web Streamer", version="3.0.0")

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

# In-memory cache for fast response times
HOMEPAGE_CACHE = {}
HOMEPAGE_CACHE_TIME = {}
CACHE_TTL = 900  # 15 minutes

def get_cached_catalog(key: str) -> Optional[list]:
    now = time.time()
    if key in HOMEPAGE_CACHE and (now - HOMEPAGE_CACHE_TIME.get(key, 0) < CACHE_TTL):
        return HOMEPAGE_CACHE[key]
    return None

def set_cached_catalog(key: str, data: list):
    HOMEPAGE_CACHE[key] = data
    HOMEPAGE_CACHE_TIME[key] = time.time()

# MCU release order (Latest on top, down to Iron Man 2008 at the bottom)
MCU_CHRONOLOGY = [
    'brand new day', 'doomsday', 'brave new world', 'thunderbolts', 'deadpool & wolverine',
    'the marvels', 'guardians of the galaxy vol. 3', 'quantumania',
    'wakanda forever', 'love and thunder', 'multiverse of madness', 'no way home',
    'eternals', 'shang-chi', 'black widow', 'far from home', 'endgame', 'captain marvel',
    'ant-man and the wasp', 'infinity war', 'black panther', 'ragnarok', 'homecoming',
    'guardians of the galaxy vol. 2', 'doctor strange', 'civil war', 'ant-man',
    'age of ultron', 'the winter soldier', 'iron man 3', 'the avengers',
    'first avenger', 'thor', 'iron man 2', 'the incredible hulk', 'iron man'
]

def mcu_sort_key(item):
    t = (item.get('title') or '').lower()
    y_str = str(item.get('year') or '2015')
    try:
        y = int(y_str[:4])
    except Exception:
        y = 2015
    
    # Iron Man (2008) is the absolute first MCU film, placed at the very bottom!
    if 'iron man' in t and y == 2008 and '2' not in t and '3' not in t:
        return 999999
    if 'incredible hulk' in t and y == 2008:
        return 999990
    
    # Otherwise sort descending by release year (latest on top)
    return -y

async def fetch_marvel_catalog() -> list:
    loop = asyncio.get_event_loop()
    mcu_search_terms = [
        # MCU Movies Chronology: Latest down to 2008
        "Avengers: Secret Wars", "Avengers: Doomsday", "Spider-Man: Brand New Day",
        "Thunderbolts", "Captain America: Brave New World", "Deadpool & Wolverine",
        "The Marvels", "Guardians of the Galaxy Vol. 3", "Ant-Man and the Wasp: Quantumania",
        "Black Panther: Wakanda Forever", "Thor: Love and Thunder", "Doctor Strange in the Multiverse of Madness",
        "Spider-Man: No Way Home", "Eternals", "Shang-Chi", "Black Widow",
        "Spider-Man: Far From Home", "Avengers: Endgame", "Captain Marvel",
        "Ant-Man and the Wasp", "Avengers: Infinity War", "Black Panther",
        "Thor: Ragnarok", "Spider-Man: Homecoming", "Guardians of the Galaxy Vol. 2",
        "Doctor Strange", "Captain America: Civil War", "Ant-Man", "Avengers: Age of Ultron",
        "Guardians of the Galaxy", "Captain America: The Winter Soldier", "Thor: The Dark World",
        "Iron Man 3", "The Avengers", "Captain America: The First Avenger", "Thor",
        "Iron Man 2", "The Incredible Hulk", "Iron Man"
    ]
    sem = asyncio.Semaphore(10)

    async def search_term(term):
        async with sem:
            try:
                res = await loop.run_in_executor(None, client.search, term, 1)
                return [it for it in (res[:2] if res else []) if not it.get("is_series")]
            except Exception:
                return []

    results = await asyncio.gather(*[search_term(t) for t in mcu_search_terms])
    raw_items = [item for sublist in results for item in sublist]
    
    unique = []
    seen = set()
    for r in raw_items:
        sid = r.get("id")
        if sid and sid not in seen and not r.get("is_series"):
            seen.add(sid)
            unique.append(r)
            
    unique.sort(key=mcu_sort_key)
    return unique

async def fetch_anime_catalog() -> list:
    loop = asyncio.get_event_loop()
    mb_items = []
    try:
        raw_mb = await loop.run_in_executor(None, client.get_homepage, "3", 1)
        mb_items = [it for it in raw_mb if not it.get("is_series")]
    except Exception:
        pass
    
    popular_queries = ["Demon Slayer Mugen Train", "Suzume", "Your Name", "Spirited Away", "Jujutsu Kaisen 0", "Weathering with You", "A Silent Voice", "Princess Mononoke", "Howl's Moving Castle", "The Boy and the Heron"]
    popular_items = []
    for q in popular_queries:
        try:
            res = await loop.run_in_executor(None, client.search, q, 1)
            if res:
                for it in res:
                    if not it.get("is_series"):
                        popular_items.append(it)
                        break
        except Exception:
            pass

    combined = []
    seen = set()
    for item in popular_items + mb_items:
        sid = item.get("id")
        if sid and sid not in seen and not item.get("is_series"):
            seen.add(sid)
            combined.append(item)
    return combined

async def prewarm_cache():
    loop = asyncio.get_event_loop()
    for tab in ["all", "movies", "anime", "marvel"]:
        try:
            if tab == "marvel":
                items = await fetch_marvel_catalog()
            elif tab == "anime":
                items = await fetch_anime_catalog()
            else:
                items = await loop.run_in_executor(None, client.get_homepage, tab, 1)
            set_cached_catalog(f"{tab}_1", items)
            logger.info(f"Pre-warmed cache for tab '{tab}': {len(items)} items")
        except Exception as e:
            logger.warning(f"Failed pre-warming tab '{tab}': {e}")
            logger.warning(f"Failed pre-warming tab '{tab}': {e}")

@app.on_event("startup")
async def startup_event():
    get_http_client()
    logger.info("Room 206 Web Server started")
    asyncio.create_task(prewarm_cache())

@app.on_event("shutdown")
async def shutdown_event():
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None

# ----------------- API Endpoints -----------------

@app.get("/api/homepage")
async def get_homepage(tab: str = "2", page: int = 1):
    """Fetch featured trending titles from Room 206 catalog (Cached for instantaneous load, movies only)"""
    cache_key = f"{tab.lower()}_{page}"
    cached = get_cached_catalog(cache_key)
    if cached is not None:
        filtered = [it for it in cached if not it.get("is_series")]
        return {"success": True, "count": len(filtered), "items": filtered, "cached": True}

    try:
        if tab.lower() == "marvel":
            items = await fetch_marvel_catalog()
        elif tab.lower() in ["anime", "animes", "animation"]:
            items = await fetch_anime_catalog()
        else:
            loop = asyncio.get_event_loop()
            items = await loop.run_in_executor(None, client.get_homepage, tab, page)
            
        items = [it for it in items if not it.get("is_series")]
        set_cached_catalog(cache_key, items)
        return {"success": True, "count": len(items), "items": items, "cached": False}
    except Exception as e:
        logger.error(f"Homepage error for tab {tab}: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/marvel")
async def get_marvel_movies():
    """Returns Marvel MCU titles in release order: Latest on top, Iron Man (2008) at the bottom!"""
    cached = get_cached_catalog("marvel_1")
    if cached is not None:
        filtered = [it for it in cached if not it.get("is_series")]
        return {"success": True, "count": len(filtered), "items": filtered}
    items = await fetch_marvel_catalog()
    items = [it for it in items if not it.get("is_series")]
    set_cached_catalog("marvel_1", items)
    return {"success": True, "count": len(items), "items": items}

@app.get("/api/search")
async def search_titles(q: str = Query(..., min_length=1), provider: str = "all", page: int = 1):
    """Search for movies across MovieBox, Dramachi, and 4KHDHub (TV shows excluded)"""
    try:
        items = await aggregator.multi_search(get_http_client(), q, provider=provider)
        items = [it for it in items if not it.get("is_series")]
        return {"success": True, "query": q, "provider": provider, "count": len(items), "items": items}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/suggest")
async def get_suggestions(q: str = Query(..., min_length=1), provider: str = "all"):
    """Search autocomplete suggestions with poster images, title, year, and type (Movies only)"""
    try:
        items = await aggregator.multi_search(get_http_client(), q, provider=provider)
        items = [it for it in items if not it.get("is_series")]
        suggestions = []
        for it in items[:8]:
            suggestions.append({
                "id": it["id"],
                "title": it["title"],
                "poster_url": it.get("poster_url", ""),
                "year": it.get("year", ""),
                "rating": it.get("rating", "8.5"),
                "is_series": False,
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
    filename: Optional[str] = Query("Room206_Video"),
    subtitle_url: Optional[str] = Query(None),
    cookie: Optional[str] = Query(None)
):
    """
    Stream video with Content-Disposition attachment so the browser downloads
    the file directly to the user's Downloads directory.
    If subtitle_url is provided, ffmpeg muxes the subtitles directly into the MP4 file on the fly!
    If the stream is DASH (.mpd), ffmpeg remuxes it into a unified .mp4 file!
    """
    clean_fn = "".join(c for c in (filename or "Room206_Video") if c.isalnum() or c in " ._-").strip()
    if not clean_fn.lower().endswith(".mp4") and not clean_fn.lower().endswith(".mkv"):
        clean_fn += ".mp4"

    ffmpeg_headers = f"User-Agent: {client.user_agent}\r\n"
    if ".mpd" in url.lower() or "dash" in url.lower():
        ffmpeg_headers += f"Referer: {STREAM_REFERER}\r\n"
    if cookie:
        ffmpeg_headers += f"Cookie: {cookie}\r\n"

    # Option 1: Subtitle provided -> Mux video and subtitle into single MP4
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
                    "-headers", ffmpeg_headers,
                    "-i", url,
                    "-i", temp_sub_path,
                    "-c:v", "copy",
                    "-c:a", "copy",
                    "-c:s", "mov_text",
                    "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
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

    # Option 2: DASH stream without subtitle -> Remux DASH into unified MP4
    if ".mpd" in url.lower() or "dash" in url.lower():
        try:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-headers", ffmpeg_headers,
                "-i", url,
                "-c:v", "copy",
                "-c:a", "copy",
                "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
                "-f", "mp4",
                "pipe:1"
            ]
            proc = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            async def dash_download_stream():
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

            return StreamingResponse(
                dash_download_stream(),
                status_code=200,
                headers={
                    "Content-Disposition": f'attachment; filename="{clean_fn}"',
                    "Content-Type": "video/mp4",
                },
                media_type="video/mp4"
            )
        except Exception as ex:
            logger.warning(f"DASH ffmpeg remux download failed: {ex}")

    # Option 3: Direct MP4 streaming fallback
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

# ----------------- Progressive MP4 Remux Stream Proxy -----------------

@app.get("/api/stream_mp4")
async def stream_mp4_proxy(
    request: Request,
    url: str = Query(...),
    cookie: Optional[str] = Query(None)
):
    """
    On-the-fly progressive MP4 remuxing stream proxy.
    Allows DASH streams or raw CDN streams to play seamlessly in standard HTML5 <video src>
    without requiring client-side MPEG-DASH MSE or MediaSource decoder capabilities.
    """
    ffmpeg_headers = f"User-Agent: {client.user_agent}\r\n"
    if ".mpd" in url.lower() or "dash" in url.lower():
        ffmpeg_headers += f"Referer: {STREAM_REFERER}\r\n"
    if cookie:
        ffmpeg_headers += f"Cookie: {cookie}\r\n"

    cmd = [
        "ffmpeg", "-y",
        "-headers", ffmpeg_headers,
        "-i", url,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
        "-f", "mp4",
        "pipe:1"
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        async def video_stream():
            try:
                while True:
                    chunk = await proc.stdout.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
            finally:
                if proc.returncode is None:
                    try:
                        proc.kill()
                    except Exception:
                        pass

        return StreamingResponse(
            video_stream(),
            media_type="video/mp4",
            headers={
                "Content-Type": "video/mp4",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        logger.error(f"stream_mp4 error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------------- DASH Segment Proxy -----------------

@app.get("/api/dash/segment/{token}/{filename}")
async def dash_segment_proxy(
    request: Request,
    token: str,
    filename: str
):
    """
    Proxies relative DASH segments (.m4s, init, chunks) with proper upstream headers and cookies.
    """
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        base_dir, cookie = decoded.split("::", 1) if "::" in decoded else (decoded, "")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid DASH segment token")

    target_url = f"{base_dir}{filename}"
    req_headers = {
        "User-Agent": client.user_agent,
        "Accept": "*/*",
        "Referer": STREAM_REFERER
    }
    if cookie:
        req_headers["Cookie"] = cookie

    range_header = request.headers.get("range")
    if range_header:
        req_headers["Range"] = range_header

    try:
        h_client = get_http_client()
        upstream_req = h_client.build_request("GET", target_url, headers=req_headers)
        upstream_resp = await h_client.send(upstream_req, stream=True)

        resp_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": upstream_resp.headers.get("content-type", "video/iso.segment"),
            "Access-Control-Allow-Origin": "*",
        }
        if "content-range" in upstream_resp.headers:
            resp_headers["Content-Range"] = upstream_resp.headers["content-range"]
        if "content-length" in upstream_resp.headers:
            resp_headers["Content-Length"] = upstream_resp.headers["content-length"]

        status_code = upstream_resp.status_code
        if range_header and status_code == 200:
            status_code = 206

        async def seg_gen():
            try:
                async for chunk in upstream_resp.aiter_bytes(chunk_size=64 * 1024):
                    yield chunk
            finally:
                await upstream_resp.aclose()

        return StreamingResponse(
            seg_gen(),
            status_code=status_code,
            headers=resp_headers,
            media_type=resp_headers["Content-Type"]
        )
    except Exception as e:
        logger.error(f"DASH segment proxy error for {target_url}: {e}")
        return JSONResponse(status_code=502, content={"error": str(e)})

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
    Automatically rewrites DASH MPD manifests with <BaseURL> pointing to /api/dash/segment/.
    """
    h_client = get_http_client()

    # Forward Range header from browser
    req_headers = {
        "User-Agent": client.user_agent,
        "Accept": "*/*",
    }
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

        # Special handling for DASH MPD manifests: Rewrite <BaseURL> to proxy segments
        if ".mpd" in url.lower() or "xml" in upstream_resp.headers.get("content-type", "").lower():
            body_bytes = await upstream_resp.aread()
            body_text = body_bytes.decode("utf-8", errors="ignore")

            base_dir = url.rsplit("/", 1)[0] + "/"
            token_payload = f"{base_dir}::{cookie or ''}"
            token = base64.urlsafe_b64encode(token_payload.encode()).decode()

            proxy_segment_base = f"/api/dash/segment/{token}/"
            if "<BaseURL>" not in body_text and "<MPD" in body_text:
                body_text = re.sub(r"(<MPD[^>]*>)", r"\1\n\t<BaseURL>" + proxy_segment_base + "</BaseURL>", body_text, count=1)

            return Response(
                content=body_text,
                status_code=200,
                media_type="application/dash+xml",
                headers={
                    "Content-Type": "application/dash+xml",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )

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
