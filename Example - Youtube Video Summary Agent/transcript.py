"""
transcript.py — YouTube URL helpers and transcript fetching via Supadata.ai.

What this file does:
    1. Detects a YouTube link inside any text string
    2. Extracts the video ID from the link
    3. Calls the Supadata.ai API to get the full spoken transcript of the video

Students: You should NOT need to edit this file.
"""

import re
import requests

from config import SUPDATA_API_KEY, SUPDATA_BASE_URL


# ── YouTube URL & ID patterns ──────────────────────────────────────────────
# These regex patterns match all common YouTube URL formats.
_YT_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtu\.be/|youtube\.com/(?:watch\?[^\s]*v=|shorts/|embed/))[^\s<>\"']*"
)
_YT_ID_PATTERNS = [
    re.compile(r"youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/watch\?[^\s]*v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
]


def extract_youtube_url(text: str) -> str | None:
    """Find and return the first YouTube URL found in a string of text."""
    m = _YT_URL_RE.search(text)
    return m.group(0) if m else None


def extract_video_id(url: str) -> str | None:
    """Extract the 11-character video ID from a YouTube URL."""
    for pattern in _YT_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    return None


def fetch_transcript(youtube_url: str) -> str:
    """
    Call Supadata.ai to retrieve the full video transcript as plain text.

    Args:
        youtube_url: A full YouTube URL (e.g. https://youtu.be/abc123)

    Returns:
        The full transcript as a single string of text.

    Raises:
        EnvironmentError: If SUPDATA_API_KEY is missing from .env.
        ValueError:       If the video is private, has no captions, or the API fails.

    ── Development tip ───────────────────────────────────────────────────────
    To avoid real API calls while testing, comment out the requests.get() block
    and uncomment the dummy_data block below it.
    """
    if not SUPDATA_API_KEY:
        raise EnvironmentError("SUPDATA_API_KEY is not set. Add it to your .env file.")

    # ── Live API call ──────────────────────────────────────────────────────
    resp = requests.get(
        f"{SUPDATA_BASE_URL}/youtube/transcript",
        headers={"x-api-key": SUPDATA_API_KEY},
        params={"url": youtube_url, "lang": "en", "text": "true"},
        timeout=30,
    )

    if resp.status_code == 401:
        raise ValueError("Invalid Supdata API key. Check SUPDATA_API_KEY in .env.")
    if resp.status_code == 404:
        raise ValueError(
            "Transcript unavailable. The video may be private, "
            "age-restricted, or have captions disabled."
        )
    if resp.status_code != 200:
        raise ValueError(f"Supdata API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()

    # ── Dummy data for development (swap in when you don't want real API calls) ──
    # data = {
    #     "content": "hello this is a sample transcript for testing purposes only..."
    # }

    # Supadata returns {"content": "full text..."} when ?text=true is used.
    # Without ?text=true it returns {"content": [{"text": "...", "offset": 0}, ...]}
    content = data.get("content", data.get("transcript", data.get("text", "")))

    if isinstance(content, list):
        return " ".join(
            seg.get("text", str(seg)) if isinstance(seg, dict) else str(seg)
            for seg in content
        )
    return str(content)