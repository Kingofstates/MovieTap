import sys
import os
import time
import requests
import subprocess

# Start server in background
proc = subprocess.Popen(
    [sys.executable, "run.py"],
    cwd=os.path.abspath(os.path.dirname(__file__)),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

time.sleep(3)

base_url = "http://127.0.0.1:8000"
passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"✅ {name}: PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ {name}: FAILED - {e}")
        failed += 1

try:
    def test_root():
        r = requests.get(base_url, timeout=5)
        assert r.status_code == 200, f"Status {r.status_code}"
        assert "<title>Movie" in r.text, "Index HTML missing title"
    test("Root Web Page", test_root)

    def test_homepage():
        r = requests.get(f"{base_url}/api/homepage", timeout=10)
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert data.get("success") is True, f"Success flag false: {data}"
        assert len(data.get("items", [])) > 0, "No homepage items"
        print(f"   (Homepage loaded {len(data['items'])} items)")
    test("Homepage API", test_homepage)

    search_item_id = None
    def test_search():
        global search_item_id
        r = requests.get(f"{base_url}/api/search?q=Avatar", timeout=10)
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert data.get("success") is True, "Search failed"
        items = data.get("items", [])
        assert len(items) > 0, "No search items"
        search_item_id = items[0]["id"]
        print(f"   (Search found {len(items)} items, top: {items[0]['title']} [ID: {search_item_id}])")
    test("Search API", test_search)

    def test_details():
        global search_item_id
        assert search_item_id, "No ID from search"
        r = requests.get(f"{base_url}/api/details?id={search_item_id}", timeout=10)
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert data.get("success") is True, "Details failed"
        d = data.get("details", {})
        assert d.get("title"), "No title in details"
        print(f"   (Details: {d['title']}, Year: {d.get('year')}, Rating: {d.get('rating')})")
    test("Details API", test_details)

    proxy_stream_url = None
    def test_streams():
        global search_item_id, proxy_stream_url
        assert search_item_id, "No ID from search"
        r = requests.get(f"{base_url}/api/streams?id={search_item_id}", timeout=10)
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert data.get("success") is True, "Streams failed"
        streams = data.get("streams", [])
        assert len(streams) > 0, "No streams returned"
        proxy_stream_url = streams[0]["proxy_url"]
        print(f"   (Found {len(streams)} streams. Top: {streams[0]['quality']} [{streams[0]['format']}])")
    test("Streams API", test_streams)

    def test_streaming_proxy():
        global proxy_stream_url
        assert proxy_stream_url, "No stream URL"
        r = requests.get(
            f"{base_url}{proxy_stream_url}",
            headers={"Range": "bytes=0-500"},
            timeout=10,
            stream=True
        )
        assert r.status_code == 206, f"Expected HTTP 206, got {r.status_code}"
        assert r.headers.get("Content-Range"), "Missing Content-Range header"
        assert r.headers.get("Accept-Ranges") == "bytes", "Missing Accept-Ranges header"
        chunk = next(r.iter_content(chunk_size=501))
        assert len(chunk) == 501, f"Expected 501 bytes, got {len(chunk)}"
        print(f"   (Proxy streamed 206 Partial Content: {r.headers.get('Content-Range')})")
    test("Video Streaming Proxy (Range Support)", test_streaming_proxy)

finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()

print("=" * 50)
print(f"Tests Completed: {passed} Passed, {failed} Failed")
print("=" * 50)
