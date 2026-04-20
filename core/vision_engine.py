"""Vision helper utilities for multimodal Gemma document workflows.

This module does not replace a full vision fine-tuning run, but it provides the
planned `vision_engine.py` interface for photographed notes, PDF pages, and
chart-like document analysis when a multimodal Ollama model is available.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

import fitz
import requests

from core.gemma_engine import DEFAULT_MODEL, GemmaConfig
from core.settings import get_ollama_base


@dataclass
class VisionConfig:
    model: str = DEFAULT_MODEL
    temperature: float = 0.2
    max_tokens: int = 2048


def render_pdf_pages(file_bytes: bytes, max_pages: int = 3, zoom: float = 1.5) -> list[bytes]:
    document = fitz.open(stream=file_bytes, filetype="pdf")
    rendered_pages: list[bytes] = []
    matrix = fitz.Matrix(zoom, zoom)
    for page_index in range(min(max_pages, len(document))):
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        rendered_pages.append(pixmap.tobytes("png"))
    return rendered_pages


def analyze_image_bytes(prompt: str, image_bytes: bytes, config: VisionConfig | None = None) -> str:
    cfg = config or VisionConfig()
    payload = {
        "model": cfg.model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [base64.b64encode(image_bytes).decode("utf-8")],
            }
        ],
        "stream": False,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": cfg.max_tokens,
        },
    }
    response = requests.post(f"{get_ollama_base()}/api/chat", json=payload, timeout=300)
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "")


def analyze_pdf_pages(file_bytes: bytes, instruction: str, config: VisionConfig | None = None, max_pages: int = 3) -> str:
    pages = render_pdf_pages(file_bytes, max_pages=max_pages)
    page_summaries: list[str] = []
    for index, page_bytes in enumerate(pages, start=1):
        summary = analyze_image_bytes(f"Page {index}: {instruction}", page_bytes, config=config)
        page_summaries.append(f"## Page {index}\n{summary}")
    return "\n\n".join(page_summaries)


def extract_structured_document_info(file_bytes: bytes, fields: list[str], config: VisionConfig | None = None) -> dict | None:
    instruction = (
        "Extract the following fields from this educational document page: "
        f"{', '.join(fields)}. Return valid JSON only."
    )
    pages = render_pdf_pages(file_bytes, max_pages=1)
    if not pages:
        return None
    raw = analyze_image_bytes(instruction, pages[0], config=config)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
