import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

# Wait for server to boot
time.sleep(2)

def test_endpoint(name, url):
    t0 = time.time()
    try:
        r = requests.get(url, timeout=12)
        elapsed = round((time.time() - t0) * 1000, 1)
        if r.status_code == 200:
            data = r.json() if "application/json" in r.headers.get("content-type", "") else {}
            count = len(data.get("items", [])) if isinstance(data, dict) else len(r.text)
            cached = data.get("cached", False) if isinstance(data, dict) else False
            print(f"✅ {name}: HTTP {r.status_code} | {elapsed}ms | Count: {count} | Cached: {cached}")
            return data
        else:
            print(f"❌ {name}: HTTP {r.status_code} | {elapsed}ms | Body: {r.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return None

print("=== TESTING ROOM 206 BACKEND ===")

# 1. Test HTML
try:
    r = requests.get(BASE_URL + "/", timeout=5)
    print(f"✅ Homepage HTML: HTTP {r.status_code} | 'Room 206': {'Room 206' in r.text} | 'king tech 1120': {'king tech 1120' in r.text}")
except Exception as e:
    print(f"❌ Homepage HTML error: {e}")

# 2. Test All Homepage
d_all = test_endpoint("Tab All", f"{BASE_URL}/api/homepage?tab=all&page=1")

# 3. Test Movies Tab
d_movies = test_endpoint("Tab Movies", f"{BASE_URL}/api/homepage?tab=movies&page=1")

# 4. Test Series Tab
d_series = test_endpoint("Tab Series", f"{BASE_URL}/api/homepage?tab=series&page=1")

# 5. Test Anime Tab
d_anime = test_endpoint("Tab Anime", f"{BASE_URL}/api/homepage?tab=anime&page=1")
if d_anime and d_anime.get("items"):
    print("   Sample Anime titles:")
    for a in d_anime["items"][:5]:
        print(f"     - {a.get('title')} ({a.get('year', '')})")

# 6. Test Marvel MCU Chronology
d_marvel = test_endpoint("Marvel MCU Catalog", f"{BASE_URL}/api/marvel")
if d_marvel and d_marvel.get("items"):
    m_items = d_marvel["items"]
    print("   Marvel items total:", len(m_items))
    print(f"   Top 3 (Latest): {[i.get('title') + ' (' + str(i.get('year')) + ')' for i in m_items[:3]]}")
    print(f"   Bottom 3 (First): {[i.get('title') + ' (' + str(i.get('year')) + ')' for i in m_items[-3:]]}")

# 7. Test Instant Caching (<5ms response)
t0 = time.time()
r_cached = requests.get(f"{BASE_URL}/api/homepage?tab=movies&page=1")
print(f"⚡ Instant Cached Movies Request: HTTP {r_cached.status_code} in {round((time.time() - t0)*1000, 2)}ms")

# 8. Test Multi-Engine Search
d_search = test_endpoint("Search Anime (Naruto)", f"{BASE_URL}/api/search?q=naruto&provider=all")
if d_search and d_search.get("items"):
    providers_found = set(i.get("provider") for i in d_search["items"])
    print(f"   Providers returned: {providers_found}")

print("=== ALL TESTS COMPLETE ===")
