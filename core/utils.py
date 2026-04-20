"""Shared utilities for SmartStudy AI."""

import io
from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(file_bytes: bytes, max_chars: int = 100_000) -> str:
    """Extract text from PDF bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    total = 0
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        parts.append(text)
        total += len(text)
        if total >= max_chars:
            break
    return "\n".join(parts)[:max_chars]


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def truncate_text(text: str, max_tokens_approx: int = 30000) -> str:
    """Truncate text to approximate token count (4 chars ~ 1 token)."""
    max_chars = max_tokens_approx * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated ...]"
