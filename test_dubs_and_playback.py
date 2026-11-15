import asyncio
import httpx
from app.client import MovieBoxClient

async def test_dubs_and_playback():
    client = MovieBoxClient()
    print("Testing MovieBox Client & Dubs...")
    
    # 1. Search for a popular title with multiple audio languages
    print("\n[1] Testing Search for 'Avatar' (known multi-language title)...")
    items = client.search("Avatar")
    print(f"    Found {len(items)} search items.")
    assert len(items) > 0, "No items found for Avatar"
    
    avatar_id = items[0]["id"]
    print(f"    Selected title: {items[0]['title']} (ID: {avatar_id})")
    
    # 2. Get Details & Dubs
    print("\n[2] Testing Subject Details & Audio Dubs...")
    details = client.get_details(avatar_id)
    title = details.get("title")
    dubs = details.get("dubs", [])
    print(f"    Title: {title}")
    print(f"    Available Dubs: {len(dubs)}")
    for i, d in enumerate(dubs):
        print(f"      - [{i+1}] {d['language']} (ID: {d['id']}, Title: {d['title']})")
    
    assert len(dubs) > 0, "Expected at least 1 audio track"
    
    # 3. Test Stream Retrieval for each dub
    print("\n[3] Testing Stream Quality Resolution for Audio Tracks...")
    for dub in dubs[:3]: # Test first 3 dubs
        streams = client.get_streams(dub["id"])
        print(f"    Dub: {dub['language']} -> {len(streams)} streams found.")
        for s in streams[:2]:
            print(f"        * Quality: {s['quality']}, Codec: {s['codec']}, Size: {s['size_formatted']}, RID: {s['resource_id']}")
            assert s["url"].startswith("http"), f"Invalid stream url: {s['url']}"
        
        # Test Captions for top stream
        if streams and streams[0].get("resource_id"):
            captions = client.get_captions(dub["id"], streams[0]["resource_id"])
            print(f"        Subtitles for {dub['language']}: {len(captions)} languages")
            for c in captions[:3]:
                print(f"           • {c['language']} (code: {c.get('code')})")
    
    # 4. Test TV Series (e.g. Loki or Wednesday)
    print("\n[4] Testing TV Series Seasons & Episodes (Loki)...")
    series_items = client.search("Loki")
    loki_item = next((it for it in series_items if it.get("is_series")), series_items[0] if series_items else None)
    if loki_item:
        print(f"    Series found: {loki_item['title']} (ID: {loki_item['id']})")
        series_details = client.get_details(loki_item["id"])
        seasons = series_details.get("seasons", [])
        print(f"    Seasons count: {len(seasons)}")
        if seasons:
            print(f"    Season 1 episodes: {len(seasons[0].get('episodes', []))}")
            s_streams = client.get_streams(loki_item["id"], season=1, episode=1)
            print(f"    Season 1 Episode 1 streams: {len(s_streams)}")
            if s_streams:
                print(f"        Top stream: {s_streams[0]['quality']} ({s_streams[0]['codec']})")

    # 5. Test Range Streaming Proxy on a direct MP4
    print("\n[5] Testing Range Proxy Request...")
    test_stream = streams[0] if streams else None
    if test_stream:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            stream_url = test_stream["url"]
            headers = {
                "User-Agent": client.user_agent,
                "Range": "bytes=0-1024"
            }
            res = await http_client.get(stream_url, headers=headers)
            print(f"    CDN Status: {res.status_code}")
            print(f"    Content-Range: {res.headers.get('content-range')}")
            print(f"    Content-Length: {res.headers.get('content-length')}")
            assert res.status_code in [200, 206], f"CDN returned status {res.status_code}"

    print("\n" + "="*50)
    print("ALL DUBS & PLAYBACK VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_dubs_and_playback())
