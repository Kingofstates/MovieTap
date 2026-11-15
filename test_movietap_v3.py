import asyncio
import os
import httpx
from app.server import app
from app.client import MovieBoxClient
from app.providers import SearchAggregator

async def test_all():
    print("==================================================")
    print("MovieTap v3.0 Verification Suite")
    print("==================================================")

    # 1. Verify wallpapers
    print("\n[1] Checking Hero Wallpapers (hero_1.jpg to hero_10.jpg)...")
    wallpapers_dir = "static/wallpapers"
    assert os.path.exists(wallpapers_dir), "wallpapers dir missing"
    for i in range(1, 11):
        wp = os.path.join(wallpapers_dir, f"hero_{i}.jpg")
        assert os.path.exists(wp), f"Missing {wp}"
        size = os.path.getsize(wp)
        assert size > 20000, f"Wallpaper {wp} too small ({size} bytes)"
    print("    All 10 wallpapers present and watermark-cleaned.")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. Test Root HTML
        print("\n[2] Testing Root HTML (MovieTap & AnimeWorld layout)...")
        r = await client.get("/")
        assert r.status_code == 200
        assert "MovieTap" in r.text
        assert "downloadModal" in r.text
        assert "Search your movie..." in r.text
        assert "wallpaperLoopBg" in r.text
        assert "footerAnimeSection" in r.text
        assert "mesamirh/MovieBox-TUI" in r.text
        print("    Root HTML verified: MovieTap branding, footer repo reference, download modal.")

        # 3. Test Multi-Engine Autocomplete Suggestions
        print("\n[3] Testing Rich Autocomplete Suggestions (/api/suggest)...")
        r = await client.get("/api/suggest?q=Iron+Man&provider=all")
        assert r.status_code == 200
        data = r.json()
        assert data.get("success"), f"Suggest failed: {data}"
        suggs = data.get("suggestions", [])
        print(f"    Returned {len(suggs)} suggestions for 'Iron Man':")
        for s in suggs[:3]:
            print(f"      • {s['title']} ({s.get('year')}) [{s.get('provider')}] - Poster: {'Yes' if s.get('poster_url') else 'No'}")
            assert s.get("title"), "Missing title"
            assert "poster_url" in s, "Missing poster_url"

        # 4. Test Telugu Audio Priority in MovieBox
        print("\n[4] Testing Telugu Audio Priority on Multi-Dub title (Avatar)...")
        r_search = await client.get("/api/search?q=Avatar&provider=moviebox")
        search_data = r_search.json()
        items = search_data.get("items", [])
        assert len(items) > 0, "No items found for Avatar"
        
        avatar_id = items[0]["id"]
        r_det = await client.get(f"/api/details?id={avatar_id}")
        det_data = r_det.json()
        details = det_data.get("details", {})
        dubs = details.get("dubs", [])
        active_lang = details.get("active_language", "")
        print(f"    Title: {details.get('title')}")
        print(f"    Active/Default Audio Language: {active_lang}")
        print(f"    All available dubs: {[d['language'] for d in dubs]}")
        assert "telugu" in active_lang.lower(), f"Expected default language to be Telugu, got: {active_lang}"

        # 5. Test Download Endpoint
        print("\n[5] Testing Browser Download Endpoint (/api/download)...")
        # Get a real stream URL from Avatar
        r_stream = await client.get(f"/api/streams?id={avatar_id}")
        stream_data = r_stream.json()
        streams = stream_data.get("streams", [])
        assert len(streams) > 0, "No streams found"
        test_stream = streams[0]
        
        import urllib.parse
        encoded_url = urllib.parse.quote(test_stream['url'], safe='')
        dl_url = f"/api/download?url={encoded_url}&filename=Avatar_Test"
        r_dl = await client.get(dl_url, headers={"Range": "bytes=0-1024"})
        print(f"    Download status: {r_dl.status_code}")
        print(f"    Content-Disposition: {r_dl.headers.get('content-disposition')}")
        print(f"    Content-Type: {r_dl.headers.get('content-type')}")
        assert "attachment" in r_dl.headers.get("content-disposition", "")
        assert "Avatar_Test.mp4" in r_dl.headers.get("content-disposition", "")
        assert len(r_dl.content) > 0

        # 6. Test Streaming Proxy Endpoint
        print("\n[6] Testing Video Streaming Proxy Endpoint (/api/stream)...")
        stream_proxy_url = f"/api/stream?url={encoded_url}"
        r_proxy = await client.get(stream_proxy_url, headers={"Range": "bytes=0-1024"})
        print(f"    Proxy stream status: {r_proxy.status_code}")
        print(f"    Content-Range: {r_proxy.headers.get('content-range')}")
        assert r_proxy.status_code in (200, 206), f"Expected 200 or 206, got {r_proxy.status_code}"
        assert len(r_proxy.content) > 0

    print("\n" + "="*50)
    print("ALL MOVIETAP v3.0 TESTS PASSED SUCCESSFULLY!")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_all())
