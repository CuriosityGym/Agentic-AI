"""
transcript.py — YouTube URL helpers and transcript fetching via MySphere proxy.

What this file does:
    1. Detects a YouTube link inside any text string
    2. Extracts the video ID from the link
    3. Calls the MySphere API proxy to get the full spoken transcript of the video

Students: You should NOT need to edit this file.
"""

import re
import requests

from config import TRANSCRIPT_URL, _api_key_store, _store_lock


# ── YouTube URL & ID patterns ──────────────────────────────────────────────
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
    Call the MySphere proxy to retrieve the full video transcript as plain text.

    Args:
        youtube_url: A full YouTube URL (e.g. https://youtu.be/abc123)

    Returns:
        The full transcript as a single string of text.

    Raises:
        EnvironmentError: If no active session token is found (codespace not registered).
        ValueError:       If the video has no captions, is private, or the proxy fails.
    """
    with _store_lock:
        store = _api_key_store.get("active")

    if not store or not store.get("key"):
        raise EnvironmentError(
            "No active session token. Please register your codespace first."
        )

    token = store["key"]
    print(f"Using session token: {token[:30]}...")  # Debug log (only show the beginning for security)

    resp = requests.get(
        TRANSCRIPT_URL,
        headers={"gradio-token": token},
        params={"url": youtube_url, "lang": "en", "text": "true"},
        timeout=30,
    )

    if resp.status_code == 401:
        raise EnvironmentError(
            "Session token is invalid or expired. Please register your codespace again."
        )
    if resp.status_code == 404:
        raise ValueError(
            "Transcript unavailable. The video may be private, "
            "age-restricted, or have captions disabled."
        )
    if resp.status_code != 200:
        raise ValueError(f"Proxy error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()

    content = data.get("content", data.get("transcript", data.get("text", "")))
    print(f"Raw transcript content: {content}...")  # Debug log
    if isinstance(content, list):
        return " ".join(
            seg.get("text", str(seg)) if isinstance(seg, dict) else str(seg)
            for seg in content
        )
    return str(content)