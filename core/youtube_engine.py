"""YouTube transcript helpers for EduTube."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    if not value:
        raise ValueError("Enter a YouTube URL or video ID.")

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    parsed = urlparse(value)
    if parsed.netloc.endswith("youtu.be"):
        video_id = parsed.path.strip("/")
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return video_id

    query_video_id = parse_qs(parsed.query).get("v", [""])[0]
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", query_video_id):
        return query_video_id

    raise ValueError("Could not extract a valid YouTube video ID from that input.")


def fetch_transcript(url_or_id: str, languages: tuple[str, ...] = ("en",)) -> str:
    video_id = extract_video_id(url_or_id)
    preferred_languages = list(languages) + ["en-US", "en-GB"]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred_languages)
    except AttributeError:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=preferred_languages)
    except Exception as exc:
        raise ValueError(f"Could not fetch transcript: {exc}") from exc

    parts: list[str] = []
    for segment in transcript:
        # Support both dict (old API) and dataclass (new API) transcript formats
        text = segment.get("text", "") if isinstance(segment, dict) else getattr(segment, "text", "")
        text = text.strip()
        if text:
            parts.append(text)
    return "\n".join(parts)
