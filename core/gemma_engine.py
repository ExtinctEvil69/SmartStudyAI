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
    """Generate and parse JSON output. Returns None on parse failure.

    Robust to:
      - markdown ```json fences
      - LaTeX in string values (\vec, \hat, \frac — not valid JSON escapes)
    """
    cfg = config or GemmaConfig()
    cfg.temperature = 0.3
    result = generate(prompt, cfg)
    return _parse_json_lenient(result)


def _parse_json_lenient(text: str) -> dict | None:
    """Try several parse strategies before giving up."""
    if not text:
        return None
    import re

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    candidate = match.group(1) if match else text

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 3. Escape lone backslashes not part of a valid JSON escape (\vec, \hat, \frac, ...)
    fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', candidate)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 4. Last resort — find the largest {...} block and try again
    brace_match = re.search(r"\{.*\}", fixed, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
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
