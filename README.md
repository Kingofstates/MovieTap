# 🎬 Room 206 - Cinema & Anime Streaming Platform

A sleek, cinema-grade web interface and multi-engine streaming platform referenced and reverse-engineered from [mesamirh/MovieBox-TUI](https://github.com/mesamirh/MovieBox-TUI).

While **MovieBox-TUI** is built for terminal environments (requiring Termux on Android or a Linux/macOS console) and external video players (`mpv`, `vlc`, `iina`), **Room 206** delivers the entire experience into any modern web browser on PC, Mac, Android, iPhone, iPad, and Smart TVs—with **zero external players, zero Termux, and zero setup required**.

---

## 🌟 Key Features

- **🌐 Zero External Player / Termux Requirement**: Plays full 1080p, 720p, and 480p streams directly in your browser using an HTML5 cinema player.
- **⚡ In-Memory Response Caching (Instant Load)**:
  - Homepage, Movies, TV Series, Anime, and Marvel catalogs are cached in memory with automatic background pre-warming.
  - Page loads and button switches are instantaneous (< 5ms) without hanging or stalling.
- **🐲 Integrated Anime Engine**:
  - Gathers anime directly from **MovieBox Anime (Tab 3)**, **AnimeWorld India (watchanimeworld.one)** for Hindi, Telugu, and Tamil dubs, and **HiAnime (hianime.biz.pl)** for international sub/dub catalogs.
  - Dedicated **Anime** navigation button and category filter pill.
- **🦸 Marvel MCU Release Chronology**:
  - Clicking the **Marvel** category sorts all movies according to Marvel's official chronological release order:
  - **Latest on top** (*Deadpool & Wolverine*, *The Marvels*, *Guardians of the Galaxy Vol. 3*, down through the phases) and the first movie (**Iron Man 2008**) at the very bottom!
- **⚡ High-Performance Range Streaming Proxy**:
  - Forwards HTTP byte-range requests (`206 Partial Content`), authentication signatures, and dynamically adapts headers to eliminate 429/428 errors, enabling instant seeking, fast buffering, and scrub support.
- **🔍 Multi-Engine Search & Aggregator**:
  - Automatically queries across **MovieBox**, **Dramachi**, **4KHDHub**, **AnimeWorld India**, and **HiAnime** concurrently.
  - Rich autocomplete suggestions with high-resolution poster thumbnails appear dynamically as you type.
- **🎧 Disney+ / Hotstar Style Audio Dub Selector**:
  - Prioritizes **Telugu Dubbed** audio by default across multi-audio releases, along with Hindi, Tamil, and English.
  - Interactive language switcher allows instant dub switching in modal details and player drawer.
- **📥 In-Browser Downloader with Embedded Subtitles**:
  - Download full movies directly to your browser's Downloads folder.
  - Uses native **FFmpeg** stream muxing (`-c:v copy -c:a copy -c:s mov_text`) to embed your chosen subtitle track directly inside a single `.mp4` video container on the fly—no separate subtitle files required!
- **🖼️ Dark Anime Aesthetics**:
  - Sharp, unblurred, dark background artwork.
  - Changes randomly upon page refresh without distracting interval flashes.
- **💬 Isolated Subtitle Engine**:
  - Native WebVTT track mode suppression prevents duplicate subtitle dialogue.
  - High-clarity subtitle overlay with toggle support.
- **⏯️ Watch History & Watchlist**:
  - Automatically records watch progress to `localStorage` with prompt to resume.
  - One-click bookmarking to personal watchlist.

---

## 🚀 Deployment on Render.com

Room 206 is fully optimized for **Render.com** (Free or Paid plans).

### Can Render handle it?
**Yes!**
1. **Low RAM footprint**: The streaming proxy uses async chunked streaming (`httpx.aiter_bytes`). Memory consumption is ~25-40 MB total, easily fitting in Render's 512 MB free tier.
2. **Dynamic Port Binding**: The application reads `PORT` from the environment automatically.
3. **Docker + FFmpeg Ready**: The included `Dockerfile` installs Python and system FFmpeg, so subtitle muxing works out-of-the-box.

### Option A: 1-Click Render Blueprint
1. Push this repository to your GitHub account (`Kingofstates/MovieTap`).
2. In [Render Dashboard](https://dashboard.render.com/), click **New +** -> **Blueprint**.
3. Select this repository. Render automatically reads `render.yaml` and deploys your service.

### Option B: Manual Web Service on Render
1. Click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Select **Docker** environment (or Python 3).
4. Set Instance Type to **Free**.
5. Click **Deploy Web Service**!

> **Render Free Tier Note**: Free services automatically spin down after 15 minutes of inactivity. The first visit after spin-down may take ~45-50 seconds to boot up. Subsequent streaming and browsing is fast.

---

## 💻 Local Quick Start

### 1. Requirements
- Python 3.10+
- FFmpeg (installed and on PATH)

### 2. Installation & Run
```bash
# Clone the repository
git clone https://github.com/Kingofstates/MovieTap.git
cd MovieTap

# Install dependencies
pip install -r requirements.txt

# Start Room 206
python run.py
```

Open your browser to:
**`http://localhost:8000`**

---

## ⌨️ Player Shortcuts
- `Space` / `K`: Play / Pause
- `Left` / `Right`: Seek 10s backward / forward
- `Up` / `Down`: Volume up / down
- `F`: Toggle Fullscreen
- `M`: Mute / Unmute
- `C`: Toggle Subtitles
- `A`: Audio & Subtitles Drawer
- `Esc`: Close Player / Modal

---

## 📜 Attribution & Credits
- Author: `king tech 1120`
- Referenced and reverse-engineered from [mesamirh/MovieBox-TUI](https://github.com/mesamirh/MovieBox-TUI).
- Licensed under Apache 2.0 / MIT.
