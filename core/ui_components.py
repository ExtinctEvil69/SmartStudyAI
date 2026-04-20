"""SmartStudy AI — Premium UI component library.

Refined dark-mode design system with Inter + JetBrains Mono,
layered surfaces, subtle gradients, and micro-interactions.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
# Primary palette
ACCENT = "#7C6CFF"
ACCENT_LIGHT = "#B4ADFF"
ACCENT_DARK = "#5A4BD6"
ACCENT_GLOW = "rgba(124, 108, 255, 0.25)"

# Secondary accents
CYAN = "#56CCF2"
TEAL = "#2DD4BF"
CORAL = "#FF6B8A"
AMBER = "#FFB84D"

# Surfaces — 4-layer depth system
BG_BASE = "#08080D"
BG_RAISED = "#0E0E16"
SURFACE_1 = "#14141E"
SURFACE_2 = "#1A1A28"
SURFACE_3 = "#222233"
BORDER = "rgba(255, 255, 255, 0.06)"
BORDER_HOVER = "rgba(124, 108, 255, 0.2)"

# Text
TEXT_PRIMARY = "#F0EFF5"
TEXT_SECONDARY = "#A0A0B8"
TEXT_TERTIARY = "#6B6B82"

# Semantic
SUCCESS = "#34D399"
WARNING = "#FBBF24"
ERROR = "#F87171"

# Typography
FONT_BODY = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO = "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace"


def inject_global_css():
    """Inject once per page — call at the top of every page module."""
    st.markdown(
        f"""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Root overrides ── */
html, body, [class*="stApp"] {{
    font-family: {FONT_BODY} !important;
    background-color: {BG_BASE};
    color: {TEXT_PRIMARY};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header {{visibility: hidden;}}
.stDeployButton {{display: none;}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_RAISED} 0%, {SURFACE_1} 100%);
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {ACCENT_LIGHT};
    font-weight: 600;
    letter-spacing: -0.02em;
}}

/* ── Typography hierarchy ── */
h1 {{
    font-family: {FONT_BODY} !important;
    font-weight: 800 !important;
    letter-spacing: -0.035em !important;
    line-height: 1.1 !important;
    background: linear-gradient(135deg, #fff 0%, {ACCENT_LIGHT} 50%, {CYAN} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
h2 {{
    font-family: {FONT_BODY} !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: {TEXT_PRIMARY} !important;
    line-height: 1.2 !important;
}}
h3 {{
    font-family: {FONT_BODY} !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: {TEXT_SECONDARY} !important;
}}

/* ── Primary buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, {ACCENT} 0%, {ACCENT_DARK} 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.5rem !important;
    font-weight: 600 !important;
    font-family: {FONT_BODY} !important;
    font-size: 0.875rem !important;
    letter-spacing: -0.01em;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.3), 0 4px 16px {ACCENT_GLOW};
    position: relative;
    overflow: hidden;
}}
.stButton > button::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.12) 0%, transparent 50%);
    border-radius: inherit;
    pointer-events: none;
}}
.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.4), 0 8px 32px {ACCENT_GLOW};
    filter: brightness(1.06);
}}
.stButton > button:active {{
    transform: translateY(0);
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 2px 8px {ACCENT_GLOW};
}}

/* ── Download / secondary buttons ── */
.stDownloadButton > button {{
    background: rgba(124, 108, 255, 0.06) !important;
    border: 1px solid rgba(124, 108, 255, 0.15) !important;
    border-radius: 10px !important;
    color: {ACCENT_LIGHT} !important;
    font-weight: 500 !important;
    font-family: {FONT_BODY} !important;
    transition: all 0.2s ease;
}}
.stDownloadButton > button:hover {{
    border-color: rgba(124, 108, 255, 0.35) !important;
    background: rgba(124, 108, 255, 0.12) !important;
    box-shadow: 0 2px 12px rgba(124, 108, 255, 0.1);
}}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: {SURFACE_1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT_PRIMARY} !important;
    font-family: {FONT_BODY} !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT_GLOW} !important;
    background: {SURFACE_2} !important;
}}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {{
    color: {TEXT_TERTIARY} !important;
}}

/* ── Selectbox ── */
.stSelectbox > div > div {{
    background: {SURFACE_1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT_PRIMARY} !important;
    font-family: {FONT_BODY} !important;
}}

