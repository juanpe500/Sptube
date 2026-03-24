import re
import urllib.parse
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_youtube(query: str) -> str | None:
    """
    Search YouTube and return the first video URL.
    Returns None if no result found.
    """
    encoded = urllib.parse.quote(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    resp = httpx.get(search_url, headers=HEADERS, follow_redirects=True, timeout=15)
    resp.raise_for_status()

    # YouTube embeds video IDs in the page as "videoId":"XXXXXXXXXXX"
    matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
    if matches:
        video_id = matches[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return None


def to_embed_url(youtube_url: str) -> str:
    """
    Convert a YouTube watch URL to a nocookie embed URL with autoplay + loop.
    
    Input:  https://www.youtube.com/watch?v=duFRnVo2LXg
    Output: https://www.youtube-nocookie.com/embed/duFRnVo2LXg?playlist=duFRnVo2LXg&autoplay=1&iv_load_policy=3&loop=1&start=
    """
    match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", youtube_url)
    if not match:
        # Maybe it's already an embed or short URL
        match = re.search(r"(?:embed/|youtu\.be/)([a-zA-Z0-9_-]{11})", youtube_url)
    if not match:
        raise ValueError(f"Could not extract video ID from: {youtube_url}")

    video_id = match.group(1)
    return (
        f"https://www.yout-ube.com/embed/{video_id}"
        f"?playlist={video_id}&autoplay=1&mute=1&enablejsapi=1&iv_load_policy=3&loop=1&start="
    )


# By JP