"""Runtime configuration helpers for SmartStudy AI."""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


TOOL_MODEL_ENV = {
    "general": "SMARTSTUDY_MODEL_GENERAL",
    "quizverse": "SMARTSTUDY_MODEL_QUIZVERSE",
    "prepmaster": "SMARTSTUDY_MODEL_PREPMASTER",
    "dsasage": "SMARTSTUDY_MODEL_DSASAGE",
    "studio": "SMARTSTUDY_MODEL_STUDIO",
    "docread": "SMARTSTUDY_MODEL_DOCREAD",
    "paperanalyzer": "SMARTSTUDY_MODEL_PAPERANALYZER",
    "codelens": "SMARTSTUDY_MODEL_CODELENS",
}


def _normalize_base_url(value: str | None, default: str) -> str:
    url = (value or default).strip().rstrip("/")
    if not url:
        return default
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"
    return url


def get_ollama_base() -> str:
    return _normalize_base_url(os.getenv("OLLAMA_HOST"), "http://localhost:11434")


def get_lightrag_base() -> str:
    return _normalize_base_url(os.getenv("LIGHTRAG_HOST"), "http://localhost:9621")


def get_anthropic_api_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def get_preferred_model(tool: str, available_models: list[str], fallback: str) -> str:
    if not available_models:
        return fallback

    env_keys = []
    tool_key = TOOL_MODEL_ENV.get(tool)
    if tool_key:
        env_keys.append(tool_key)
    env_keys.append(TOOL_MODEL_ENV["general"])

    requested_models = [os.getenv(key, "").strip() for key in env_keys if os.getenv(key, "").strip()]
    for requested in requested_models:
        for model in available_models:
            if model == requested:
                return model
        for model in available_models:
            if requested.lower() in model.lower():
                return model

    if fallback in available_models:
        return fallback
    return available_models[0]
