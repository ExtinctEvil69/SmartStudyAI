"""NetSeek — AI web research assistant with live search."""

import streamlit as st

from core import gemma_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header
from core.web_research import build_research_context, search_web
from core.vidya_smriti import log_event

st.set_page_config(page_title="NetSeek", page_icon="🔍", layout="wide")
inject_global_css()
model_config = render_sidebar("netseek")

page_header("🔍", "NetSeek", "Search the web, synthesize the results, and keep the source trail visible.", badge="Research")

ensure_state(
    netseek_history=[],
    netseek_result="",
    netseek_sources=[],
    netseek_query="",
    netseek_error="",
)

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input("Research query", placeholder="e.g. Recent advances in CRISPR gene editing")
    additional_context = st.text_area(
        "Additional context (optional)",
        height=80,
        placeholder="e.g. Focus on therapeutic applications in 2024-2025",
    )

with col2:
    depth = st.selectbox("Research depth", ["Quick overview", "Detailed analysis", "Comprehensive report"])
    output_format = st.selectbox("Output format", ["Summary", "Bullet points", "Academic style", "ELI5"])
    max_results = st.slider("Web results", 3, 10, 5)

depth_instructions = {
    "Quick overview": "Provide a concise 3-5 paragraph overview.",
    "Detailed analysis": "Provide a detailed analysis with sections for background, key findings, current state, and future directions.",
    "Comprehensive report": "Write a comprehensive report with an executive summary, analysis sections, implications, and further reading.",
}

format_instructions = {
    "Summary": "Write in flowing prose with clear topic sentences.",
    "Bullet points": "Use bullet points with bold key terms.",
    "Academic style": "Write in academic style and cite sources using [Source X].",
    "ELI5": "Explain like I'm 5 using simple analogies and short sentences.",
}

if st.button("Research", type="primary") and query.strip():
    try:
        with st.spinner("Searching the web..."):
            raw_results = search_web(query, max_results=max_results)
        if not raw_results:
            raise ValueError("No search results found. Try a different query.")

        research_context, enriched_sources = build_research_context(raw_results)
        prompt = f"""You are a meticulous research assistant. Use only the supplied search results and fetched page excerpts.

Research topic: {query}
Additional context: {additional_context or 'None provided'}

Instructions:
- {depth_instructions[depth]}
- {format_instructions[output_format]}
- Distinguish established facts from uncertainty or conflicting claims.
- Cite factual claims inline using [Source X].
- End with a short section called `Source Notes` listing the most useful sources.

Available sources:
{research_context}
"""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4, max_tokens=5000)
        config.system_prompt = "You synthesize web research faithfully and never invent sources."

        placeholder = st.empty()
        with st.spinner("Synthesizing sources..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda text: placeholder.markdown(text))
        placeholder.markdown(result)

        set_result("netseek_query", query)
        set_result("netseek_result", result)
        set_result("netseek_sources", enriched_sources)
        set_result("netseek_error", "")
        st.session_state.netseek_history.append({"query": query, "result": result, "depth": depth})
        # ── Vidya Smriti: log research ──
        log_event("NetSeek", "search_performed", query[:80], depth=depth, sources=len(enriched_sources))
    except Exception as exc:
        set_result("netseek_error", str(exc))

if st.session_state.netseek_error:
    st.error(st.session_state.netseek_error)

if st.session_state.netseek_result:
    st.divider()
    st.subheader(f"Research Brief: {st.session_state.netseek_query}")
    st.markdown(st.session_state.netseek_result)

    if st.session_state.netseek_sources:
        with st.expander("Sources", expanded=True):
            for source in st.session_state.netseek_sources:
                st.markdown(f"**{source['source_id']}**: [{source['title']}]({source['url']})")
                if source["snippet"]:
                    st.caption(source["snippet"])
                if source.get("fetch_error"):
                    st.caption(f"Full page fetch skipped: {source['fetch_error']}")

    col_export, col_download = st.columns(2)
    if col_export.button("Export to Obsidian"):
        sources_md = "\n".join(
            f"- [{source['title']}]({source['url']})" for source in st.session_state.netseek_sources
        )
        path = export_study_guide(
            f"NetSeek - {st.session_state.netseek_query[:50]}",
            f"## Query\n{st.session_state.netseek_query}\n\n{st.session_state.netseek_result}\n\n## Sources\n{sources_md}",
            tags=["netseek", "research"],
        )
        st.success(f"Exported to: {path}")
    col_download.download_button(
        "Download Markdown",
        data=st.session_state.netseek_result,
        file_name="netseek_research.md",
        mime="text/markdown",
    )

if st.session_state.netseek_history:
    st.divider()
    with st.expander("Research History", expanded=False):
        for item in reversed(st.session_state.netseek_history):
            st.markdown(f"**{item['query']}** ({item['depth']})")
            st.markdown(item["result"][:300] + "...")
            st.divider()
