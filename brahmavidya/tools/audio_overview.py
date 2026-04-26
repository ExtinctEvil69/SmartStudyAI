"""AudioOverview — generate a podcast-style narration with gTTS.

Pipeline:
  1. Gemma rewrites the source content as a conversational script
  2. gTTS converts script → MP3
  3. Endpoint streams the MP3 back
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.gemma_engine import GemmaConfig, generate
from brahmavidya.memory import log_event

router = APIRouter()


class ScriptRequest(BaseModel):
    content: str
    style: str = "Podcast (conversational)"
    duration: str = "Short (3-5 min)"


class ScriptResponse(BaseModel):
    script: str


@router.post("/script", response_model=ScriptResponse)
async def script(req: ScriptRequest):
    """Generate the spoken script. Audio synthesis happens via /audio."""
    prompt = f"""Rewrite this content as a **{req.style}** spoken script.
Target length: **{req.duration}**.

Rules:
- No headings, no bullet points — flowing speech only
- Use plain English; no markdown
- Add natural pauses (commas, periods)
- Open with a hook, close with a takeaway

Content:
{req.content}"""

    cfg = GemmaConfig(temperature=0.5, max_tokens=2500)
    cfg.system_prompt = "You write engaging spoken-word scripts — clear, warm, never academic."
    out = generate(prompt, cfg)
    log_event("AudioOverview", "script_generated", req.content[:80], style=req.style)
    return ScriptResponse(script=out)


class AudioRequest(BaseModel):
    script: str
    accent: str = "us"   # us | uk | au | in


@router.post("/audio")
async def audio(req: AudioRequest):
    """Convert script text to MP3 audio (gTTS), stream it back."""
    try:
        from gtts import gTTS
    except ImportError:
        return {"error": "gTTS not installed. Run: .venv/bin/pip install gtts"}

    tld_map = {"us": "com", "uk": "co.uk", "au": "com.au", "in": "co.in"}
    tld = tld_map.get(req.accent, "com")

    tts = gTTS(text=req.script, lang="en", tld=tld, slow=False)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", prefix="polaris_audio_")
    tmp_path = Path(tmp.name)
    tmp.close()
    tts.save(str(tmp_path))

    log_event("AudioOverview", "audio_generated", "tts", accent=req.accent, length=len(req.script))
    return FileResponse(
        tmp_path,
        media_type="audio/mpeg",
        filename="polaris_overview.mp3",
        headers={"Content-Disposition": "inline; filename=polaris_overview.mp3"},
    )
