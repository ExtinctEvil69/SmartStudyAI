"""BrahmaVidya — FastAPI application.

Unified learning ecosystem with Vidya Smriti shared memory.
Run with: uvicorn brahmavidya.app:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Allow importing core engines from parent project
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brahmavidya.memory import get_dashboard_data, LearnerProfile
from brahmavidya.tools.netseek import router as netseek_router
from brahmavidya.tools.edutube import router as edutube_router
from brahmavidya.tools.quizforge import router as quizforge_router
from brahmavidya.tools.neuroread import router as neuroread_router
from brahmavidya.tools.mindmapper import router as mindmapper_router
from brahmavidya.tools.prepmaster import router as prepmaster_router
from brahmavidya.tools.smriti_api import router as smriti_router

app = FastAPI(title="BrahmaVidya", version="1.0.0")

# ── Static files & templates ─────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


# ── Page routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    dashboard = get_dashboard_data()
    return templates.TemplateResponse(request=request, name="index.html", context={"dashboard": dashboard})


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    from core.gemma_engine import _ollama_available, list_models
    ollama_ok = _ollama_available()
    models = list_models() if ollama_ok else []
    gemma_ok = any("gemma" in m.lower() for m in models)
    return {
        "status": "ok",
        "ollama": ollama_ok,
        "gemma": gemma_ok,
        "models": models,
    }


# ── Tool routers ─────────────────────────────────────────────────────────────

app.include_router(netseek_router, prefix="/api/netseek", tags=["NetSeek"])
app.include_router(edutube_router, prefix="/api/edutube", tags=["EduTube"])
app.include_router(quizforge_router, prefix="/api/quizforge", tags=["QuizForge"])
app.include_router(neuroread_router, prefix="/api/neuroread", tags=["NeuroRead"])
app.include_router(mindmapper_router, prefix="/api/mindmapper", tags=["MindMapper"])
app.include_router(prepmaster_router, prefix="/api/prepmaster", tags=["PrepMaster"])
app.include_router(smriti_router, prefix="/api/smriti", tags=["VidyaSmriti"])