/* ── Sliders ── */
.stSlider > div > div > div > div {{
    background: {ACCENT} !important;
}}
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {{
    color: {TEXT_TERTIARY} !important;
    font-size: 0.75rem !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background: {SURFACE_1};
    border-radius: 12px;
    padding: 4px;
    border: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 9px !important;
    padding: 8px 20px !important;
    font-weight: 500 !important;
    font-family: {FONT_BODY} !important;
    font-size: 0.85rem !important;
    color: {TEXT_TERTIARY} !important;
    background: transparent !important;
    border: none !important;
    transition: all 0.2s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {TEXT_SECONDARY} !important;
    background: rgba(255,255,255,0.03) !important;
}}
.stTabs [aria-selected="true"] {{
    background: {ACCENT} !important;
    color: #fff !important;
    box-shadow: 0 2px 12px {ACCENT_GLOW};
    font-weight: 600 !important;
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

/* ── Expanders ── */
.streamlit-expanderHeader {{
    background: {SURFACE_1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s;
}}
.streamlit-expanderHeader:hover {{
    border-color: {BORDER_HOVER} !important;
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background: {SURFACE_1};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 20px 24px;
    transition: all 0.25s ease;
}}
[data-testid="stMetric"]:hover {{
    border-color: {BORDER_HOVER};
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}}
[data-testid="stMetricValue"] {{
    font-family: {FONT_BODY} !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, {TEXT_PRIMARY} 0%, {ACCENT_LIGHT} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
[data-testid="stMetricLabel"] {{
    color: {TEXT_TERTIARY} !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em;
}}

/* ── Code blocks ── */
code {{
    font-family: {FONT_MONO} !important;
    font-size: 0.85rem !important;
    background: {SURFACE_2} !important;
    padding: 2px 6px !important;
    border-radius: 5px !important;
    color: {ACCENT_LIGHT} !important;
}}
pre {{
    font-family: {FONT_MONO} !important;
    background: {SURFACE_1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    padding: 16px !important;
}}

/* ── Alerts ── */
.stAlert {{
    border-radius: 12px !important;
    border-left-width: 3px !important;
    font-size: 0.9rem !important;
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    background: {SURFACE_1};
    border: 1px dashed rgba(124, 108, 255, 0.2);
    border-radius: 14px;
    padding: 16px;
    transition: border-color 0.25s;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: rgba(124, 108, 255, 0.4);
}}

/* ── Glassmorphism cards ── */
.glass-card {{
    background: linear-gradient(145deg, rgba(20, 20, 30, 0.8) 0%, rgba(14, 14, 22, 0.9) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 14px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
.glass-card:hover {{
    border-color: {BORDER_HOVER};
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(124, 108, 255, 0.06);
    transform: translateY(-1px);
}}

/* ── Stat pills ── */
.stat-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: {SURFACE_1};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 4px 14px 4px 10px;
    font-size: 0.78rem;
    font-weight: 500;
    color: {TEXT_SECONDARY};
    font-family: {FONT_BODY};
    transition: all 0.2s;
}}
.stat-pill:hover {{
    border-color: {BORDER_HOVER};
    background: {SURFACE_2};
}}
.stat-pill .dot {{
    width: 7px; height: 7px; border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}}
.dot-green {{ background: {SUCCESS}; box-shadow: 0 0 8px rgba(52, 211, 153, 0.5); }}
.dot-red   {{ background: {ERROR};   box-shadow: 0 0 8px rgba(248, 113, 113, 0.5); }}
.dot-amber {{ background: {WARNING}; box-shadow: 0 0 8px rgba(251, 191, 36, 0.5); }}

/* ── Feature card grid ── */
.feature-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 14px;
    margin: 16px 0;
}}
.feature-card {{
    background: linear-gradient(145deg, {SURFACE_1} 0%, {BG_RAISED} 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 24px 26px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}}
.feature-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, {ACCENT_GLOW} 50%, transparent 100%);
    opacity: 0;
    transition: opacity 0.3s;
}}
.feature-card:hover {{
    border-color: {BORDER_HOVER};
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.35), 0 0 0 1px rgba(124, 108, 255, 0.08);
}}
.feature-card:hover::before {{
    opacity: 1;
}}
.feature-card .card-icon {{
    font-size: 1.5rem;
    margin-bottom: 12px;
    display: block;
}}
.feature-card h4 {{
    margin: 0 0 8px 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    letter-spacing: -0.01em;
}}
.feature-card p {{
    margin: 0;
    font-size: 0.84rem;
    color: {TEXT_TERTIARY};
    line-height: 1.6;
}}

/* ── Badge ── */
.badge {{
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, rgba(124, 108, 255, 0.12) 0%, rgba(86, 204, 242, 0.08) 100%);
    color: {ACCENT_LIGHT};
    font-size: 0.68rem;
    font-weight: 600;
    padding: 3px 12px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border: 1px solid rgba(124, 108, 255, 0.15);
}}

/* ── Divider ── */
hr {{
    border: none;
    border-top: 1px solid {BORDER};
    margin: 28px 0;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{
    width: 5px; height: 5px;
}}
::-webkit-scrollbar-track {{
    background: transparent;
}}
::-webkit-scrollbar-thumb {{
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: rgba(255,255,255,0.12);
}}

/* ── Radio buttons (horizontal) ── */
.stRadio > div {{
    gap: 4px !important;
}}
.stRadio [role="radiogroup"] > label {{
    background: {SURFACE_1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 9px !important;
    padding: 6px 16px !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    color: {TEXT_TERTIARY} !important;
    transition: all 0.2s !important;
}}
.stRadio [role="radiogroup"] > label:hover {{
    border-color: {BORDER_HOVER} !important;
    color: {TEXT_SECONDARY} !important;
}}
.stRadio [role="radiogroup"] > label[data-checked="true"],
.stRadio [role="radiogroup"] > label:has(input:checked) {{
    background: rgba(124, 108, 255, 0.1) !important;
    border-color: {ACCENT} !important;
    color: {ACCENT_LIGHT} !important;
}}

/* ── Number inputs ── */
.stNumberInput > div > div > input {{
    background: {SURFACE_1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT_PRIMARY} !important;
    font-family: {FONT_MONO} !important;
    font-size: 0.85rem !important;
}}

/* ── Containers ── */
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stVerticalBlockBorderWrapper"]) {{
    border-radius: 14px;
}}

/* ── Captions ── */
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {TEXT_TERTIARY} !important;
    font-size: 0.78rem !important;
}}

