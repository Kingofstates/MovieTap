"""
Room 206 - Multi-Provider Aggregator
Integrates:
1. MovieBox (Primary high-speed HD/4K multi-dub engine with Telugu/Hindi/English)
2. Dramachi (Asian dramas, anime, and movies via nodeobjects API)
3. 4KHDHub (4K/UHD releases via 4khdhub.one)
4. AnimeWorld India (Anime in Hindi, Telugu, Tamil, and English via watchanimeworld.one)
5. HiAnime (International Anime sub/dub via hianime.biz.pl)
"""

import asyncio
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from app.client import MovieBoxClient, clean_title

logger = logging.getLogger("room206.providers")

# ----------------- Dramachi Provider -----------------
class DramachiProvider:
    BASE_URL = "https://api.nodeobjects.com/"
    IMAGE_CDN = "https://static.nodeobjects.com/thumbnail/"

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def search(self, query: str, page: int = 1) -> List[dict]:
        try:
            url = f"{self.BASE_URL}?interface=search&q={urllib.parse.quote(query)}&filter=all&page={page}"
            res = await self.http_client.get(url, timeout=7.0)
            if res.status_code != 200:
                return []
            data = res.json()
            raw_items = data.get("data") or []
            results = []
            for item in raw_items:
                thumb = item.get("thumb") or ""
                poster_url = f"{self.IMAGE_CDN}{thumb}" if thumb else ""
                is_series = (item.get("content") or "").lower() in ["series", "tv", "drama"]
                title_id = str(item.get("id") or "")
                raw_title = item.get("title") or item.get("common_title") or "Unknown"
                results.append({
                    "id": f"dramachi_{title_id}",
                    "title": clean_title(raw_title),
                    "raw_title": raw_title,
                    "poster_url": poster_url,
                    "is_series": is_series,
                    "year": str(item.get("year") or "")[:4],
                    "rating": "8.0",
                    "duration": "",
                    "genres": ["Drama", item.get("category") or "Cinema"],
                    "provider": "Dramachi"
                })
            return results
        except Exception as e:
            logger.warning(f"Dramachi search failed: {e}")
            return []

    async def get_details(self, title_id: str) -> Optional[dict]:
        try:
            clean_id = title_id.replace("dramachi_", "")
            url = f"{self.BASE_URL}?interface=title_v2&id={clean_id}"
            res = await self.http_client.get(url, timeout=7.0)
            if res.status_code != 200:
                return None
            data = res.json()
            albums = data.get("album") or []
            album = albums[0] if isinstance(albums, list) and albums else (albums if isinstance(albums, dict) else {})
            
            thumb = album.get("thumb") or ""
            poster_url = f"{self.IMAGE_CDN}{thumb}" if thumb else ""
            
            seasons_data = data.get("seasons") or {}
            dubs = []
            if isinstance(seasons_data, dict):
                for s_key, group in seasons_data.items():
                    for v in (group.get("versions") or []):
                        v_name = v.get("version_name") or "Original"
                        rip = v.get("rip") or s_key
                        dubs.append({
                            "id": f"dramachi_{clean_id}::{rip}",
                            "subject_id": f"dramachi_{clean_id}::{rip}",
                            "language": v_name,
                            "raw_language": v_name,
                            "title": v_name,
                            "is_current": len(dubs) == 0
                        })
            
            if not dubs:
                dubs.append({
                    "id": f"dramachi_{clean_id}",
                    "subject_id": f"dramachi_{clean_id}",
                    "language": "Original Audio",
                    "raw_language": "Original",
                    "title": "Original Audio",
                    "is_current": True
                })

            is_series = (album.get("content") or "").lower() in ["series", "tv", "drama"]
            seasons = []
            if is_series and isinstance(seasons_data, dict):
                s_idx = 1
                for s_key in sorted(seasons_data.keys()):
                    seasons.append({
                        "season": s_idx,
                        "episodes": [{"episode": ep, "title": f"Episode {ep}"} for ep in range(1, 13)]
                    })
                    s_idx += 1

            return {
                "id": f"dramachi_{clean_id}",
                "title": clean_title(album.get("title") or "Unknown"),
                "raw_title": album.get("title") or "Unknown",
                "is_series": is_series,
                "subject_type": 2 if is_series else 1,
                "year": str(album.get("year") or "")[:4],
                "duration": album.get("runtime") or "",
                "genres": [g.strip() for g in (album.get("genres") or "").split(",") if g.strip()],
                "description": album.get("storyline") or "",
                "director": album.get("director") or "",
                "stars": "",
                "rating": "8.2",
                "poster_url": poster_url,
                "seasons": seasons,
                "dubs": dubs,
                "active_dub_index": 0,
                "active_language": dubs[0]["language"],
                "provider": "Dramachi"
            }
        except Exception as e:
            logger.error(f"Dramachi get_details error: {e}")
            return None

    async def get_streams(self, target_id: str, season: int = 0, episode: int = 0) -> List[dict]:
        try:
            clean_id = target_id.replace("dramachi_", "")
            title_id, rip = clean_id.split("::") if "::" in clean_id else (clean_id, "hd Rip")
            
            ep_url = f"{self.BASE_URL}?interface=eplist&season={urllib.parse.quote(rip)}&id={title_id}"
            ep_res = await self.http_client.get(ep_url, timeout=7.0)
            if ep_res.status_code != 200:
                return []
            ep_data = ep_res.json()
            ep_list = ep_data.get("episode_list") or []
            if not ep_list:
                return []

            target_ep = ep_list[0]
            if episode > 1 and len(ep_list) >= episode:
                target_ep = ep_list[episode - 1]

            fid = target_ep.get("fid")
            disk = target_ep.get("disk") or "4"
            if not fid:
                return []

            file_url = f"{self.BASE_URL}?interface=getFile&fid={fid}&findex={disk}"
            file_res = await self.http_client.get(file_url, timeout=7.0)
            if file_res.status_code != 200:
                return []
            f_data = file_res.json()
            host = (f_data.get("hostInfo") or {}).get("host")
            file_info_list = f_data.get("fileInfo") or []
            if not host or not file_info_list:
                return []

            f_info = file_info_list[0]
            raw_stream_url = f_info.get("url", "").lstrip("/")
            full_stream_url = f"https://{host}/cdn/{raw_stream_url}"

            quality = target_ep.get("quality") or "1080p"
            return [{
                "quality": quality,
                "resolution": 1080 if "1080" in quality else (720 if "720" in quality else 540),
                "url": full_stream_url,
                "format": "MP4",
                "size_bytes": 0,
                "size_formatted": target_ep.get("size") or "HD",
                "codec": "h264",
                "source": "Dramachi CDN",
                "resource_id": str(fid)
            }]
        except Exception as e:
            logger.error(f"Dramachi get_streams error: {e}")
            return []


