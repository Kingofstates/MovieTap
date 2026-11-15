"""
MovieBox API Client - Python Implementation
Reverse engineered from MovieBox-TUI (https://github.com/mesamirh/MovieBox-TUI)
Provides HMAC-MD5 signed requests, session token management, host rotation,
catalog search, metadata retrieval, stream extraction, and subtitle fetching.
"""

import urllib.parse
import hashlib
import hmac
import base64
import random
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("moviebox.client")

# MovieBox API Constants
DEFAULT_SECRET_BYTES = bytes([
    0xef, 0xa8, 0x91, 0x97, 0x4e, 0xec, 0xd3, 0x14,
    0x8d, 0xf6, 0x3a, 0xa6, 0x11, 0x60, 0x2d, 0xef,
    0xd1, 0x01, 0x25, 0x9b, 0xa5, 0x21, 0x02, 0x2c,
    0x57, 0xae, 0x05, 0x66, 0xbd, 0x8e
])
STOCK_CERT_SHA256 = "03d4b741632d136bc23e2de4c6adcdb7712f1980b619c183221801730bbd0410"
BUILD_TAG_SALT = "oneroom"
STREAM_REFERER = "https://sportslive.wine"

HOST_POOL = [
    "https://api6.aoneroom.com",
    "https://api5.aoneroom.com",
    "https://api4.aoneroom.com",
    "https://api4sg.aoneroom.com",
    "https://api3.aoneroom.com",
    "https://api6sg.aoneroom.com",
    "https://api.inmoviebox.com",
]

def build_tag_stamp(ts_ms: int, rand_part: int) -> str:
    return f"{ts_ms // 1000}{ts_ms % 1000:03d}000{rand_part}"

def build_tag_for_cert(ts_ms: int, rand_part: int, cert_sha256_hex: str) -> str:
    stamp = build_tag_stamp(ts_ms, rand_part)
    h = hashlib.md5(f"{cert_sha256_hex}{BUILD_TAG_SALT}{stamp}".encode('utf-8')).hexdigest()
    return f"{stamp}.{h}"

def generate_x_client_build(ts_ms: int) -> str:
    return build_tag_for_cert(ts_ms, random.randint(0, 999), STOCK_CERT_SHA256)

def generate_x_client_token(ts: int) -> str:
    ts_str = str(ts)
    reversed_ts = ts_str[::-1]
    h = hashlib.md5(reversed_ts.encode('utf-8')).hexdigest()
    return f"{ts_str},{h}"

def sorted_query_string(url_str: str) -> str:
    parsed = urllib.parse.urlparse(url_str)
    if not parsed.query:
        return ""
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    params_dict = {}
    for k, v in pairs:
        params_dict.setdefault(k, []).append(v)
    parts = []
    for k in sorted(params_dict.keys()):
        for v in params_dict[k]:
            parts.append(f"{k}={v}")
    return "&".join(parts)

def build_canonical_string(method: str, accept: str, content_type: str, url: str, body: Optional[str], ts: int) -> str:
    parsed = urllib.parse.urlparse(url)
    q = sorted_query_string(url)
    canonical_url = f"{parsed.path}?{q}" if q else parsed.path
    
    if body is not None:
        b_bytes = body.encode('utf-8') if isinstance(body, str) else body
        b_len = len(b_bytes)
        trunc = b_bytes[:102400]
        body_hash = hashlib.md5(trunc).hexdigest()
        body_len_str = str(b_len)
    else:
        body_hash = ""
        body_len_str = ""
        
    return f"{method.upper()}\n{accept or ''}\n{content_type or ''}\n{body_len_str}\n{ts}\n{body_hash}\n{canonical_url}"

def generate_x_tr_signature(method: str, accept: str, content_type: str, url: str, body: Optional[str], ts: int) -> str:
    canonical = build_canonical_string(method, accept, content_type, url, body, ts)
    mac = hmac.new(DEFAULT_SECRET_BYTES, canonical.encode('utf-8'), hashlib.md5)
    sig_b64 = base64.b64encode(mac.digest()).decode('ascii')
    return f"{ts}|2|{sig_b64}"

def random_hex(length: int) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))

def random_uuid() -> str:
    return f"{random_hex(8)}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{random_hex(12)}"

