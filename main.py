import asyncio
import threading
import time

from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database as db
from scraper import scrape_spotify_track
from youtube import search_youtube, to_embed_url

app = FastAPI(title="Sptube")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize DB on startup
db.init_db()


# ── Background import worker ──────────────────────────────────────────────

_import_lock = threading.Lock()


def _process_import():
    """Process all pending songs one-by-one with a delay."""
    songs = db.get_all_songs()
    pending = [s for s in songs if s["status"] == "pending"]

    for i, song in enumerate(pending):
        try:
            info = scrape_spotify_track(song["spotify_url"])
            db.update_song(song["id"], info["title"], info["artist"], "scraped")
            try:
                print(f"  [OK] Scraped: {info['title']} - {info['artist']}")
            except Exception:
                pass
        except Exception as e:
            db.set_song_error(song["id"], str(e))
            try:
                print(f"  [ERR] Error for {song['spotify_url']}: {e}")
            except Exception:
                pass

        # Delay between requests to avoid getting blocked
        if i < len(pending) - 1:
            time.sleep(3)

    _import_lock.release()


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    songs = db.get_all_songs()
    pending = db.get_pending_count()
    playlists = db.get_all_playlists()
    return templates.TemplateResponse(request, "index.html", context={
        "songs": songs,
        "pending": pending,
        "playlists": playlists,
    })


@app.post("/import")
async def import_songs(urls: str = Form(...)):
    lines = [u.strip() for u in urls.strip().splitlines() if u.strip()]
    spotify_urls = [u for u in lines if "open.spotify.com/track/" in u]

    for url in spotify_urls:
        db.insert_song(url)

    # Start background processing if not already running
    if _import_lock.acquire(blocking=False):
        t = threading.Thread(target=_process_import, daemon=True)
        t.start()

    return RedirectResponse("/", status_code=303)


@app.post("/clear")
async def clear_songs():
    db.clear_all_songs()
    return RedirectResponse("/", status_code=303)


@app.post("/retry")
async def retry_songs():
    db.reset_stuck_songs()
    if _import_lock.acquire(blocking=False):
        t = threading.Thread(target=_process_import, daemon=True)
        t.start()
    return RedirectResponse("/", status_code=303)


@app.get("/yt/{video_id}")
async def yt_redirect(video_id: str):
    """Our own redirect proxy - like yout-ube.com but with OUR params.
    The 302 redirect chain tricks Chrome's autoplay policy."""
    target = (
        f"https://www.youtube-nocookie.com/embed/{video_id}"
        f"?autoplay=1&enablejsapi=1&iv_load_policy=3&rel=0&modestbranding=1"
    )
    return RedirectResponse(url=target, status_code=302)


@app.get("/api/songs")
async def api_songs():
    songs = db.get_all_songs()
    pending = db.get_pending_count()
    return {"songs": songs, "pending": pending}


@app.get("/api/search-youtube")
async def api_search_youtube(q: str, song_id: int = None):
    """Search YouTube for a query and return the embed URL + video ID."""
    import re as _re
    try:
        if song_id:
            song = db.get_song(song_id)
            if song and song.get("youtube_url"):
                vid = _re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", song["youtube_url"])
                embed = to_embed_url(song["youtube_url"])
                return {"youtube_url": song["youtube_url"], "embed_url": embed, "video_id": vid.group(1) if vid else None}

        yt_url = search_youtube(q)
        if not yt_url:
            return JSONResponse({"error": "No results found"}, status_code=404)
        embed = to_embed_url(yt_url)
        vid = _re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", yt_url)

        if song_id:
            db.set_youtube_url(song_id, yt_url)

        return {"youtube_url": yt_url, "embed_url": embed, "video_id": vid.group(1) if vid else None}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Playlist API ───────────────────────────────────────────────────────────

@app.get("/api/playlists")
async def api_list_playlists():
    return db.get_all_playlists()


@app.post("/api/playlists")
async def api_create_playlist(name: str = Body(..., embed=True)):
    pid = db.create_playlist(name)
    return {"id": pid, "name": name}


@app.delete("/api/playlists/{playlist_id}")
async def api_delete_playlist(playlist_id: int):
    db.delete_playlist(playlist_id)
    return {"ok": True}


@app.put("/api/playlists/{playlist_id}")
async def api_rename_playlist(playlist_id: int, name: str = Body(..., embed=True)):
    db.rename_playlist(playlist_id, name)
    return {"ok": True}


@app.get("/api/playlists/{playlist_id}/songs")
async def api_playlist_songs(playlist_id: int):
    return db.get_playlist_songs(playlist_id)


@app.post("/api/playlists/{playlist_id}/songs")
async def api_add_to_playlist(playlist_id: int, song_id: int = Body(..., embed=True)):
    db.add_song_to_playlist(playlist_id, song_id)
    return {"ok": True}


@app.delete("/api/playlists/{playlist_id}/songs/{song_id}")
async def api_remove_from_playlist(playlist_id: int, song_id: int):
    db.remove_song_from_playlist(playlist_id, song_id)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# By JP