# ----------------- 4KHDHub Provider -----------------
class FourKHdHubProvider:
    BASE_URL = "https://4khdhub.one/"

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def search(self, query: str) -> List[dict]:
        try:
            url = f"{self.BASE_URL}?s={urllib.parse.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = await self.http_client.get(url, headers=headers, timeout=6.0)
            if res.status_code != 200:
                return []
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for article in soup.select("article"):
                a_tag = article.select_one("h2 a, h3 a, a")
                if not a_tag:
                    continue
                href = a_tag.get("href") or ""
                title = a_tag.get_text(strip=True)
                if not href or not title:
                    continue
                
                img_tag = article.select_one("img")
                poster = img_tag.get("src") or "" if img_tag else ""
                
                is_series = "season" in title.lower() or "s0" in title.lower() or "series" in title.lower()
                year = ""
                for word in title.split():
                    if word.isdigit() and 1900 <= int(word) <= 2030:
                        year = word
                        break
                
                results.append({
                    "id": f"4khd_{urllib.parse.quote(href, safe='')}",
                    "title": clean_title(title),
                    "raw_title": title,
                    "poster_url": poster,
                    "is_series": is_series,
                    "year": year,
                    "rating": "8.5",
                    "duration": "",
                    "genres": ["4K Ultra HD", "Cinema"],
                    "provider": "4KHDHub"
                })
            return results
        except Exception as e:
            logger.warning(f"4KHDHub search error: {e}")
            return []


