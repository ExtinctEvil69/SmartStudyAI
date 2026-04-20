"""Text-to-speech helpers for AudioOverview."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gtts import gTTS


AUDIO_DIR = Path(__file__).parent.parent / "data" / "audio_cache"


def _slugify(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_ " else "_" for char in value)
    return "_".join(cleaned.split())[:80] or "audio_overview"


def synthesize_speech(text: str, title: str = "Audio Overview", lang: str = "en") -> Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_slugify(title)}.mp3"
    output_path = AUDIO_DIR / filename
    clipped_text = text.strip()[:4500]
    if not clipped_text:
        raise ValueError("No text available for audio synthesis.")
    tts = gTTS(text=clipped_text, lang=lang)
    tts.save(str(output_path))
    return output_path
