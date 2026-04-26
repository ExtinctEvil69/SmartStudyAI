"""YouTube lecture source — fetches transcripts for one or more videos.

Supports both:
- Explicit video lists [(video_id, title), ...]
- Playlist extraction via yt-dlp if installed (graceful fallback otherwise)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.youtube_engine import fetch_transcript

name = "youtube"


def fetch(spec: dict) -> list[dict]:
    """Returns list of {text, title, source_id, source_kind, meta}.

    spec accepts either:
      {"videos": [(id, title), ...], "subject": "Physics"}
      {"playlist_url": "...", "subject": "Physics", "max_videos": 10}
    """
    subject = spec.get("subject", "General")
    docs: list[dict] = []

    videos = spec.get("videos") or []
    if not videos and spec.get("playlist_url"):
        videos = _extract_playlist(spec["playlist_url"], spec.get("max_videos", 20))

    for video_id, title in videos:
        try:
            transcript = fetch_transcript(video_id)
        except Exception as exc:
            print(f"  ✗ {video_id}: {exc}")
            continue
        if len(transcript) < 500:
            continue
        docs.append({
            "text": transcript,
            "title": title,
            "source_id": f"youtube:{video_id}",
            "source_kind": "lecture_transcript",
            "meta": {"video_id": video_id, "subject": subject, "url": f"https://youtube.com/watch?v={video_id}"},
        })
    return docs


def _extract_playlist(playlist_url: str, max_videos: int) -> list[tuple[str, str]]:
    """Use yt-dlp (if available) to enumerate playlist video IDs + titles."""
    if not shutil.which("yt-dlp"):
        print("  ⚠ yt-dlp not installed — install with: pip install yt-dlp")
        print("    Falling back to empty list. Add explicit videos= to the recipe instead.")
        return []
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print", "%(id)s\t%(title)s",
             "--playlist-end", str(max_videos), playlist_url],
            capture_output=True, text=True, timeout=60,
        )
        pairs: list[tuple[str, str]] = []
        for line in result.stdout.strip().split("\n"):
            if "\t" in line:
                vid, title = line.split("\t", 1)
                pairs.append((vid.strip(), title.strip()))
        return pairs
    except Exception as exc:
        print(f"  ⚠ playlist extraction failed: {exc}")
        return []
