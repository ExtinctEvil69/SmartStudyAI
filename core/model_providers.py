"""Multi-provider model routing — Gemma (default), Claude, OpenAI, Gemini.

All pages call `generate()` from this module. The active provider is
selected per-session in the sidebar.  Gemma runs locally via Ollama;
the others need API keys set as env vars.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import requests
import streamlit as st

from core.settings import get_ollama_base


# ── Provider registry ──────────────────────────────────────────────────────

PROVIDERS: dict[str, dict] = {
    "Gemma (Local)": {
        "id": "gemma",
        "models": [],          # populated dynamically from Ollama
        "default": "gemma4:e2b",
        "needs_key": False,
    },
    "Claude (Anthropic)": {
        "id": "claude",
        "models": [
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
        ],
        "default": "claude-sonnet-4-6",
        "needs_key": True,
        "key_env": "ANTHROPIC_API_KEY",
    },
    "OpenAI": {
        "id": "openai",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1-mini",
        ],
        "default": "gpt-4o-mini",
        "needs_key": True,
        "key_env": "OPENAI_API_KEY",
    },
    "Gemini (Google)": {
        "id": "gemini",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ],
        "default": "gemini-2.5-flash",
        "needs_key": True,
        "key_env": "GOOGLE_API_KEY",
    },
}


@dataclass
class ModelConfig:
    provider: str = "gemma"
    model: str = "gemma4:e2b"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""


# ── Ollama model listing ───────────────────────────────────────────────────

# Ollama model families that are embedding-only (cannot generate text)
_EMBED_ONLY_FAMILIES = {"nomic-bert", "bert", "all-minilm"}


def _list_ollama_models() -> list[str]:
    try:
        r = requests.get(f"{get_ollama_base()}/api/tags", timeout=3)
        r.raise_for_status()
        models = []
        for m in r.json().get("models", []):
            family = m.get("details", {}).get("family", "")
            name = m["name"]
            # Skip embedding-only models that can't generate text
            if family in _EMBED_ONLY_FAMILIES or "embed" in name.lower():
                continue
            models.append(name)
        return models
    except Exception:
        return []


def _ollama_available() -> bool:
    try:
        r = requests.get(f"{get_ollama_base()}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Sidebar model picker ──────────────────────────────────────────────────

def render_model_selector(tool_key: str = "global") -> ModelConfig:
    """Render a provider + model selector.  Returns the chosen ModelConfig.

    Call this in the sidebar or in a page column.  The selection is stored
    in session_state so it persists across reruns.
    """
    state_key = f"_provider_{tool_key}"
    model_key = f"_model_{tool_key}"

    # Populate Gemma models once
    if "_ollama_models" not in st.session_state:
        st.session_state._ollama_models = _list_ollama_models()
    ollama_models = st.session_state._ollama_models
    PROVIDERS["Gemma (Local)"]["models"] = ollama_models or ["gemma4:e2b"]

    provider_name = st.selectbox(
        "Provider",
        list(PROVIDERS.keys()),
        key=f"sel_provider_{tool_key}",
        help="Gemma runs locally via Ollama.  Others require API keys.",
    )
    provider = PROVIDERS[provider_name]

    # Check API key
    if provider["needs_key"]:
        key_env = provider.get("key_env", "")
        if not os.environ.get(key_env):
            st.caption(f"Set `{key_env}` env var to enable.")

    model = st.selectbox(
        "Model",
        provider["models"] or [provider["default"]],
        key=f"sel_model_{tool_key}",
    )

    return ModelConfig(provider=provider["id"], model=model)


# ── Unified generate ──────────────────────────────────────────────────────

def generate(
    prompt: str,
    config: ModelConfig | None = None,
    stream_callback=None,
) -> str:
    """Route generation to the active provider."""
    cfg = config or ModelConfig()

    if cfg.provider == "gemma":
        return _generate_ollama(prompt, cfg, stream_callback)
    elif cfg.provider == "claude":
        return _generate_claude(prompt, cfg, stream_callback)
    elif cfg.provider == "openai":
        return _generate_openai(prompt, cfg, stream_callback)
    elif cfg.provider == "gemini":
        return _generate_gemini(prompt, cfg, stream_callback)
    else:
        return f"[Unknown provider: {cfg.provider}]"


def generate_json(prompt: str, config: ModelConfig | None = None) -> dict | None:
    """Generate and parse JSON from any provider."""
    cfg = config or ModelConfig()
    cfg.temperature = 0.3
    result = generate(prompt, cfg)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", result, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return None


# ── Provider implementations ──────────────────────────────────────────────

def _generate_ollama(prompt: str, cfg: ModelConfig, stream_callback=None) -> str:
    payload = {
        "model": cfg.model,
        "prompt": prompt,
        "stream": stream_callback is not None,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": cfg.max_tokens,
        },
    }
    if cfg.system_prompt:
        payload["system"] = cfg.system_prompt

    try:
        if stream_callback:
            r = requests.post(
                f"{get_ollama_base()}/api/generate",
                json={**payload, "stream": True},
                stream=True,
                timeout=600,
            )
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
            r = requests.post(
                f"{get_ollama_base()}/api/generate", json=payload, timeout=600
            )
            r.raise_for_status()
            return r.json().get("response", "")
    except requests.exceptions.RequestException as e:
        return f"[Ollama error: {e}]"


def _generate_claude(prompt: str, cfg: ModelConfig, stream_callback=None) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "[Claude error: ANTHROPIC_API_KEY not set]"

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": cfg.model,
        "max_tokens": cfg.max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if cfg.system_prompt:
        body["system"] = cfg.system_prompt

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        text = "".join(
            block["text"] for block in data.get("content", []) if block.get("type") == "text"
        )
        if stream_callback:
            stream_callback(text)
        return text
    except Exception as e:
        return f"[Claude error: {e}]"


def _generate_openai(prompt: str, cfg: ModelConfig, stream_callback=None) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "[OpenAI error: OPENAI_API_KEY not set]"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = []
    if cfg.system_prompt:
        messages.append({"role": "system", "content": cfg.system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": cfg.model,
        "messages": messages,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
    }
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=120,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        if stream_callback:
            stream_callback(text)
        return text
    except Exception as e:
        return f"[OpenAI error: {e}]"


def _generate_gemini(prompt: str, cfg: ModelConfig, stream_callback=None) -> str:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return "[Gemini error: GOOGLE_API_KEY not set]"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.model}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": cfg.temperature,
            "maxOutputTokens": cfg.max_tokens,
        },
    }
    if cfg.system_prompt:
        body["systemInstruction"] = {"parts": [{"text": cfg.system_prompt}]}

    try:
        r = requests.post(url, json=body, timeout=120)
        r.raise_for_status()
        candidates = r.json().get("candidates", [])
        text = candidates[0]["content"]["parts"][0]["text"] if candidates else ""
        if stream_callback:
            stream_callback(text)
        return text
    except Exception as e:
        return f"[Gemini error: {e}]"
