"""Gemma 4 inference wrapper backed by Ollama."""

import json
from dataclasses import dataclass

import requests

from core.settings import get_ollama_base

DEFAULT_MODEL = "gemma4:e2b"


@dataclass
class GemmaConfig:
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096
    num_ctx: int = 32768
    stream: bool = False
    system_prompt: str = ""


def _ollama_available() -> bool:
    try:
        r = requests.get(f"{get_ollama_base()}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """Return Ollama models that support text generation (excludes embedding-only)."""
    try:
        r = requests.get(f"{get_ollama_base()}/api/tags", timeout=5)
        r.raise_for_status()
        models = []
        for m in r.json().get("models", []):
            name = m["name"]
            family = m.get("details", {}).get("family", "")
            if family in ("nomic-bert", "bert", "all-minilm") or "embed" in name.lower():
                continue
            models.append(name)
        return models
    except Exception:
        return []


def generate(prompt: str, config: GemmaConfig | None = None, stream_callback=None) -> str:
    """Generate text using Ollama. Optionally stream tokens via callback."""
    cfg = config or GemmaConfig()
    payload = {
        "model": cfg.model,
        "prompt": prompt,
        "stream": cfg.stream or (stream_callback is not None),
        "options": {
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "num_predict": cfg.max_tokens,
            "num_ctx": cfg.num_ctx,
        },
    }
    if cfg.system_prompt:
        payload["system"] = cfg.system_prompt

    try:
        if stream_callback:
            r = requests.post(f"{get_ollama_base()}/api/generate", json={**payload, "stream": True}, stream=True, timeout=600)
            r.raise_for_status()
            full = []
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    full.append(token)
                    stream_callback("".join(full))
                if chunk.get("done"):
                    break
            return "".join(full)
        else:
            r = requests.post(f"{get_ollama_base()}/api/generate", json=payload, timeout=600)
            r.raise_for_status()
            return r.json().get("response", "")
    except requests.exceptions.RequestException as e:
        return f"[Ollama error: {e}. Check OLLAMA_HOST and confirm `ollama serve` is running.]"


def chat(messages: list[dict], config: GemmaConfig | None = None, stream_callback=None) -> str:
    """Chat completion using Ollama /api/chat endpoint."""
    cfg = config or GemmaConfig()
    payload = {
        "model": cfg.model,
        "messages": messages,
        "stream": stream_callback is not None,
        "options": {
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "num_predict": cfg.max_tokens,
            "num_ctx": cfg.num_ctx,
        },
    }

    try:
        if stream_callback:
            r = requests.post(f"{get_ollama_base()}/api/chat", json=payload, stream=True, timeout=600)
            r.raise_for_status()
            full = []
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    full.append(token)
                    stream_callback("".join(full))
                if chunk.get("done"):
                    break
            return "".join(full)
        else:
            r = requests.post(f"{get_ollama_base()}/api/chat", json=payload, timeout=600)
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "")
    except requests.exceptions.RequestException as e:
        return f"[Ollama error: {e}]"


def generate_json(prompt: str, config: GemmaConfig | None = None) -> dict | None:
    """Generate and parse JSON output. Returns None on parse failure."""
    cfg = config or GemmaConfig()
    cfg.temperature = 0.3  # Lower temp for structured output
    result = generate(prompt, cfg)
    # Try to extract JSON from the response
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # Try to find JSON in markdown code blocks
        import re
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", result, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return None


def embed(texts: list[str], model: str = "nomic-embed-text:latest") -> list[list[float]]:
    """Generate embeddings using Ollama."""
    results = []
    for text in texts:
        r = requests.post(f"{get_ollama_base()}/api/embed", json={"model": model, "input": text}, timeout=60)
        r.raise_for_status()
        results.append(r.json()["embeddings"][0])
    return results
