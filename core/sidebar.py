"""Unified sidebar — branding, system status, model provider, navigation."""

import streamlit as st

from core import gemma_engine, lightrag_engine
from core.model_providers import PROVIDERS, _ollama_available, render_model_selector, ModelConfig
from core.settings import get_ollama_base, get_lightrag_base
from core.ui_components import stat_pill


def render_sidebar(tool_key: str = "global") -> ModelConfig:
    """Render the full SmartStudy sidebar.  Returns the selected ModelConfig."""
    with st.sidebar:
        # ── Brand mark ──
        st.markdown(
            """
<div style="text-align:center; padding:16px 0 8px 0;">
    <div style="
        width: 48px; height: 48px;
        background: linear-gradient(135deg, rgba(124,108,255,0.15) 0%, rgba(86,204,242,0.1) 100%);
        border: 1px solid rgba(124,108,255,0.2);
        border-radius: 14px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 8px;
    ">🎓</div>
    <h2 style="margin:0; font-size:1.2rem; font-weight:800;
               background:linear-gradient(135deg, #fff 0%, #B4ADFF 50%, #56CCF2 100%);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;
               background-clip:text; letter-spacing:-0.03em;">
        SmartStudy AI
    </h2>
    <p style="color:#6B6B82; font-size:0.68rem; margin:4px 0 0 0;
              letter-spacing:0.06em; text-transform:uppercase; font-weight:500;">
        Gemma-powered learning
    </p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── System health ──
        ollama_ok = _ollama_available()
        models = gemma_engine.list_models() if ollama_ok else []
        gemma_ok = any("gemma" in m.lower() for m in models)
        rag_ok = lightrag_engine.is_available()

        pills = [
            ("Ollama", "green" if ollama_ok else "red"),
            ("Gemma", "green" if gemma_ok else "amber"),
            ("LightRAG", "green" if rag_ok else "red"),
        ]
        html = "".join(stat_pill(l, s) for l, s in pills)
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-bottom:4px;">{html}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"`{get_ollama_base()}`  ·  `{get_lightrag_base()}`")

        st.divider()

        # ── Model selector ──
        st.markdown(
            "<p style='color:#6B6B82;font-size:0.68rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px;'>Model</p>",
            unsafe_allow_html=True,
        )
        config = render_model_selector(tool_key)

        st.divider()

        # ── Quick nav ──
        st.markdown(
            "<p style='color:#6B6B82;font-size:0.68rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px;'>Modules</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
<div style="font-size:0.78rem; line-height:2; color:#A0A0B8;">
<span style="color:#FF6B8A;font-weight:600;font-size:0.68rem;letter-spacing:0.04em;text-transform:uppercase;">Memory</span><br>
<span style="color:#6B6B82;">Vidya Smriti</span><br>
<span style="color:#B4ADFF;font-weight:600;font-size:0.68rem;letter-spacing:0.04em;text-transform:uppercase;margin-top:4px;display:inline-block;">Study</span><br>
<span style="color:#6B6B82;">NetSeek · NeuroRead · QuizVerse · EduTube · MindMapper · PrepMaster · PaperAnalyzer</span><br>
<span style="color:#56CCF2;font-weight:600;font-size:0.68rem;letter-spacing:0.04em;text-transform:uppercase;margin-top:4px;display:inline-block;">Create</span><br>
<span style="color:#6B6B82;">AudioOverview · Studio · MultiSourceSynth · GraphiQ · WriteWise</span><br>
<span style="color:#2DD4BF;font-weight:600;font-size:0.68rem;letter-spacing:0.04em;text-transform:uppercase;margin-top:4px;display:inline-block;">Build</span><br>
<span style="color:#6B6B82;">CodeBuddy · DSASage · IdeaSpark · FeatureForge</span><br>
<span style="color:#FFB84D;font-weight:600;font-size:0.68rem;letter-spacing:0.04em;text-transform:uppercase;margin-top:4px;display:inline-block;">Code</span><br>
<span style="color:#6B6B82;">CodeFlow · ArchViz · LogicTrace · DocGen</span>
</div>
""",
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Footer ──
        st.markdown(
            """
<div style="text-align:center; padding:4px 0;">
    <p style="color:#3D3D52; font-size:0.65rem; margin:0; line-height:1.6; letter-spacing:0.02em;">
        Built for Gemma 4 Good Hackathon<br>
        Kaggle × Google DeepMind
    </p>
</div>
""",
            unsafe_allow_html=True,
        )

    return config