def random_spoofed_ip() -> str:
    prefixes = [
        "103.241", "49.36", "117.195", "106.198", "122.162", "157.32", "182.70", "103.58", "27.60", "59.90"
    ]
    return f"{random.choice(prefixes)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

def generate_client_info_and_ua() -> Tuple[str, dict]:
    android_versions = [
        ("9", "PQ3A.190605.03081104"),
        ("10", "QP1A.191005.007.A3"),
        ("11", "RP1A.200720.011"),
        ("12", "S1B.220414.015"),
        ("13", "TQ2A.230405.003"),
    ]
    redmi_devices = [
        ("23078RKD5C", "Redmi"),
        ("2201117TY", "Redmi"),
        ("2201117TG", "Redmi"),
        ("22101316G", "Redmi"),
        ("21121210G", "Redmi"),
        ("M2012K11AG", "Redmi"),
        ("M2007J20CG", "Redmi"),
    ]
    version_codes = [50020117, 50020118, 50020119, 50020120, 50020121]
    network_types = ["NETWORK_WIFI", "NETWORK_MOBILE"]
    timezones = ["Asia/Kolkata", "Asia/Shanghai", "Asia/Tokyo", "America/New_York", "Europe/London"]

    android = random.choice(android_versions)
    device = random.choice(redmi_devices)
    version_code = random.choice(version_codes)
    network = random.choice(network_types)
    tz = random.choice(timezones)
    gaid = random_uuid()
    device_id = random_hex(32)

    user_agent = f"com.community.oneroom/{version_code} (Linux; U; Android {android[0]}; en_US; {device[0]}; Build/{android[1]}; Cronet/135.0.7012.3)"
    client_info_obj = {
        "package_name": "com.community.oneroom",
        "version_name": "4.0.01.0813.03",
        "version_code": version_code,
        "os": "android",
        "os_version": android[0],
        "install_ch": "ps",
        "device_id": device_id,
        "install_store": "ps",
        "gaid": gaid,
        "brand": device[1],
        "model": device[0],
        "system_language": "en",
        "net": network,
        "region": "US",
        "timezone": tz,
        "sp_code": "40401",
        "X-Play-Mode": "2"
    }
    return user_agent, client_info_obj

def clean_title(raw_title: str) -> str:
    """Strip language and format tags like [Hindi], [CAM], [1080P] from title"""
    if not raw_title:
        return ""
    t = raw_title.strip()
    while t.startswith("["):
        idx = t.find("]")
        if idx != -1:
            t = t[idx + 1:].strip()
        else:
            break
    idx = t.find("[")
    if idx != -1:
        t = t[:idx].strip()
    if " - " in t:
        parts = t.rsplit(" - ", 1)
        suffix = parts[1].lower()
        if any(lang in suffix for lang in ["hindi", "tamil", "telugu", "kannada", "malayalam", "dub"]):
            t = parts[0].strip()
    return t

def clean_language_name(value: str) -> str:
    val = value.strip()
    low = val.lower()
    if low.startswith("original") or low == "orig":
        return "Original Audio"
    if low.endswith("dub"):
        val = val[:-3].strip()
    
    mapping = {
        "ptbr": "Portuguese (Brazil)",
        "esla": "Spanish (Latin America)",
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "ml": "Malayalam",
        "kn": "Kannada",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ru": "Russian",
        "ar": "Arabic",
        "bn": "Bengali",
        "id": "Indonesian"
    }
    return mapping.get(val.lower(), val.title())

def is_deprecation_notice_url(url: str) -> bool:
    lower = url.lower()
    return (
        "1c7de0bd3393702d9191801f15f88f8d" in lower
        or "9a0461bc39da389663bf3dbb17091d3f" in lower
        or "b164fbfb4347792950bdfbfb563d39d9" in lower
        or "/notice.mp4" in lower
        or ("macdn.aoneroom.com" in lower and "/other/" in lower)
    )

