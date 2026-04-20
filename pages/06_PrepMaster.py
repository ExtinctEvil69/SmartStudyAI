"""PrepMaster — AI Study Plan Generator (CAG)."""

import streamlit as st

from core import cag_engine, gemma_engine
from core.page_state import ensure_state, set_result
from core.utils import extract_pdf_text, truncate_text
from core.obsidian_export import export_study_plan
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header

st.set_page_config(page_title="PrepMaster", page_icon="📝", layout="wide")
inject_global_css()
model_config = render_sidebar("prepmaster")

page_header("📝", "PrepMaster — AI Study Plan Generator", "Generate personalized week-by-week study plans using Gemma 4 + CAG.", badge="Planning")

ensure_state(prepmaster_context="", prepmaster_plan="", prepmaster_goal="")

col_input, col_config = st.columns([2, 1])

with col_config:
    st.subheader("Plan Settings")
    goal = st.text_input("Learning goal", placeholder="e.g. Master organic chemistry for finals")
    duration = st.slider("Duration (weeks)", 1, 12, 4)
    hours = st.slider("Hours per week", 1, 40, 10)
    knowledge_level = st.selectbox("Current knowledge", ["Beginner", "Intermediate", "Advanced"])
    preferences = st.text_area("Study preferences (optional)", placeholder="e.g. I learn best through practice problems, prefer morning study sessions", height=80)


with col_input:
    input_method = st.radio("Content source", ["Paste syllabus/topics", "Upload PDF"], horizontal=True)

    if input_method == "Paste syllabus/topics":
        context = st.text_area("Paste your syllabus, topics, or learning materials", height=250)
        if context:
            set_result("prepmaster_context", context)
    else:
        uploaded = st.file_uploader("Upload course material PDF", type=["pdf"])
        if uploaded:
            with st.spinner("Extracting..."):
                context = extract_pdf_text(uploaded.read())
            set_result("prepmaster_context", context)
            st.success(f"Extracted {len(context):,} characters")

if st.button("Generate Study Plan", type="primary") and (st.session_state.prepmaster_context or goal):
    full_context = st.session_state.prepmaster_context or f"Learning goal: {goal}"
    if knowledge_level:
        full_context += f"\n\nCurrent knowledge level: {knowledge_level}"
    if preferences:
        full_context += f"\n\nStudy preferences: {preferences}"

    config = gemma_engine.GemmaConfig(model=model_config.model, max_tokens=8192)
    placeholder = st.empty()

    with st.spinner("Generating study plan..."):
        plan = cag_engine.generate_study_plan(
            context=truncate_text(full_context, 25000),
            goal=goal,
            duration_weeks=duration,
            hours_per_week=hours,
            config=config,
            stream_callback=lambda text: placeholder.markdown(text),
        )

    if plan:
        placeholder.markdown(plan)
        set_result("prepmaster_plan", plan)
        set_result("prepmaster_goal", goal)

if st.session_state.prepmaster_plan:
    st.divider()
    st.markdown(st.session_state.prepmaster_plan)
    col1, col2 = st.columns(2)
    if col1.button("Export to Obsidian"):
        path = export_study_plan(
            f"Study Plan - {st.session_state.prepmaster_goal[:50]}" if st.session_state.prepmaster_goal else "Study Plan",
            st.session_state.prepmaster_plan,
            tags=["prepmaster", "study-plan"],
        )
        st.success(f"Exported to: {path}")

    col2.download_button(
        "Download .md",
        data=st.session_state.prepmaster_plan,
        file_name="study_plan.md",
        mime="text/markdown",
    )
