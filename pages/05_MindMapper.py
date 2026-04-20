"""MindMapper — Concept maps from text/PDF via Gemma 4 + Mermaid.js."""

import streamlit as st
import streamlit.components.v1 as components

from core import gemma_engine
from core.mermaid_utils import build_mermaid_html, extract_mermaid_code
from core.page_state import ensure_state, set_result
from core.utils import extract_pdf_text, truncate_text
from core.obsidian_export import export_mind_map
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="MindMapper", page_icon="🗺️", layout="wide")
inject_global_css()
model_config = render_sidebar("mindmapper")

page_header("🗺️", "MindMapper — Interactive Concept Maps", "Transform content into visual mind maps with Gemma 4 + Mermaid.js. Exports to Obsidian.", badge="Visual")

ensure_state(mindmapper_code="", mindmapper_title="")

input_method = st.radio("Input", ["Paste text", "Upload PDF"], horizontal=True)
context = ""
if input_method == "Paste text":
    context = st.text_area("Paste content", height=200)
else:
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded:
        context = extract_pdf_text(uploaded.read())
        st.success(f"Extracted {len(context):,} chars")

map_type = st.selectbox("Map type", ["mindmap", "flowchart TD", "flowchart LR", "graph TD"])
title = st.text_input("Title", placeholder="e.g. Cell Biology Concepts")

if st.button("Generate Mind Map", type="primary") and context:
    prompt = f"""Analyze the following content and create a Mermaid.js {map_type} diagram that captures the key concepts and their relationships.

STRICT SYNTAX RULES:
- First line must be exactly: {map_type}
- Node IDs: simple alphanumeric only (e.g. A, concept1, topicX) — NO spaces or special chars in IDs
- Node labels in square brackets: A[Photosynthesis]
- Edge labels with pipes: A -->|produces| B
- Do NOT put parentheses, colons, or quotes inside node labels
- Do NOT use markdown formatting (no **, #, _)
- Maximum 25 nodes for readability
- Output ONLY the Mermaid code. No explanation, no markdown fences.

Content:
{truncate_text(context, 15000)}"""

    config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.4)
    with st.spinner("Generating mind map..."):
        result = gemma_engine.generate(prompt, config)

    if result.startswith("[") and "error" in result.lower():
        st.error(result)
    else:
        set_result("mindmapper_code", extract_mermaid_code(result, fallback_prefix=map_type))
        set_result("mindmapper_title", title or "Mind Map")

if st.session_state.mindmapper_code:
    st.code(st.session_state.mindmapper_code, language="mermaid")
    components.html(build_mermaid_html(st.session_state.mindmapper_code), height=600, scrolling=True)
    col1, col2 = st.columns(2)
    if col1.button("Export to Obsidian"):
        path = export_mind_map(st.session_state.mindmapper_title, st.session_state.mindmapper_code, tags=["mindmapper"])
        st.success(f"Exported to: {path}")
    col2.download_button(
        "Download .md",
        data=f"```mermaid\n{st.session_state.mindmapper_code}\n```",
        file_name="mindmap.md",
        mime="text/markdown",
    )