# ----------------- AnimeWorld India Provider -----------------
class AnimeWorldProvider:
    """AnimeWorld India (watchanimeworld.one) - Best source for Hindi, Telugu, Tamil & English Anime"""
    BASE_URL = "https://watchanimeworld.one/"

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def search(self, query: str) -> List[dict]:
        try:
            url = f"{self.BASE_URL}?s={urllib.parse.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = await self.http_client.get(url, headers=headers, timeout=6.0)
            if res.status_code != 200:
                return []
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for article in soup.select("article, .post-item, .bsx, .animposx"):
                a_tag = article.select_one("a")
                if not a_tag:
                    continue
                href = a_tag.get("href") or ""
                title_elem = article.select_one(".tt, h2, h3, .title") or a_tag
                title = title_elem.get_text(strip=True) if title_elem else ""
                if not href or not title:
                    continue
                
                img_tag = article.select_one("img")
                poster = ""
                if img_tag:
                    poster = img_tag.get("data-src") or img_tag.get("src") or ""
                    if poster.startswith("//"):
                        poster = "https:" + poster

                is_series = "/series/" in href or "season" in title.lower() or "s0" in title.lower()
                year = ""
                for word in title.split():
                    if word.isdigit() and 1980 <= int(word) <= 2030:
                        year = word
                        break

                results.append({
                    "id": f"animeworld_{urllib.parse.quote(href, safe='')}",
                    "title": clean_title(title),
                    "raw_title": title,
                    "poster_url": poster,
                    "is_series": is_series,
                    "year": year or "2024",
                    "rating": "8.8",
                    "duration": "24m",
                    "genres": ["Anime", "Action", "Animation"],
                    "provider": "AnimeWorld"
                })
            return results
        except Exception as e:
            logger.warning(f"AnimeWorld search error: {e}")
            return []


# ----------------- HiAnime Provider -----------------
class HiAnimeProvider:
    """HiAnime (hianime.biz.pl) - Leading anime stream catalog"""
    BASE_URL = "https://hianime.biz.pl/"

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def search(self, query: str) -> List[dict]:
        try:
            url = f"{self.BASE_URL}search?keyword={urllib.parse.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = await self.http_client.get(url, headers=headers, timeout=6.0)
            if res.status_code != 200:
                return []
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for item in soup.select(".flw-item"):
                name_elem = item.select_one(".film-name a")
                if not name_elem:
                    continue
                title = name_elem.get_text(strip=True)
                href = name_elem.get("href") or ""
                poster_elem = item.select_one(".film-poster img")
                poster = ""
                if poster_elem:
                    poster = poster_elem.get("data-src") or poster_elem.get("src") or ""
                
                is_sub = bool(item.select_one(".tick-sub"))
                is_dub = bool(item.select_one(".tick-dub"))
                lang_tag = "Multi Dub" if is_sub and is_dub else ("Dubbed" if is_dub else "Subbed")

                results.append({
                    "id": f"hianime_{urllib.parse.quote(href, safe='')}",
                    "title": clean_title(title),
                    "raw_title": title,
                    "language_tag": lang_tag,
                    "poster_url": poster,
                    "is_series": True,
                    "year": "2024",
                    "rating": "8.9",
                    "duration": "24m",
                    "genres": ["Anime", "Animation", "Action"],
                    "provider": "HiAnime"
                })
            return results
        except Exception as e:
            logger.warning(f"HiAnime search error: {e}")
            return []


