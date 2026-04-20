"""NetSeek — Web research API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.gemma_engine import GemmaConfig, generate
from core.web_research import search_web, build_research_context
from brahmavidya.memory import log_event

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    depth: str = "Quick overview"
    output_format: str = "Summary"
    max_results: int = 5
    additional_context: str = ""


class SearchResponse(BaseModel):
    result: str
    sources: list[dict]
    query: str


DEPTH_INSTRUCTIONS = {
    "Quick overview": "Provide a concise 3-5 paragraph overview.",
    "Detailed analysis": "Provide a detailed analysis with sections for background, key findings, current state, and future directions.",
    "Comprehensive report": "Write a comprehensive report with an executive summary, analysis sections, implications, and further reading.",
}

FORMAT_INSTRUCTIONS = {
    "Summary": "Write in flowing prose with clear topic sentences.",
    "Bullet points": "Use bullet points with bold key terms.",
    "Academic style": "Write in academic style and cite sources using [Source X].",
    "ELI5": "Explain like I'm 5 using simple analogies and short sentences.",
}


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    raw_results = search_web(req.query, max_results=req.max_results)
    if not raw_results:
        return SearchResponse(result="No search results found. Try a different query.", sources=[], query=req.query)

    research_context, enriched_sources = build_research_context(raw_results)

    prompt = f"""You are a meticulous research assistant. Use only the supplied search results and fetched page excerpts.

Research topic: {req.query}
Additional context: {req.additional_context or 'None provided'}

Instructions:
- {DEPTH_INSTRUCTIONS.get(req.depth, DEPTH_INSTRUCTIONS['Quick overview'])}
- {FORMAT_INSTRUCTIONS.get(req.output_format, FORMAT_INSTRUCTIONS['Summary'])}
- Distinguish established facts from uncertainty or conflicting claims.
- Cite factual claims inline using [Source X].
- End with a short section called `Source Notes` listing the most useful sources.

Available sources:
{research_context}
"""

    config = GemmaConfig(temperature=0.4, max_tokens=5000)
    config.system_prompt = "You synthesize web research faithfully and never invent sources."
    result = generate(prompt, config)

    log_event("NetSeek", "search_performed", req.query[:80], depth=req.depth, sources=len(enriched_sources))

    sources_clean = [
        {"title": s["title"], "url": s["url"], "snippet": s["snippet"], "source_id": s["source_id"]}
        for s in enriched_sources
    ]
    return SearchResponse(result=result, sources=sources_clean, query=req.query)
