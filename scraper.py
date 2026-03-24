import re
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_spotify_track(url: str) -> dict:
    """
    Get song title and artist from a Spotify track URL.
    
    Strategy:
    1. oEmbed API → gets the song title (reliable, no JS needed)
    2. Embed page HTML → has artist name in a link to /artist/... 
       (server-rendered, unlike the main track page which is a JS SPA)
    """
    track_id = url.rstrip("/").split("/")[-1].split("?")[0]
    title = "Unknown"
    artist = "Unknown Artist"

    # ── Step 1: oEmbed for the title ───────────────────────────────────
    try:
        oembed_url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/track/{track_id}"
        resp = httpx.get(oembed_url, timeout=15)
        data = resp.json()
        title = data.get("title", "Unknown")
    except Exception:
        pass

    # ── Step 2: Embed page for the artist ──────────────────────────────
    try:
        embed_url = f"https://open.spotify.com/embed/track/{track_id}"
        resp = httpx.get(embed_url, headers=HEADERS, follow_redirects=True, timeout=15)
        html = resp.text

        # Artist is in: <a href="https://open.spotify.com/artist/...">ArtistName</a>
        artist_match = re.search(
            r'href="https://open\.spotify\.com/artist/[^"]+[^>]*>([^<]+)</a>',
            html,
        )
        if artist_match:
            artist = artist_match.group(1).strip()
    except Exception:
        pass

    if title == "Unknown" and artist == "Unknown Artist":
        raise RuntimeError(f"Failed to scrape {url}")

    return {"title": title, "artist": artist}

# By JP