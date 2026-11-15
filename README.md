# 🎬 MovieTap - Cinema Streaming & Search Platform

A sleek, cinema-grade web interface and multi-engine streaming platform referenced and reverse-engineered from [mesamirh/MovieBox-TUI](https://github.com/mesamirh/MovieBox-TUI).

While **MovieBox-TUI** is built for terminal environments (requiring Termux on Android or a Linux/macOS console) and external video players (`mpv`, `vlc`, `iina`), **MovieTap** delivers the entire experience into any modern web browser on PC, Mac, Android, iPhone, iPad, and Smart TVs—with **zero external players, zero Termux, and zero setup required**.

---

## 🌟 Key Features

- **🌐 Zero External Player / Termux Requirement**: Plays full 1080p, 720p, and 480p streams directly in your browser using an HTML5 cinema player.
- **⚡ High-Performance Range Streaming Proxy**:
  - MovieBox CDN endpoints require specific mobile headers and reject standard web browsers.
  - MovieTap includes an asynchronous HTTP range proxy that forwards range requests (`206 Partial Content`), authentication signatures, and dynamically adapts headers to eliminate 429/428 errors, enabling instant seeking, fast buffering, and scrub support.
- **🔍 Multi-Engine Search & Aggregator**:
  - Automatically queries across **MovieBox**, **Dramachi**, and **4KHDHub** in parallel.
  - Rich autocomplete suggestions with high-resolution poster thumbnails appear dynamically as you type.
- **🎧 Disney+ / Hotstar Style Audio Dub Selector**:
  - Prioritizes **Telugu Dubbed** audio by default across multi-audio releases, along with Hindi, Tamil, and English.
  - Interactive language switcher allows instant dub switching in modal details and player drawer.
- **📥 In-Browser Downloader with Embedded Subtitles**:
  - Download full movies directly to your browser's Downloads folder.
  - Uses native **FFmpeg** stream muxing (`-c:v copy -c:a copy -c:s mov_text`) to embed your chosen subtitle track directly inside a single `.mp4` video container on the fly—no separate subtitle files required!
- **🖼️ Dark & High-Contrast Anime Aesthetics**:
  - Sharp, unblurred, dark background artwork inspired by AnimeWorld.
  - Changes randomly upon page refresh without distracting interval flashes.
  - Clean, unbranded poster cards without visual clutter.
- **🎞️ Complete Catalog (420+ Titles)**:
  - Aggregates Trending, Movies (Tab 2), and TV Series (Tab 5).
  - Smooth layout tabs navigate directly to movies and shows.
- **💬 Isolated Subtitle Engine**:
  - Native WebVTT track mode suppression prevents duplicate subtitle dialogue.
  - High-clarity subtitle overlay with toggle support.
- **⏯️ Watch History & Watchlist**:
  - Automatically records watch progress to `localStorage` with prompt to resume.
  - One-click bookmarking to personal watchlist.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- FFmpeg (installed and on PATH)

### 2. Installation & Run
```bash
# Clone the repository
git clone https://github.com/Kingofstates/MovieTap.git
cd MovieTap

# Install dependencies
pip install fastapi uvicorn httpx requests beautifulsoup4

# Start the MovieTap server
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
Referenced and reverse-engineered from [mesamirh/MovieBox-TUI](https://github.com/mesamirh/MovieBox-TUI).
Licensed under Apache 2.0 / MIT.
