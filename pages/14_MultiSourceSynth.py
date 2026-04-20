"""MultiSourceSynth — source-aware multi-document synthesis."""

import streamlit as st

from core import gemma_engine, cag_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.utils import extract_pdf_text, truncate_text
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="MultiSourceSynth", page_icon="🔗", layout="wide")
inject_global_css()
model_config = render_sidebar("multisource")

page_header("🔗", "MultiSourceSynth — Multi-Document Synthesis", "Upload multiple sources, preserve source labels, and generate grounded synthesis notes.", badge="Synthesis")

ensure_state(
    synth_documents={},
    synth_result="",
    synth_analysis_type="",
    synth_focus_question="",
)

st.subheader("Upload Documents")
uploaded_files = st.file_uploader("Upload PDFs or text files", type=["pdf", "txt"], accept_multiple_files=True)

if uploaded_files:
    for uploaded in uploaded_files:
        if uploaded.name not in st.session_state.synth_documents:
            with st.spinner(f"Processing {uploaded.name}..."):
                if uploaded.name.endswith(".pdf"):
                    text = extract_pdf_text(uploaded.read())
                else:
                    text = uploaded.read().decode("utf-8", errors="replace")
            st.session_state.synth_documents[uploaded.name] = text
            st.success(f"Loaded: {uploaded.name} ({len(text):,} chars)")

with st.expander("Or paste text sources"):
    for index in range(1, 4):
        source_col, text_col = st.columns([1, 3])
        with source_col:
            source_name = st.text_input(f"Source {index} name", key=f"src_name_{index}", placeholder=f"Source {index}")
        with text_col:
            source_text = st.text_area(f"Source {index} text", key=f"src_text_{index}", height=100)
        if source_name and source_text:
            st.session_state.synth_documents[source_name] = source_text

if st.session_state.synth_documents:
    st.markdown(f"**{len(st.session_state.synth_documents)} documents loaded:**")
    for name, text in st.session_state.synth_documents.items():
        st.markdown(f"- **{name}** — {len(text):,} characters")
    st.divider()

    analysis_col, focus_col = st.columns(2)
    with analysis_col:
        analysis_type = st.selectbox(
            "Analysis type",
            [
                "Cross-document summary",
                "Compare & contrast",
                "Find agreements & contradictions",
                "Thematic analysis",
                "Literature review synthesis",
                "Timeline / chronological analysis",
            ],
        )
    with focus_col:
        focus_question = st.text_input("Focus question (optional)", placeholder="e.g. How do these sources differ on climate policy?")


    if st.button("Synthesize", type="primary"):
        source_blocks = []
        source_catalog = []
        for index, (name, text) in enumerate(st.session_state.synth_documents.items(), start=1):
            source_id = f"Source {index}"
            excerpt = truncate_text(text, 7000)
            source_catalog.append({"source_id": source_id, "name": name, "chars": len(text)})
            source_blocks.append(f"[{source_id}] {name}\n{excerpt}")

        combined_context = "\n\n".join(source_blocks)

        instructions = {
            "Cross-document summary": "Create a unified summary with an overview, shared themes, unique contributions, and source-specific citations.",
            "Compare & contrast": "Compare where the sources agree, differ, and emphasize different trade-offs. Cite each comparison with [Source X].",
            "Find agreements & contradictions": "List claims supported by multiple sources, contradictions, and areas that need more evidence. Cite each claim with [Source X].",
            "Thematic analysis": "Identify major themes, explain how each source contributes to each theme, and cite each point with [Source X].",
            "Literature review synthesis": "Write a literature-review style synthesis with field overview, methods, findings, debates, and research gaps. Cite each section with [Source X].",
            "Timeline / chronological analysis": "Reconstruct the timeline, turning points, and current state from the sources. Cite each step with [Source X].",
        }

        instruction = instructions[analysis_type]
        if focus_question:
            instruction = f"Focus question: {focus_question}\n\n{instruction}"

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=6000)
        placeholder = st.empty()
        with st.spinner(f"Synthesizing {len(source_catalog)} sources..."):
            result = cag_engine.generate_from_context(
                combined_context,
                instruction,
                system_prompt=(
                    "You are an expert research analyst. Only use the provided sources, cite with [Source X], "
                    "and call out unresolved contradictions clearly."
                ),
                config=config,
                stream_callback=lambda text: placeholder.markdown(text),
            )
        placeholder.markdown(result)
        set_result("synth_result", result)
        set_result("synth_analysis_type", analysis_type)
        set_result("synth_focus_question", focus_question)

if st.session_state.synth_result:
    st.divider()
    st.subheader(st.session_state.synth_analysis_type)
    if st.session_state.synth_focus_question:
        st.caption(f"Focus question: {st.session_state.synth_focus_question}")
    st.markdown(st.session_state.synth_result)

    with st.expander("Source Index", expanded=True):
        for index, (name, text) in enumerate(st.session_state.synth_documents.items(), start=1):
            st.markdown(f"**Source {index}**: {name}")
            st.caption(f"{len(text):,} characters")

    col_export, col_download = st.columns(2)
    if col_export.button("Export to Obsidian"):
        sources_str = "\n".join(f"- Source {i}: {name}" for i, name in enumerate(st.session_state.synth_documents.keys(), start=1))
        path = export_study_guide(
            f"Synthesis - {st.session_state.synth_analysis_type}",
            f"## Sources\n{sources_str}\n\n{st.session_state.synth_result}",
            tags=["multi-source", st.session_state.synth_analysis_type.lower().replace(" ", "-")],
        )
        st.success(f"Exported to: {path}")
    col_download.download_button(
        "Download Markdown",
        data=st.session_state.synth_result,
        file_name="multi_source_synthesis.md",
        mime="text/markdown",
    )
