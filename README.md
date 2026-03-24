# Sptube 🎵▶️

**Spotify to YouTube — Free Music Player**

Import your Spotify track URLs and Sptube automatically finds them on YouTube, creating an auto-playing playlist with seamless song transitions. Runs as a local desktop app with **zero API keys** required.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-darkgreen?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- **Spotify URL Import** — Paste one or multiple Spotify track URLs and Sptube scrapes the metadata (title + artist) automatically
- **YouTube Auto-Search** — Finds each song on YouTube and caches the result so repeat plays are instant
- **Seamless Autoplay** — Songs play one after another with full sound — no manual clicking required
- **Playback Modes:**
  - ▶️ **Sequential** — plays in order (default)
  - 🔀 **Shuffle** — randomized play order
  - 🔁 **Repeat All** — loops the entire playlist
  - 🔂 **Repeat One** — loops the current song
- **Custom Playlists** — Create, manage, and switch between playlists
- **Keyboard Shortcuts:**
  - `→` or `n` — Next song
  - `←` or `p` — Previous song
  - `s` — Toggle shuffle
  - `r` — Cycle repeat mode
- **Dark Theme** — Spotify-inspired premium dark UI
- **Persistent Storage** — SQLite database stores all songs and YouTube URL cache

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Google Chrome** or **Microsoft Edge** (Chromium-based)

### Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/juanpabloxk/Sptube.git
   cd Sptube
   ```

2. **Run Sptube:**

   **Windows:**
   ```bash
   start.bat
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies
   - Start the FastAPI server on `http://localhost:8002`
   - Launch Chrome/Edge with autoplay enabled (the magic flag!)

   **Linux/macOS:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8002 &
   
   # Launch Chrome with autoplay bypass:
   google-chrome --autoplay-policy=no-user-gesture-required --app=http://localhost:8002
   ```

3. **Import your Spotify tracks:**
   - Click **"＋ Import Spotify Tracks"**
   - Paste Spotify track URLs (one per line):
     ```
     https://open.spotify.com/track/6FY8Imjs6YSglIAqnbU9mM
     https://open.spotify.com/track/5jM3TXYc0jYFSJVNUFhfU8
     ```
   - Click **"Import & Process"**
   - Wait for scraping to complete (a few seconds per track)

4. **Click any song to start playing!**

## 🏗️ How It Works

```
Spotify URL → Scrape metadata (title + artist) → Search YouTube → Play via YT IFrame API
```

1. **Scraper** (`scraper.py`): Uses Spotify's oEmbed API for the title and the embed page HTML for the artist name. No Spotify API key needed.

2. **YouTube Search** (`youtube.py`): Scrapes YouTube search results to find the first matching video. No YouTube API key needed.

3. **Player**: Uses the official [YouTube IFrame API](https://developers.google.com/youtube/iframe_api_reference) with a **single persistent player instance**. When a song ends, `loadVideoById()` loads the next one — preserving the browser's autoplay context.

4. **The Autoplay Trick**: Chrome's `--autoplay-policy=no-user-gesture-required` flag completely bypasses browser autoplay restrictions. This is why Sptube launches Chrome with this flag via `start.bat`.

## 📁 Project Structure

```
Sptube/
├── main.py             # FastAPI server + API endpoints
├── database.py         # SQLite DB (songs, playlists)
├── scraper.py          # Spotify metadata scraper
├── youtube.py          # YouTube search + URL helpers
├── requirements.txt    # Python dependencies
├── start.bat           # Windows launcher (server + Chrome)
├── static/
│   └── style.css       # Dark theme styles
└── templates/
    └── index.html      # Frontend (Jinja2 template)
```

## 🎛️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main page |
| `POST` | `/import` | Import Spotify URLs |
| `POST` | `/clear` | Delete all songs |
| `POST` | `/retry` | Retry failed scrapes |
| `GET` | `/api/songs` | List all songs + pending count |
| `GET` | `/api/search-youtube?q=...&song_id=...` | Search YouTube (with caching) |
| `GET` | `/api/playlists` | List all playlists |
| `POST` | `/api/playlists` | Create playlist `{"name": "..."}` |
| `DELETE` | `/api/playlists/{id}` | Delete playlist |
| `PUT` | `/api/playlists/{id}` | Rename playlist `{"name": "..."}` |
| `GET` | `/api/playlists/{id}/songs` | Get playlist songs |
| `POST` | `/api/playlists/{id}/songs` | Add song `{"song_id": 1}` |
| `DELETE` | `/api/playlists/{id}/songs/{song_id}` | Remove song |

## ⚠️ Notes

- **For personal/local use only.** This tool scrapes public web pages — heavy usage may trigger rate limiting.
- **No API keys required.** Everything works via web scraping.
- The SQLite database (`sptube.db`) is created automatically on first run.
- A 3-second delay between scrapes helps avoid being blocked.

## 📄 License

[MIT License](LICENSE) — Free to use, modify, and distribute.
