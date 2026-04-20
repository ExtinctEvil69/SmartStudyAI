"""SmartStudy AI — homepage."""

import streamlit as st

from core.ui_components import (
    inject_global_css,
    feature_cards,
    kpi_row,
    page_header,
    section_header,
)
from core.sidebar import render_sidebar

st.set_page_config(
    page_title="SmartStudy AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
config = render_sidebar("home")

# ── Hero ──────────────────────────────────────────────────────────────────

page_header(
    "🎓",
    "SmartStudy AI",
    "21-tool learning platform powered by Gemma 4. Turns raw inputs into grounded answers, quizzes, study plans, flashcards, diagrams, and Obsidian exports — with Vidya Smriti cross-tool memory.",
    badge="Gemma 4 Good",
)

kpi_row([
    {"label": "Core Model", "value": "Gemma 4"},
    {"label": "Grounding", "value": "LightRAG"},
    {"label": "Tools", "value": "21 Pages"},
    {"label": "Export", "value": "Obsidian"},
])

# ── Tabs ──────────────────────────────────────────────────────────────────

overview_tab, demo_tab, architecture_tab, status_tab = st.tabs([
    "Overview",
    "Judge Demo",
    "Architecture",
    "Build Status",
])

with overview_tab:
    section_header("Why this project matters", "💡")
    st.markdown(
        "Learners deal with fragmented inputs — PDFs, lecture notes, YouTube videos, podcasts, "
        "research papers, and code.  SmartStudy AI unifies those into a single Gemma-powered workflow "
        "that keeps everything local, private, and grounded."
    )

    section_header("Core capabilities", "⚡")

    feature_cards([
        {
            "icon": "📖",
            "title": "Grounded Learning",
            "desc": "Document Q&A with LightRAG knowledge graph. Source-aware web synthesis. Citation-backed research analysis.",
        },
        {
            "icon": "🧠",
            "title": "Adaptive Assessment",
            "desc": "Quizzes with Bloom's taxonomy coverage, difficulty mixing, and explanation quality — powered by the fine-tuned reward model.",
        },
        {
            "icon": "🎨",
            "title": "Study Artifact Factory",
            "desc": "Flashcards, study plans, mind maps, summaries, and audio narration — one-click generation from any content source.",
        },
        {
            "icon": "📊",
            "title": "Interactive Graphing",
            "desc": "Desmos-powered 2D equation lab with implicit curve support, Plotly 3D surfaces, physics templates, calculus tools.",
        },
        {
            "icon": "🔀",
            "title": "Code Intelligence",
            "desc": "Code explanation, debugging, flowcharts, architecture diagrams, and documentation generation.",
        },
        {
            "icon": "🔗",
            "title": "Multi-Source Synthesis",
            "desc": "Upload multiple documents, preserve source labels, and get cross-referenced synthesis with inline citations.",
        },
        {
            "icon": "🧬",
            "title": "Vidya Smriti — Learning Memory",
            "desc": "Persistent cross-tool memory layer. Tracks mastery, study streaks, activity timelines, and delivers personalized recommendations.",
        },
    ])

with demo_tab:
    section_header("Recommended judge walkthrough", "🎯")

    steps = [
        ("1", "NetSeek", "Live web research — DuckDuckGo search, page scraping, and source-aware Gemma synthesis."),
        ("2", "EduTube", "Paste a YouTube URL, auto-fetch the transcript, generate study notes or flashcards."),
        ("3", "NeuroRead", "Upload PDFs, build a LightRAG knowledge graph, ask grounded questions with references."),
        ("4", "QuizVerse", "Generate an adaptive quiz from the same content — closing the learn → test loop."),
        ("5", "AudioOverview", "Generate a podcast-style audio explanation and export MP3 via gTTS."),
        ("6", "MultiSourceSynth", "Upload multiple sources, produce cited cross-document synthesis."),
        ("7", "CodeFlow + LogicTrace", "CodeLens suite — flowcharts, debug triage, execution tracing."),
    ]

    for num, name, desc in steps:
        st.markdown(
            f"""<div class="glass-card" style="display:flex;gap:18px;align-items:flex-start;padding:20px 24px;">
    <div style="background:linear-gradient(135deg,#7C6CFF,#5A4BD6);color:#fff;font-weight:700;
                width:34px;height:34px;border-radius:10px;display:flex;align-items:center;
                justify-content:center;flex-shrink:0;font-size:0.85rem;
                box-shadow:0 2px 8px rgba(124,108,255,0.25);">{num}</div>
    <div>
        <strong style="color:#B4ADFF;font-size:0.95rem;">{name}</strong>
        <p style="color:#6B6B82;margin:4px 0 0 0;font-size:0.85rem;line-height:1.5;">{desc}</p>
    </div>
</div>""",
            unsafe_allow_html=True,
        )

    st.success("Best demo path: **search → ingest → ground → teach → quiz → summarize → explain**.")

with architecture_tab:
    section_header("System architecture", "🏗️")

    feature_cards([
        {
            "icon": "🔮",
            "title": "Inference Layer",
            "desc": "Ollama-backed Gemma for local generation. Multi-provider routing for Claude, OpenAI, and Gemini.",
        },
        {
            "icon": "🔍",
            "title": "Retrieval Layer",
            "desc": "LightRAG server for graph-based document grounding. Session-scoped workspaces. Reference-aware queries.",
        },
        {
            "icon": "🖥️",
            "title": "Presentation Layer",
            "desc": "Streamlit multi-page UI. Mermaid diagrams. Desmos graphing. Obsidian export. gTTS audio.",
        },
    ])

    section_header("Fine-tuning pipeline", "🔧")
    st.markdown(
        "The repository includes a **3-stage fine-tuning pipeline** under `fine_tuning/`:\n\n"
        "1. **SFT + rsLoRA** — teach Gemma structured JSON output format\n"
        "2. **GRPO** — multi-dimensional reward model for quiz quality\n"
        "3. **SimPO** — self-play preference optimization for taste\n\n"
        "Plus evaluation, dataset preparation, and GGUF export for Ollama deployment."
    )

with status_tab:
    section_header("Current build status", "📋")

    col_done, col_next = st.columns(2)
    with col_done:
        st.markdown("#### Working now")
        items = [
            "Env-driven Ollama + LightRAG config",
            "Session-scoped LightRAG workspaces",
            "Source-aware NetSeek research",
            "YouTube transcript ingestion",
            "Persistent outputs across all pages",
            "MP3 narration in AudioOverview",
            "Desmos + Plotly graphing in GraphiQ",
            "Implicit equation support (heart curves, circles)",
            "Mermaid-based CodeLens suite",
            "Obsidian export across all tools",
            "Multi-provider model routing",
        ]
        for item in items:
            st.markdown(f"- {item}")

    with col_next:
        st.markdown("#### Highest-value next steps")
        items = [
            "Run fine-tuning notebook on Kaggle T4",
            "Richer citation rendering in RAG pages",
            "Packaged startup script for judges",
            "Screenshots and demo assets in README",
        ]
        for item in items:
            st.markdown(f"- {item}")

st.divider()
st.caption(
    "Open the sidebar and follow the Judge Demo path.  "
    "If LightRAG is offline, the Gemma-first pages still work."
)
