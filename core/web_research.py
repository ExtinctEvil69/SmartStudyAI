"""Lightweight web research helpers for NetSeek."""

from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

USER_AGENT = "SmartStudyAI/1.0 (+https://smartstudy.local)"


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": (item.get("title") or "Untitled result").strip(),
                    "url": (item.get("href") or "").strip(),
                    "snippet": (item.get("body") or "").strip(),
                }
            )
    return [item for item in results if item["url"]]


def fetch_page_text(url: str, timeout: int = 15, max_chars: int = 5000) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    paragraphs = [node.get_text(" ", strip=True) for node in soup.find_all(["p", "li", "h1", "h2", "h3"])]
    content = "\n".join(part for part in paragraphs if part)
    if title:
        content = f"{title}\n\n{content}"
    return content[:max_chars]


def build_research_context(results: list[dict[str, str]], max_full_pages: int = 3) -> tuple[str, list[dict[str, Any]]]:
    compiled: list[str] = []
    enriched: list[dict[str, Any]] = []

    for index, result in enumerate(results, start=1):
        full_text = ""
        error = ""
        if index <= max_full_pages:
            try:
                full_text = fetch_page_text(result["url"])
            except Exception as exc:  # pragma: no cover - network dependent
                error = str(exc)

        enriched_result = {
            **result,
            "full_text": full_text,
            "fetch_error": error,
            "source_id": f"Source {index}",
        }
        enriched.append(enriched_result)

        sections = [
            f"[{enriched_result['source_id']}] {result['title']}",
            f"URL: {result['url']}",
            f"Snippet: {result['snippet']}",
        ]
        if full_text:
            sections.append(f"Page text:\n{full_text}")
        compiled.append("\n".join(sections))

    return "\n\n".join(compiled), enriched