/* ── Plotly chart container ── */
.stPlotlyChart {{
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid {BORDER};
}}

/* ── Selection highlight ── */
::selection {{
    background: rgba(124, 108, 255, 0.3);
    color: #fff;
}}
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Reusable HTML components
# ---------------------------------------------------------------------------

def page_header(icon: str, title: str, subtitle: str, badge: str = ""):
    """Render a refined page header with gradient title and optional badge."""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
<div style="margin-bottom: 32px; padding-top: 8px;">
    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px; flex-wrap: wrap;">
        <div style="
            width: 44px; height: 44px;
            background: linear-gradient(135deg, rgba(124,108,255,0.15) 0%, rgba(86,204,242,0.1) 100%);
            border: 1px solid rgba(124,108,255,0.2);
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.4rem;
            flex-shrink: 0;
        ">{icon}</div>
        <h1 style="margin: 0; font-size: 1.8rem; line-height: 1.1;">{title}</h1>
        {badge_html}
    </div>
    <p style="color: {TEXT_TERTIARY}; font-size: 0.9rem; margin: 0; line-height: 1.5; max-width: 720px; padding-left: 58px;">{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def glass_card(content: str, **kwargs):
    """Render content inside a glassmorphism card."""
    st.markdown(f'<div class="glass-card">{content}</div>', unsafe_allow_html=True)


def stat_pill(label: str, status: str = "green"):
    """Render a small status pill — green / red / amber."""
    return f'<span class="stat-pill"><span class="dot dot-{status}"></span>{label}</span>'


def status_bar(items: list[tuple[str, str]]):
    """Render a row of stat pills. items = [(label, status), ...]"""
    pills = "".join(stat_pill(label, status) for label, status in items)
    st.markdown(f'<div style="margin-bottom: 16px;">{pills}</div>', unsafe_allow_html=True)


def feature_cards(cards: list[dict]):
    """Render a grid of feature cards.

    cards = [{"icon": "...", "title": "...", "desc": "..."}, ...]
    """
    items = ""
    for card in cards:
        icon = card.get("icon", "")
        items += f"""
<div class="feature-card">
    <span class="card-icon">{icon}</span>
    <h4>{card['title']}</h4>
    <p>{card['desc']}</p>
</div>"""
    st.markdown(f'<div class="feature-grid">{items}</div>', unsafe_allow_html=True)


def section_header(text: str, icon: str = ""):
    """A refined section separator with accent line."""
    st.markdown(
        f"""
<div style="display:flex; align-items:center; gap:10px; margin:32px 0 16px 0;">
    <div style="
        width: 28px; height: 28px;
        background: rgba(124,108,255,0.1);
        border-radius: 7px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem;
        flex-shrink: 0;
    ">{icon}</div>
    <h3 style="margin:0; font-size:0.95rem; font-weight:600; color:{TEXT_SECONDARY}; letter-spacing:-0.01em;">{text}</h3>
    <div style="flex:1; height:1px; background:linear-gradient(90deg, {BORDER} 0%, transparent 100%); margin-left:8px;"></div>
</div>
""",
        unsafe_allow_html=True,
    )


def kpi_row(metrics: list[dict]):
    """Render a row of styled KPI metrics.

    metrics = [{"label": "...", "value": "...", "delta": "..."}, ...]
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(m["label"], m["value"], m.get("delta", None))


def provider_badge(provider: str) -> str:
    """Return an HTML badge for the active model provider."""
    colors = {
        "gemma": ("#4285F4", "Gemma"),
        "claude": ("#CC785C", "Claude"),
        "openai": ("#10a37f", "OpenAI"),
        "gemini": ("#886FBF", "Gemini"),
    }
    color, label = colors.get(provider.lower(), (ACCENT, provider))
    return f'<span style="background:rgba({_hex_to_rgb(color)},0.12);color:{color};font-size:0.68rem;font-weight:600;padding:3px 10px;border-radius:20px;letter-spacing:0.04em;text-transform:uppercase;border:1px solid rgba({_hex_to_rgb(color)},0.15);">{label}</span>'


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i : i + 2], 16)) for i in (0, 2, 4))
