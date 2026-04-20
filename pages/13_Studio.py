"""Studio — One-click study artifacts (flashcards, guides, timelines) via CAG."""

import streamlit as st

from core import cag_engine, gemma_engine
from core.page_state import ensure_state, set_result
from core.utils import extract_pdf_text, truncate_text
from core.obsidian_export import export_flashcards, export_study_guide
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="Studio", page_icon="🎨", layout="wide")
inject_global_css()
model_config = render_sidebar("studio")

page_header("🎨", "Studio — One-Click Study Artifacts", "Generate flashcards, study guides, and summaries from your documents. Export to Obsidian.", badge="Create")

ensure_state(
    studio_context="",
    studio_flashcards=None,
    studio_guide="",
    studio_summary="",
)

# --- Input ---
input_method = st.radio("Content source", ["Paste text", "Upload PDF"], horizontal=True)

if input_method == "Paste text":
    text = st.text_area("Paste your study material", height=200)
    if text:
        set_result("studio_context", text)
else:
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded:
        with st.spinner("Extracting..."):
            set_result("studio_context", extract_pdf_text(uploaded.read()))
        st.success(f"Extracted {len(st.session_state.studio_context):,} characters")

if not st.session_state.studio_context:
    st.info("Upload or paste content to generate study artifacts.")
    st.stop()


st.divider()

# --- Artifact buttons ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📇 Flashcards")
    num_cards = st.slider("Number of cards", 5, 30, 10)
    gen_cards = st.button("Generate Flashcards", type="primary")

with col2:
    st.markdown("### 📖 Study Guide")
    gen_guide = st.button("Generate Study Guide", type="primary")

with col3:
    st.markdown("### 📋 Summary")
    gen_summary = st.button("Generate Summary", type="primary")

context = truncate_text(st.session_state.studio_context, 25000)
config = gemma_engine.GemmaConfig(model=model_config.model)

# --- Flashcards ---
if gen_cards:
    with st.spinner("Generating flashcards..."):
        cards = cag_engine.generate_flashcards(context, num_cards=num_cards, config=config)

    if cards and "cards" in cards:
        set_result("studio_flashcards", cards)
    else:
        st.error("Failed to generate flashcards. Try again.")

# --- Study Guide ---
if gen_guide:
    placeholder = st.empty()
    with st.spinner("Generating study guide..."):
        guide = cag_engine.generate_study_guide(
            context, config=config,
            stream_callback=lambda t: placeholder.markdown(t),
        )
    if guide:
        placeholder.markdown(guide)
        set_result("studio_guide", guide)

# --- Summary ---
if gen_summary:
    placeholder = st.empty()
    with st.spinner("Generating summary..."):
        summary = cag_engine.generate_from_context(
            context,
            "Create a concise but comprehensive summary of the provided content. Use bullet points for key facts, bold for important terms, and organize by topic.",
            "You are an expert summarizer. Be thorough but concise.",
            config=config,
            stream_callback=lambda t: placeholder.markdown(t),
        )
    if summary:
        placeholder.markdown(summary)
        set_result("studio_summary", summary)

if st.session_state.studio_flashcards:
    cards = st.session_state.studio_flashcards
    st.divider()
    st.markdown(f"## {cards.get('title', 'Flashcards')}")
    for i, card in enumerate(cards["cards"], 1):
        with st.expander(f"Card {i}: {card['front'][:60]}"):
            st.markdown(f"**Front:** {card['front']}")
            st.markdown(f"**Back:** {card['back']}")
            if card.get("tags"):
                st.caption(f"Tags: {', '.join(card['tags'])}")
    if st.button("Export Flashcards to Obsidian"):
        path = export_flashcards(cards.get("title", "Flashcards"), cards["cards"], tags=["studio", "flashcards"])
        st.success(f"Exported to: {path}")

if st.session_state.studio_guide:
    st.divider()
    st.markdown("## Study Guide")
    st.markdown(st.session_state.studio_guide)
    col_a, col_b = st.columns(2)
    if col_a.button("Export Guide to Obsidian"):
        path = export_study_guide("Study Guide", st.session_state.studio_guide, tags=["studio", "study-guide"])
        st.success(f"Exported to: {path}")
    col_b.download_button("Download .md", data=st.session_state.studio_guide, file_name="study_guide.md", mime="text/markdown")

if st.session_state.studio_summary:
    st.divider()
    st.markdown("## Summary")
    st.markdown(st.session_state.studio_summary)
    if st.button("Export Summary to Obsidian"):
        path = export_study_guide("Summary", st.session_state.studio_summary, tags=["studio", "summary"])
        st.success(f"Exported to: {path}")
    st.download_button(
        "Download Summary",
        data=st.session_state.studio_summary,
        file_name="studio_summary.md",
        mime="text/markdown",
    )
