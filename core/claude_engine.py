"""Claude API wrapper for Module D (CodeLens suite)."""

from dataclasses import dataclass

import anthropic

from core.settings import get_anthropic_api_key

DEFAULT_MODEL = "claude-sonnet-4-20250514"


@dataclass
class ClaudeConfig:
    model: str = DEFAULT_MODEL
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str = ""


def _get_client() -> anthropic.Anthropic:
    api_key = get_anthropic_api_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set. Add it to your .env file.")
    return anthropic.Anthropic(api_key=api_key)


def generate(prompt: str, config: ClaudeConfig | None = None, stream_callback=None) -> str:
    """Generate text using Claude API."""
    cfg = config or ClaudeConfig()
    client = _get_client()

    messages = [{"role": "user", "content": prompt}]
    kwargs = {
        "model": cfg.model,
        "max_tokens": cfg.max_tokens,
        "messages": messages,
        "temperature": cfg.temperature,
    }
    if cfg.system_prompt:
        kwargs["system"] = cfg.system_prompt

    if stream_callback:
        full = []
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                full.append(text)
                stream_callback("".join(full))
        return "".join(full)
    else:
        response = client.messages.create(**kwargs)
        return response.content[0].text


def chat(messages: list[dict], config: ClaudeConfig | None = None, stream_callback=None) -> str:
    """Chat completion using Claude API."""
    cfg = config or ClaudeConfig()
    client = _get_client()

    kwargs = {
        "model": cfg.model,
        "max_tokens": cfg.max_tokens,
        "messages": messages,
        "temperature": cfg.temperature,
    }
    if cfg.system_prompt:
        kwargs["system"] = cfg.system_prompt

    if stream_callback:
        full = []
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                full.append(text)
                stream_callback("".join(full))
        return "".join(full)
    else:
        response = client.messages.create(**kwargs)
        return response.content[0].text
