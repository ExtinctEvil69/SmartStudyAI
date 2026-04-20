"""WriteWise — AI Writing Assistant (Gemma 4)."""

import streamlit as st

from core import gemma_engine
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="WriteWise", page_icon="✍️", layout="wide")
inject_global_css()
model_config = render_sidebar("writewise")

page_header("✍️", "WriteWise — AI Writing Assistant", "Get help with essays, reports, emails, and academic writing — powered by Gemma 4.", badge="Writing")

ensure_state(
    writewise_write_result="",
    writewise_improve_result="",
    writewise_feedback_result="",
)

# --- Input ---
tab_write, tab_improve, tab_feedback = st.tabs(["Write New", "Improve Existing", "Get Feedback"])

with tab_write:
    col1, col2 = st.columns([2, 1])
    with col1:
        writing_prompt = st.text_area("What do you want to write?", height=120,
                                       placeholder="e.g. A 500-word essay on the impact of AI on healthcare")
    with col2:
        writing_type = st.selectbox("Type", [
            "Essay", "Report", "Email", "Research abstract", "Blog post",
            "Cover letter", "Literature review", "Lab report", "Thesis outline",
        ])
        tone = st.selectbox("Tone", ["Academic", "Professional", "Casual", "Persuasive", "Informative"])
        word_count = st.slider("Target word count", 100, 3000, 500, step=100)

    if st.button("Generate Draft", type="primary", key="write") and writing_prompt.strip():
        prompt = f"""Write a {writing_type.lower()} with the following specifications:

**Topic/Prompt:** {writing_prompt}
**Tone:** {tone}
**Target length:** ~{word_count} words

Requirements:
- Clear structure with introduction, body, and conclusion
- Strong topic sentences for each paragraph
- Smooth transitions between ideas
- {'Formal academic language with proper citations style' if tone == 'Academic' else f'{tone} language appropriate for the format'}

Write the complete {writing_type.lower()} now."""

        config = gemma_engine.GemmaConfig(temperature=0.7, max_tokens=word_count * 3)
        config.system_prompt = f"You are an expert {tone.lower()} writer specializing in {writing_type.lower()}s."

        placeholder = st.empty()
        with st.spinner("Writing..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("writewise_write_result", result)

    if st.session_state.writewise_write_result:
        st.markdown(st.session_state.writewise_write_result)

with tab_improve:
    existing_text = st.text_area("Paste your text to improve", height=250)
    improve_focus = st.multiselect("Focus areas", [
        "Grammar & spelling", "Clarity & conciseness", "Stronger vocabulary",
        "Better transitions", "Academic tone", "Structure & flow", "Argument strength",
    ], default=["Clarity & conciseness", "Grammar & spelling"])

    if st.button("Improve Text", type="primary", key="improve") and existing_text.strip():
        prompt = f"""Improve the following text. Focus on: {', '.join(improve_focus)}.

**Original text:**
{existing_text}

Provide the improved version first, then a brief list of key changes made."""

        config = gemma_engine.GemmaConfig(temperature=0.4, max_tokens=len(existing_text) * 2)
        config.system_prompt = "You are a professional editor. Improve text while preserving the author's voice and intent."

        placeholder = st.empty()
        with st.spinner("Improving text..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("writewise_improve_result", result)

    if st.session_state.writewise_improve_result:
        st.markdown(st.session_state.writewise_improve_result)

with tab_feedback:
    review_text = st.text_area("Paste your text for feedback", height=250)
    rubric = st.selectbox("Evaluation rubric", [
        "General writing quality", "Academic essay rubric", "Professional communication",
        "Creative writing", "Technical writing",
    ])

    if st.button("Get Feedback", type="primary", key="feedback") and review_text.strip():
        prompt = f"""Evaluate the following text using a {rubric.lower()} rubric.

**Text to evaluate:**
{review_text}

Provide:
1. **Overall Assessment** (1-2 sentences)
2. **Strengths** (bullet points)
3. **Areas for Improvement** (bullet points with specific suggestions)
4. **Score** (out of 10, with brief justification)
5. **Priority Actions** (top 3 things to fix first)"""

        config = gemma_engine.GemmaConfig(temperature=0.3, max_tokens=2000)
        config.system_prompt = "You are an experienced writing instructor. Give constructive, specific, actionable feedback."

        placeholder = st.empty()
        with st.spinner("Analyzing your writing..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)
        set_result("writewise_feedback_result", result)

    if st.session_state.writewise_feedback_result:
        st.markdown(st.session_state.writewise_feedback_result)

# Export — show for whichever tab has a result
any_result = (
    st.session_state.writewise_write_result
    or st.session_state.writewise_improve_result
    or st.session_state.writewise_feedback_result
)
if any_result:
    st.divider()
    col_export, col_download = st.columns(2)
    latest = (
        st.session_state.writewise_write_result
        or st.session_state.writewise_improve_result
        or st.session_state.writewise_feedback_result
    )
    if col_export.button("Export to Obsidian"):
        path = export_study_guide(
            "WriteWise Output",
            latest,
            tags=["writewise", "writing"],
        )
        st.success(f"Exported to: {path}")
    col_download.download_button(
        "Download Markdown",
        data=latest,
        file_name="writewise_output.md",
        mime="text/markdown",
    )