# ----------------- Animerulz Provider -----------------
class AnimerulzProvider:
    """Animerulz (animerulz.com.in) - Best source for Indian Anime sub/dub"""
    BASE_URL = "https://animerulz.com.in/"

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def search(self, query: str) -> List[dict]:
        try:
            url = f"{self.BASE_URL}?s={urllib.parse.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = await self.http_client.get(url, headers=headers, timeout=6.0)
            if res.status_code != 200:
                return []
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for item in soup.select("article, .post-item, .item, .featured, .entry"):
                a_tag = item.select_one("a")
                if not a_tag:
                    continue
                href = a_tag.get("href") or ""
                title_elem = item.select_one("h2, h3, .title, .entry-title") or a_tag
                title = title_elem.get_text(strip=True) if title_elem else ""
                if not href or not title:
                    continue
                
                img_tag = item.select_one("img")
                poster = ""
                if img_tag:
                    poster = img_tag.get("src") or img_tag.get("data-src") or ""
                
                results.append({
                    "id": f"animerulz_{urllib.parse.quote(href, safe='')}",
                    "title": clean_title(title),
                    "raw_title": title,
                    "poster_url": poster,
                    "is_series": True,
                    "year": "2024",
                    "rating": "8.7",
                    "duration": "24m",
                    "genres": ["Anime", "Animation"],
                    "provider": "Animerulz"
                })
            return results
        except Exception as e:
            logger.warning(f"Animerulz search error: {e}")
            return []


# ----------------- Aggregated Multi-Search Engine -----------------
class SearchAggregator:
    def __init__(self, moviebox_client: MovieBoxClient):
        self.moviebox = moviebox_client

    async def multi_search(self, http_client: httpx.AsyncClient, query: str, provider: str = "all") -> List[dict]:
        """
        Search across MovieBox, Dramachi, 4KHDHub, AnimeWorld, HiAnime, and Animerulz concurrently.
        """
        tasks = []
        dramachi = DramachiProvider(http_client)
        fourkhd = FourKHdHubProvider(http_client)
        animeworld = AnimeWorldProvider(http_client)
        hianime = HiAnimeProvider(http_client)
        animerulz = AnimerulzProvider(http_client)

        # 1. MovieBox search
        if provider in ["all", "moviebox"]:
            async def run_mb():
                loop = asyncio.get_event_loop()
                try:
                    items = await loop.run_in_executor(None, self.moviebox.search, query)
                    for it in items:
                        it["provider"] = "MovieBox"
                    return items
                except Exception as e:
                    logger.warning(f"MovieBox async search error: {e}")
                    return []
            tasks.append(run_mb())

        # 2. Dramachi search
        if provider in ["all", "dramachi"]:
            tasks.append(dramachi.search(query))

        # 3. 4KHDHub search
        if provider in ["all", "4khdhub"]:
            tasks.append(fourkhd.search(query))

        # 4. AnimeWorld search (Hindi/Telugu/English anime)
        if provider in ["all", "anime", "animeworld"]:
            tasks.append(animeworld.search(query))

        # 5. HiAnime search
        if provider in ["all", "anime", "hianime"]:
            tasks.append(hianime.search(query))

        # 6. Animerulz search
        if provider in ["all", "anime", "animerulz"]:
            tasks.append(animerulz.search(query))

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined = []
        seen_titles = set()
        for res in results_lists:
            if isinstance(res, list):
                for item in res:
                    # Filter out any TV series (Movies only)
                    if item.get("is_series"):
                        continue
                    key = (item.get("title", "").strip().lower(), item.get("year", ""))
                    if key not in seen_titles:
                        seen_titles.add(key)
                        combined.append(item)

        # Sort: MovieBox primary, then others
        combined.sort(key=lambda x: (0 if x.get("provider") == "MovieBox" else 1))
        return combined