class MovieBoxClient:
    """
    Asynchronous and synchronous capable client for the MovieBox / OneRoom backend.
    """
    def __init__(self):
        import requests
        self.session = requests.Session()
        self.user_agent, self.client_info = generate_client_info_and_ua()
        self.spoofed_ip = random_spoofed_ip()
        self.token: Optional[str] = None
        self.active_host_idx = 0

    def build_headers(self, method: str, url: str, body_str: Optional[str] = None) -> dict:
        ts = int(time.time() * 1000)
        accept = "application/json"
        content_type = "application/json"
        client_token = generate_x_client_token(ts)
        sig = generate_x_tr_signature(method, accept, content_type, url, body_str, ts)
        build_tag = generate_x_client_build(ts)
        
        info = dict(self.client_info)
        info["X-Client-Build"] = build_tag
        info_str = json.dumps(info, separators=(',', ':'))

        headers = {
            "User-Agent": self.user_agent,
            "Accept": accept,
            "Content-Type": content_type,
            "Connection": "keep-alive",
            "x-client-token": client_token,
            "x-tr-signature": sig,
            "x-client-build": build_tag,
            "x-client-info": info_str,
            "x-client-status": "0",
            "x-forwarded-for": self.spoofed_ip
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def ensure_session(self) -> str:
        if self.token:
            return self.token
        return self.login()

    def login(self) -> str:
        path = "/wefeed-mobile-bff/user-api/visitor-login"
        data = self._request("POST", path, {})
        self.token = data.get("token")
        if not self.token:
            raise RuntimeError("Failed to obtain visitor token from MovieBox")
        logger.info(f"Obtained MovieBox visitor token: {self.token[:12]}...")
        return self.token

    def _request(self, method: str, path: str, body_obj: Optional[dict] = None) -> Any:
        body_str = json.dumps(body_obj, separators=(',', ':')) if body_obj is not None else None
        
        last_error = None
        for i in range(len(HOST_POOL)):
            idx = (self.active_host_idx + i) % len(HOST_POOL)
            host = HOST_POOL[idx]
            url = f"{host}{path}"
            headers = self.build_headers(method, url, body_str)
            try:
                resp = self.session.request(
                    method,
                    url,
                    data=body_str,
                    headers=headers,
                    timeout=12
                )
                if 'x-user' in resp.headers:
                    try:
                        u_data = json.loads(resp.headers['x-user'])
                        if 'token' in u_data and u_data['token']:
                            self.token = u_data['token']
                    except Exception:
                        pass
                
                if resp.status_code == 200:
                    self.active_host_idx = idx
                    data = resp.json()
                    return data.get("data", data)
                elif resp.status_code in (401, 403):
                    self.token = None
                    last_error = f"Auth error HTTP {resp.status_code}"
                else:
                    last_error = f"Host {host} status {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
                
        raise RuntimeError(f"MovieBox API request failed on all hosts: {last_error}")

    def get(self, path: str) -> Any:
        self.ensure_session()
        try:
            return self._request("GET", path)
        except RuntimeError:
            # Retry once after refreshing session
            self.login()
            return self._request("GET", path)

    def post(self, path: str, body: dict) -> Any:
        self.ensure_session()
        try:
            return self._request("POST", path, body)
        except RuntimeError:
            self.login()
            return self._request("POST", path, body)

    def search(self, query: str, page: int = 1) -> List[dict]:
        """Search MovieBox for titles matching keyword with multi-page depth"""
        items = []
        seen = set()
        pages_to_fetch = [page, page + 1, page + 2] if page == 1 else [page]
        for p in pages_to_fetch:
            payload = {
                "keyword": query,
                "page": p,
                "perPage": 15,
                "subjectType": 0
            }
            try:
                res = self.post("/wefeed-mobile-bff/subject-api/search/v2", payload)
                for group in res.get("results", []):
                    for s in group.get("subjects", []):
                        sid = str(s.get("subjectId") or s.get("id") or "")
                        if sid and sid not in seen:
                            seen.add(sid)
                            items.append(self._format_catalog_item(s))
            except Exception as e:
                logger.warning(f"MovieBox search page {p} error: {e}")
        return items

    def suggest(self, query: str) -> List[str]:
        """Return auto-complete suggestions"""
        items = self.search(query, page=1)
        return [item["title"] for item in items[:8]]

    def get_homepage(self, tab_id: str = "all", page: int = 1) -> List[dict]:
        """Fetch rich catalog combining Discover (Tab 1), TV Series (Tab 5), and Movies (Tab 2)"""
        items = []
        seen = set()
        tab_str = str(tab_id or "all").lower().strip()
        tab_map = {
            "all": ["1", "6", "2", "5"],
            "home": ["1", "6", "2", "5"],
            "movies": ["2"],
            "movie": ["2"],
            "series": ["5"],
            "tv": ["5"],
            "shows": ["5"],
            "trending": ["6", "1"],
            "popular": ["7"]
        }
        tabs_to_fetch = tab_map.get(tab_str, [tab_str] if tab_str.isdigit() else ["1", "2", "5"])
        
        for tid in tabs_to_fetch:
            try:
                path = f"/wefeed-mobile-bff/tab-operating?page={page}&tabId={tid}&version="
                res = self.get(path)
                groups = res.get("items", []) or []
                for g in groups:
                    banner = g.get("banner") or {}
                    for b in banner.get("banners") or []:
                        s = b.get("subject")
                        if s:
                            sid = str(s.get("subjectId") or s.get("id") or "")
                            if sid and sid not in seen:
                                seen.add(sid)
                                items.append(self._format_catalog_item(s))
                    custom = g.get("customData") or {}
                    for c in custom.get("items") or []:
                        s = c.get("subject")
                        if s:
                            sid = str(s.get("subjectId") or s.get("id") or "")
                            if sid and sid not in seen:
                                seen.add(sid)
                                items.append(self._format_catalog_item(s))
                    for s in g.get("subjects") or []:
                        if s:
                            sid = str(s.get("subjectId") or s.get("id") or "")
                            if sid and sid not in seen:
                                seen.add(sid)
                                items.append(self._format_catalog_item(s))
            except Exception as e:
                logger.warning(f"Error fetching tab {tid}: {e}")
                        
        return items

    def get_details(self, subject_id: str) -> dict:
        """Fetch complete metadata for movie or series"""
        path = f"/wefeed-mobile-bff/subject-api/get?subjectId={subject_id}"
        res = self.get(path)
        subject = res.get("subject", res)
        stype = int(subject.get("subjectType", 1))
        
        # Build seasons / episode list if TV series
        seasons = []
        seasons_data = subject.get("seasons", {})
        seasons_arr = []
        if isinstance(seasons_data, dict):
            seasons_arr = seasons_data.get("seasons", [])
        elif isinstance(seasons_data, list):
            seasons_arr = seasons_data
            
        for s in seasons_arr:
            se_num = int(s.get("se", 1))
            episodes = []
            ep_nums = s.get("episodeNumbers", [])
            if ep_nums:
                for ep in ep_nums:
                    episodes.append({
                        "season": se_num,
                        "episode": int(ep),
                        "title": f"Episode {ep}"
                    })
            else:
                max_ep = int(s.get("maxEp", 1))
                for ep_num in range(1, max_ep + 1):
                    episodes.append({
                        "season": se_num,
                        "episode": ep_num,
                        "title": f"Episode {ep_num}"
                    })
            seasons.append({
                "season": se_num,
                "episodes": episodes
            })

        # Fallback if TV series has seNum but empty seasons array
        if stype == 2 and not seasons:
            se_count = int(subject.get("seNum") or 1)
            for s_idx in range(1, se_count + 1):
                seasons.append({
                    "season": s_idx,
                    "episodes": [
                        {"season": s_idx, "episode": ep_idx, "title": f"Episode {ep_idx}"}
                        for ep_idx in range(1, 13)
                    ]
                })

        # Audio dubs / available languages
        current_sid = str(subject.get("subjectId") or subject.get("id") or subject_id)
        dubs = []
        dubs_arr = subject.get("dubs") or []
        for d in dubs_arr:
            sub_id = str(d.get("subjectId") or d.get("id") or "")
            if not sub_id:
                continue
            raw_lang = d.get("lanName") or d.get("language") or d.get("lang") or "Unknown"
            clean_lang = clean_language_name(raw_lang)
            dubs.append({
                "id": sub_id,
                "subject_id": sub_id,
                "language": clean_lang,
                "raw_language": raw_lang,
                "title": d.get("title") or d.get("name") or clean_lang,
                "is_current": (sub_id == current_sid)
            })

        # Ensure current subject has an entry if dubs is empty or doesn't include current_sid
        if not dubs:
            subj_lang = clean_language_name(subject.get("language") or "Original Audio")
            dubs.append({
                "id": current_sid,
                "subject_id": current_sid,
                "language": subj_lang,
                "raw_language": subject.get("language") or "Original",
                "title": subj_lang,
                "is_current": True
            })
        elif not any(d["id"] == current_sid for d in dubs):
            subj_lang = clean_language_name(subject.get("language") or "Original Audio")
            dubs.insert(0, {
                "id": current_sid,
                "subject_id": current_sid,
                "language": subj_lang,
                "raw_language": subject.get("language") or "Original",
                "title": subj_lang,
                "is_current": True
            })

        # Determine active dub index - Prioritize Telugu as requested by user
        active_dub_idx = 0
        telugu_idx = next((i for i, d in enumerate(dubs) if "telugu" in d["language"].lower()), None)
        hindi_idx = next((i for i, d in enumerate(dubs) if "hindi" in d["language"].lower()), None)
        current_match_idx = next((i for i, d in enumerate(dubs) if d.get("is_current") or d["id"] == current_sid), 0)

        if telugu_idx is not None:
            active_dub_idx = telugu_idx
        elif hindi_idx is not None and not dubs[current_match_idx]["language"].lower().startswith("telugu"):
            active_dub_idx = hindi_idx
        else:
            active_dub_idx = current_match_idx

        # Mark chosen dub as is_current
        for i, d in enumerate(dubs):
            d["is_current"] = (i == active_dub_idx)

        sibling_ids = [d["id"] for d in dubs if d["id"] != current_sid]

        raw_title = subject.get("title", "Unknown")
        display_title = clean_title(raw_title)

        cover_url = ""
        if isinstance(subject.get("cover"), dict):
            cover_url = subject["cover"].get("url", "")
        elif isinstance(subject.get("cover"), str):
            cover_url = subject.get("cover")

        rating = subject.get("imdbRatingValue") or subject.get("rating")
        rating_str = f"{float(rating):.1f}" if rating else "N/A"

        return {
            "id": current_sid,
            "title": display_title,
            "raw_title": raw_title,
            "is_series": stype == 2,
            "subject_type": stype,
            "year": (subject.get("releaseDate") or subject.get("year") or "")[:4],
            "release_date": subject.get("releaseDate") or "",
            "duration": subject.get("duration") or "",
            "genres": [g.strip() for g in (subject.get("genre") or "").split(",") if g.strip()] if isinstance(subject.get("genre"), str) else (subject.get("genres") or []),
            "description": subject.get("description") or subject.get("intro") or "",
            "tagline": subject.get("tagline") or "",
            "rating": rating_str,
            "director": subject.get("director") or "",
            "stars": subject.get("stars") or "",
            "poster_url": cover_url,
            "seasons": seasons,
            "dubs": dubs,
            "active_dub_index": active_dub_idx,
            "active_language": dubs[active_dub_idx]["language"] if dubs else "Original Audio",
            "sibling_ids": sibling_ids,
            "raw_subject": subject
        }

    def get_resource_position(self, subject_id: str, resource_id: str, failed_url: str) -> dict:
        """Recover direct streaming file when resourceLink points to notice/placeholder"""
        params = urllib.parse.urlencode({
            "subjectId": subject_id,
            "resourceId": resource_id,
            "failUrl": failed_url,
            "failCode": "404"
        })
        path = f"/wefeed-mobile-bff/subject-api/resource-position/v2?{params}"
        return self.get(path)

    def get_streams(self, subject_id: str, season: int = 0, episode: int = 0) -> List[dict]:
        """
        Aggregate all available stream links (1080p, 720p, 480p, 360p, DASH)
        with direct URLs and quality tags.
        """
        streams = []
        seen_urls = set()

        # Source 1: Check subject details resourceDetectors
        try:
            details_data = self.get(f"/wefeed-mobile-bff/subject-api/get?subjectId={subject_id}")
            subj = details_data.get("subject", details_data)
            detectors = subj.get("resourceDetectors") or []
            for det in detectors:
                res_list = det.get("resolutionList") or []
                if res_list:
                    for item in res_list:
                        url = item.get("resourceLink") or item.get("downloadUrl")
                        if url and not is_deprecation_notice_url(url) and url not in seen_urls:
                            seen_urls.add(url)
                            res = item.get("resolution") or 720
                            size_bytes = int(item.get("size") or 0)
                            streams.append({
                                "quality": f"{res}p" if not str(res).endswith("p") else str(res),
                                "resolution": int(str(res).rstrip("p") or 0),
                                "url": url,
                                "format": "MP4",
                                "size_bytes": size_bytes,
                                "size_formatted": self._format_size(size_bytes),
                                "codec": item.get("codecName") or "h264",
                                "source": item.get("uploadBy") or "MovieBox Direct",
                                "resource_id": str(item.get("resourceId") or "")
                            })
                else:
                    dl_url = det.get("downloadUrl")
                    if dl_url and not is_deprecation_notice_url(dl_url) and dl_url not in seen_urls:
                        seen_urls.add(dl_url)
                        size_bytes = int(det.get("firstSize") or det.get("size") or 0)
                        streams.append({
                            "quality": "Direct HD",
                            "resolution": 1080,
                            "url": dl_url,
                            "format": "MP4",
                            "size_bytes": size_bytes,
                            "size_formatted": self._format_size(size_bytes),
                            "codec": det.get("codecName") or "h264",
                            "source": det.get("uploadBy") or "MovieBox Direct",
                            "resource_id": str(det.get("resourceId") or "")
                        })
        except Exception as e:
            logger.warning(f"Error fetching resourceDetectors: {e}")

        # Source 2: Query resource/v2 for targeted episode / movie
        try:
            res_path = (
                f"/wefeed-mobile-bff/subject-api/resource/v2?subjectId={subject_id}"
                f"&page=1&perPage=20&all=0&startPosition=1&endPosition=1&pagerMode=2&resolution=0"
                f"&se={season}&epFrom={episode}&epTo={episode}&isVip=true"
            )
            res_data = self.get(res_path)
            items = res_data.get("list") or []
            for item in items:
                link = item.get("resourceLink") or item.get("url") or ""
                rid = str(item.get("resourceId") or item.get("id") or "")
                
                # Check if deprecation notice or placeholder, try recovery
                if link and is_deprecation_notice_url(link) and rid:
                    try:
                        recovered = self.get_resource_position(subject_id, rid, link)
                        rec_items = (recovered.get("data") or recovered).get("list") or []
                        for rec in rec_items:
                            rec_url = rec.get("resourceLink") or rec.get("url")
                            if rec_url and not is_deprecation_notice_url(rec_url):
                                link = rec_url
                                item["size"] = rec.get("size") or item.get("size")
                                break
                    except Exception as ex:
                        logger.warning(f"Recovery failed for {rid}: {ex}")

                if link and not is_deprecation_notice_url(link) and link not in seen_urls:
                    seen_urls.add(link)
                    res = item.get("resolution") or 720
                    size_bytes = int(item.get("size") or 0)
                    streams.append({
                        "quality": f"{res}p" if not str(res).endswith("p") else str(res),
                        "resolution": int(str(res).rstrip("p") or 0),
                        "url": link,
                        "format": "MP4",
                        "size_bytes": size_bytes,
                        "size_formatted": self._format_size(size_bytes),
                        "codec": item.get("codecName") or "h264",
                        "source": item.get("uploadBy") or "MovieBox Direct",
                        "resource_id": rid
                    })
        except Exception as e:
            logger.warning(f"Error querying resource v2: {e}")

        # Source 3: Query play-info/v2 for DASH / MP4 streams
        try:
            if season == 0 and episode == 0:
                p_path = f"/wefeed-mobile-bff/subject-api/play-info/v2?subjectId={subject_id}"
            else:
                p_path = f"/wefeed-mobile-bff/subject-api/play-info/v2?subjectId={subject_id}&se={season}&ep={episode}"
            pinfo = self.get(p_path)
            p_streams = pinfo.get("streams") or []
            for s in p_streams:
                url = s.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    resolutions = s.get("resolutions") or "720"
                    res_val = int(resolutions.split(",")[0].rstrip("p")) if resolutions else 720
                    size_bytes = int(s.get("size") or 0)
                    streams.append({
                        "quality": f"{res_val}p",
                        "resolution": res_val,
                        "url": url,
                        "format": s.get("format", "MP4"),
                        "size_bytes": size_bytes,
                        "size_formatted": self._format_size(size_bytes),
                        "codec": s.get("codecName") or "h264",
                        "source": "MovieBox Stream",
                        "sign_cookie": s.get("signCookie"),
                        "resource_id": str(s.get("id") or "")
                    })
        except Exception as e:
            logger.warning(f"Error querying play info: {e}")

        # Prioritize MP4 over DASH for native browser HTML5 playback
        # and sort by resolution descending (1080p -> 720p -> 480p -> 360p)
        streams.sort(key=lambda s: (s["format"] == "MP4", s["resolution"]), reverse=True)
        
        # Deduplicate streams with same resolution and format, keeping highest size
        unique_streams = []
        seen_qualities = set()
        for s in streams:
            key = (s["resolution"], s["format"])
            if key not in seen_qualities:
                seen_qualities.add(key)
                unique_streams.append(s)

        return unique_streams

    def get_captions(self, subject_id: str, resource_id: str = "") -> List[dict]:
        """Fetch subtitles/captions for a given subject & resource"""
        if not resource_id:
            try:
                streams = self.get_streams(subject_id)
                for s in streams:
                    if s.get("resource_id"):
                        resource_id = s["resource_id"]
                        break
            except Exception:
                pass
        if not resource_id:
            return []
        path = f"/wefeed-mobile-bff/subject-api/get-ext-captions?subjectId={subject_id}&resourceId={resource_id}"
        try:
            res = self.get(path)
            captions = res.get("extCaptions") or res.get("list") or []
            results = []
            seen_langs = set()
            for cap in captions:
                url = cap.get("url")
                if not url or "aa348f2541d13ffe" in url:
                    continue
                lang = cap.get("lanName") or cap.get("lan") or "Unknown"
                if lang in seen_langs:
                    continue
                seen_langs.add(lang)
                results.append({
                    "id": str(cap.get("id") or ""),
                    "language": lang,
                    "code": cap.get("lan", "en"),
                    "url": url,
                    "size": int(cap.get("size") or 0)
                })
            # Prioritize English at the top
            results.sort(key=lambda c: (c["language"].lower() != "english", c["language"]))
            return results
        except Exception as e:
            logger.warning(f"Error fetching captions: {e}")
            return []

    def _format_catalog_item(self, s: dict) -> dict:
        sid = str(s.get("subjectId") or s.get("id") or "")
        stype = int(s.get("subjectType") or s.get("stype") or 1)
        cover_url = ""
        if isinstance(s.get("cover"), dict):
            cover_url = s["cover"].get("url", "")
        elif isinstance(s.get("cover"), str):
            cover_url = s.get("cover")

        rating = s.get("imdbRatingValue") or s.get("rating")
        rating_str = f"{float(rating):.1f}" if rating else ""

        raw_title = s.get("title", "Unknown")
        display_title = clean_title(raw_title)

        lang_tag = ""
        if "[" in raw_title and "]" in raw_title:
            try:
                candidate = raw_title.split("[", 1)[1].split("]", 1)[0].strip()
                if candidate.lower() in ("hindi", "tamil", "telugu", "english", "spanish", "korean", "japanese", "malayalam", "kannada"):
                    lang_tag = candidate.title()
            except Exception:
                pass

        return {
            "id": sid,
            "title": display_title,
            "raw_title": raw_title,
            "language_tag": lang_tag,
            "is_series": stype == 2,
            "subject_type": stype,
            "year": (s.get("releaseDate") or s.get("year") or "")[:4],
            "duration": s.get("duration") or "",
            "genres": [g.strip() for g in (s.get("genre") or "").split(",") if g.strip()] if isinstance(s.get("genre"), str) else [],
            "rating": rating_str,
            "poster_url": cover_url
        }

    def _format_size(self, size_bytes: int) -> str:
        if not size_bytes:
            return ""
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024**3):.1f} GB"
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024**2):.1f} MB"
        return f"{size_bytes / 1024:.0f} KB"
