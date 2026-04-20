"""Vidya Smriti — Learning Memory Dashboard.

Cross-tool memory layer inspired by the BrahmaVidya blueprint.
Tracks learner profile, topic mastery, study activity, and
provides personalized recommendations across all SmartStudy tools.
"""

import time
from dataclasses import asdict

import streamlit as st

from core.sidebar import render_sidebar
from core.ui_components import (
    inject_global_css,
    page_header,
    section_header,
    feature_cards,
    kpi_row,
    ACCENT,
    ACCENT_LIGHT,
    ACCENT_DARK,
    ACCENT_GLOW,
    CYAN,
    TEAL,
    CORAL,
    AMBER,
    SURFACE_1,
    SURFACE_2,
    SURFACE_3,
    BORDER,
    BORDER_HOVER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
    SUCCESS,
    WARNING,
    ERROR,
    FONT_MONO,
    _hex_to_rgb,
)
from core.vidya_smriti import (
    LearnerProfile,
    get_events,
    get_mastery,
    get_tool_usage_stats,
    get_study_streak,
    get_recommendations,
    get_active_topics,
    log_event,
    update_mastery,
)

st.set_page_config(page_title="Vidya Smriti", page_icon="🧬", layout="wide")
inject_global_css()
model_config = render_sidebar("smriti")

page_header(
    "🧬",
    "Vidya Smriti — Learning Memory",
    "Your persistent learning profile across all SmartStudy tools. Track mastery, review activity, and get personalized study recommendations.",
    badge="Memory Layer",
)

# ── Load data ────────────────────────────────────────────────────────────
profile = LearnerProfile.load()
events = get_events(500)
mastery = get_mastery()
streak = get_study_streak()
tool_stats = get_tool_usage_stats()
active_topics = get_active_topics()

# ── KPIs ─────────────────────────────────────────────────────────────────
total_events = len(events)
topics_tracked = len(mastery)
avg_mastery = round(sum(m["score"] for m in mastery.values()) / max(len(mastery), 1), 1)
tools_used = len(tool_stats)

kpi_row([
    {"label": "Study Sessions", "value": str(total_events)},
    {"label": "Topics Tracked", "value": str(topics_tracked)},
    {"label": "Avg Mastery", "value": f"{avg_mastery}%"},
    {"label": "Study Streak", "value": f"{streak}d"},
    {"label": "Tools Used", "value": f"{tools_used}/20"},
])

# ── Tabs ─────────────────────────────────────────────────────────────────
tab_dash, tab_mastery, tab_activity, tab_profile, tab_log = st.tabs([
    "Dashboard",
    "Mastery Map",
    "Activity",
    "Learner Profile",
    "Quick Log",
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard
# ══════════════════════════════════════════════════════════════════════════
with tab_dash:
    # ── Recommendations ──
    section_header("Personalized recommendations", "💡")
    recs = get_recommendations(profile, mastery, events)

    for rec in recs:
        _type_colors = {
            "review": CORAL,
            "spaced_repetition": AMBER,
            "explore": CYAN,
            "celebrate": SUCCESS,
        }
        color = _type_colors.get(rec["type"], ACCENT_LIGHT)
        st.markdown(
            f"""<div class="glass-card" style="display:flex;gap:16px;align-items:flex-start;padding:18px 22px;">
    <div style="font-size:1.4rem;flex-shrink:0;margin-top:2px;">{rec['icon']}</div>
    <div style="flex:1;">
        <div style="font-weight:600;color:{color};font-size:0.92rem;margin-bottom:4px;">{rec['title']}</div>
        <div style="color:{TEXT_TERTIARY};font-size:0.82rem;line-height:1.5;">{rec['reason']}</div>
        <div style="color:{TEXT_SECONDARY};font-size:0.8rem;margin-top:6px;font-style:italic;">{rec['action']}</div>
    </div>
    <span style="background:rgba({_hex_to_rgb(color)},0.12);color:{color};font-size:0.65rem;font-weight:600;
                 padding:3px 10px;border-radius:20px;letter-spacing:0.04em;text-transform:uppercase;
                 border:1px solid rgba({_hex_to_rgb(color)},0.15);white-space:nowrap;margin-top:2px;">
        {rec['type'].replace('_', ' ')}
    </span>
</div>""",
            unsafe_allow_html=True,
        )

    # ── Active topics ──
    if active_topics:
        section_header("Active topics (last 24h)", "🔥")
        pills = "".join(
            f'<span style="display:inline-block;background:{SURFACE_2};border:1px solid {BORDER};'
            f'border-radius:20px;padding:5px 14px;font-size:0.8rem;color:{TEXT_SECONDARY};'
            f'font-weight:500;margin:3px 4px;">{t}</span>'
            for t in active_topics[:12]
        )
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:2px;">{pills}</div>', unsafe_allow_html=True)

    # ── Tool usage distribution ──
    if tool_stats:
        section_header("Tool usage distribution", "📊")
        sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1], reverse=True)
        max_count = max(v for _, v in sorted_tools)
        bars_html = ""
        _tool_colors = {
            "NetSeek": CYAN, "NeuroRead": ACCENT_LIGHT, "QuizVerse": CORAL,
            "EduTube": AMBER, "MindMapper": TEAL, "PrepMaster": SUCCESS,
            "AudioOverview": "#E879F9", "GraphiQ": CYAN, "CodeBuddy": TEAL,
            "Studio": AMBER, "WriteWise": ACCENT_LIGHT,
        }
        for tool_name, count in sorted_tools[:10]:
            pct = int((count / max_count) * 100)
            color = _tool_colors.get(tool_name, ACCENT_LIGHT)
            bars_html += f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
    <div style="width:110px;font-size:0.8rem;color:{TEXT_SECONDARY};font-weight:500;text-align:right;">{tool_name}</div>
    <div style="flex:1;height:24px;background:{SURFACE_1};border-radius:6px;overflow:hidden;border:1px solid {BORDER};">
        <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{color},rgba({_hex_to_rgb(color)},0.4));
                     border-radius:6px;transition:width 0.6s cubic-bezier(0.4,0,0.2,1);"></div>
    </div>
    <div style="width:40px;font-size:0.78rem;color:{TEXT_TERTIARY};font-family:{FONT_MONO};">{count}</div>
</div>"""
        st.markdown(bars_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — Mastery Map
# ══════════════════════════════════════════════════════════════════════════
with tab_mastery:
    section_header("Topic mastery heat map", "🎯")

    if not mastery:
        st.info("No mastery data yet. Use QuizVerse, NeuroRead, or the Quick Log tab to track your first topic.")
    else:
        sorted_mastery = sorted(mastery.values(), key=lambda m: m["score"], reverse=True)

        # Grid of mastery cards
        cols = st.columns(3)
        for i, m in enumerate(sorted_mastery):
            score = m["score"]
            if score >= 80:
                color, label = SUCCESS, "Strong"
            elif score >= 60:
                color, label = AMBER, "Developing"
            elif score >= 40:
                color, label = "#FB923C", "Emerging"
            else:
                color, label = ERROR, "Needs Work"

            days_ago = max(0, int((time.time() - m["last_studied"]) / 86400))
            freshness = "today" if days_ago == 0 else f"{days_ago}d ago"

            with cols[i % 3]:
                st.markdown(
                    f"""<div class="glass-card" style="padding:18px 20px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span style="font-weight:600;color:{TEXT_PRIMARY};font-size:0.9rem;">{m['topic']}</span>
        <span style="background:rgba({_hex_to_rgb(color)},0.12);color:{color};font-size:0.65rem;font-weight:600;
                     padding:2px 8px;border-radius:12px;letter-spacing:0.04em;">{label}</span>
    </div>
    <div style="height:8px;background:{SURFACE_2};border-radius:4px;overflow:hidden;margin-bottom:10px;">
        <div style="width:{score}%;height:100%;background:linear-gradient(90deg,{color},{ACCENT_LIGHT});
                     border-radius:4px;transition:width 0.5s;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:{TEXT_TERTIARY};">
        <span>{score}% mastery</span>
        <span>{m['attempts']} attempts</span>
        <span>{freshness}</span>
    </div>
    <div style="margin-top:8px;font-size:0.72rem;color:{TEXT_TERTIARY};">
        Sources: {', '.join(m.get('sources', [])[:4]) or 'N/A'}
    </div>
</div>""",
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — Activity Timeline
# ══════════════════════════════════════════════════════════════════════════
with tab_activity:
    section_header("Learning activity timeline", "📜")

    if not events:
        st.info("No activity recorded yet. Start using any SmartStudy tool to build your timeline.")
    else:
        # Show most recent first
        recent = list(reversed(events[-50:]))
        _event_icons = {
            "content_ingested": "📥",
            "quiz_completed": "🧠",
            "notes_generated": "📝",
            "search_performed": "🔍",
            "diagram_created": "🔀",
            "audio_generated": "🎙️",
            "plan_created": "📋",
            "code_analyzed": "💻",
            "flashcards_created": "🃏",
            "study_logged": "📖",
        }

        timeline_html = ""
        for evt in recent:
            icon = _event_icons.get(evt.event_type, "📌")
            ts = time.strftime("%b %d, %H:%M", time.localtime(evt.timestamp))
            detail_parts = []
            for k, v in evt.details.items():
                if k not in ("timestamp",):
                    detail_parts.append(f"<span style='color:{TEXT_TERTIARY};'>{k}: {v}</span>")
            details_html = " · ".join(detail_parts) if detail_parts else ""

            timeline_html += f"""
<div style="display:flex;gap:14px;padding:12px 0;border-bottom:1px solid {BORDER};">
    <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;width:32px;">
        <div style="font-size:1.1rem;">{icon}</div>
        <div style="width:1px;flex:1;background:{BORDER};margin-top:6px;"></div>
    </div>
    <div style="flex:1;padding-bottom:4px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
            <span style="font-weight:600;color:{TEXT_PRIMARY};font-size:0.85rem;">{evt.topic}</span>
            <span style="font-size:0.72rem;color:{TEXT_TERTIARY};font-family:{FONT_MONO};">{ts}</span>
        </div>
        <div style="font-size:0.78rem;color:{TEXT_SECONDARY};margin-bottom:2px;">
            <span style="color:{ACCENT_LIGHT};font-weight:500;">{evt.tool}</span>
            <span style="color:{TEXT_TERTIARY};margin:0 6px;">·</span>
            {evt.event_type.replace('_', ' ')}
        </div>
        <div style="font-size:0.72rem;margin-top:2px;">{details_html}</div>
    </div>
</div>"""

        st.markdown(
            f'<div style="max-height:600px;overflow-y:auto;padding-right:8px;">{timeline_html}</div>',
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — Learner Profile
# ══════════════════════════════════════════════════════════════════════════
with tab_profile:
    section_header("Your learner profile", "👤")
    st.caption("This profile persists across sessions and helps all SmartStudy tools personalize for you.")

    col_form, col_preview = st.columns([3, 2])

    with col_form:
        name = st.text_input("Name", value=profile.name, placeholder="Your name")
        grade = st.text_input("Grade / Level", value=profile.grade_level, placeholder="e.g. Undergraduate, Grade 11")
        style = st.selectbox(
            "Preferred learning style",
            ["", "Visual", "Auditory", "Reading/Writing", "Kinesthetic"],
            index=["", "Visual", "Auditory", "Reading/Writing", "Kinesthetic"].index(profile.preferred_style)
            if profile.preferred_style in ["", "Visual", "Auditory", "Reading/Writing", "Kinesthetic"]
            else 0,
        )
        goals = st.text_area(
            "Learning goals (one per line)",
            value="\n".join(profile.goals),
            height=100,
            placeholder="e.g.\nMaster calculus for finals\nLearn Python for data science",
        )
        subjects = st.text_area(
            "Subjects you're studying (one per line)",
            value="\n".join(profile.subjects),
            height=80,
            placeholder="e.g.\nMathematics\nComputer Science\nBiology",
        )
        strengths = st.text_input("Strengths (comma separated)", value=", ".join(profile.strengths))
        weaknesses = st.text_input("Areas to improve (comma separated)", value=", ".join(profile.weaknesses))

        if st.button("Save Profile", type="primary"):
            profile.name = name
            profile.grade_level = grade
            profile.preferred_style = style
            profile.goals = [g.strip() for g in goals.split("\n") if g.strip()]
            profile.subjects = [s.strip() for s in subjects.split("\n") if s.strip()]
            profile.strengths = [s.strip() for s in strengths.split(",") if s.strip()]
            profile.weaknesses = [w.strip() for w in weaknesses.split(",") if w.strip()]
            profile.save()
            st.success("Profile saved!")

    with col_preview:
        st.markdown(
            f"""<div class="glass-card" style="padding:22px 26px;">
    <div style="text-align:center;margin-bottom:16px;">
        <div style="width:56px;height:56px;background:linear-gradient(135deg,rgba(124,108,255,0.15),rgba(86,204,242,0.1));
                    border:1px solid rgba(124,108,255,0.2);border-radius:16px;display:inline-flex;align-items:center;
                    justify-content:center;font-size:1.6rem;margin-bottom:8px;">👤</div>
        <div style="font-weight:700;color:{TEXT_PRIMARY};font-size:1rem;">{profile.name or 'Learner'}</div>
        <div style="color:{TEXT_TERTIARY};font-size:0.78rem;">{profile.grade_level or 'Not set'}</div>
    </div>
    <div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:4px;">
        <div style="font-size:0.72rem;color:{TEXT_TERTIARY};text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:6px;">Style</div>
        <div style="color:{TEXT_SECONDARY};font-size:0.85rem;margin-bottom:12px;">{profile.preferred_style or '—'}</div>
        <div style="font-size:0.72rem;color:{TEXT_TERTIARY};text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:6px;">Goals</div>
        <div style="color:{TEXT_SECONDARY};font-size:0.82rem;margin-bottom:12px;">{'<br>'.join(f'• {g}' for g in profile.goals) or '—'}</div>
        <div style="font-size:0.72rem;color:{TEXT_TERTIARY};text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:6px;">Subjects</div>
        <div style="color:{TEXT_SECONDARY};font-size:0.82rem;">{'<br>'.join(f'• {s}' for s in profile.subjects) or '—'}</div>
    </div>
</div>""",
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════════
# TAB 5 — Quick Log (manual entry)
# ══════════════════════════════════════════════════════════════════════════
with tab_log:
    section_header("Quick study log", "✏️")
    st.caption("Manually log a study session or update topic mastery. Useful when studying outside SmartStudy tools.")

    col_log, col_mastery = st.columns(2)

    with col_log:
        st.markdown(f"##### Log Activity")
        log_tool = st.selectbox(
            "Tool / Source",
            ["Manual", "NetSeek", "NeuroRead", "QuizVerse", "EduTube", "MindMapper",
             "PrepMaster", "PaperAnalyzer", "AudioOverview", "Studio",
             "MultiSourceSynth", "GraphiQ", "WriteWise", "CodeBuddy",
             "DSASage", "IdeaSpark", "FeatureForge", "CodeFlow", "ArchViz",
             "LogicTrace", "DocGen"],
        )
        log_type = st.selectbox(
            "Event type",
            ["study_logged", "content_ingested", "quiz_completed", "notes_generated",
             "search_performed", "diagram_created", "audio_generated",
             "plan_created", "code_analyzed", "flashcards_created"],
        )
        log_topic = st.text_input("Topic", placeholder="e.g. Organic Chemistry — Reactions")
        log_notes = st.text_input("Notes (optional)", placeholder="e.g. Covered alkene additions")

        if st.button("Log Event") and log_topic:
            log_event(log_tool, log_type, log_topic, notes=log_notes)
            st.success(f"Logged: {log_topic}")
            st.rerun()

    with col_mastery:
        st.markdown(f"##### Update Mastery")
        m_topic = st.text_input("Topic name", placeholder="e.g. Linear Algebra", key="mastery_topic")
        m_score = st.slider("Score (%)", 0, 100, 70, key="mastery_score")
        m_tool = st.text_input("Source tool", value="Manual", key="mastery_tool")

        if st.button("Update Mastery") and m_topic:
            update_mastery(m_topic, m_score, m_tool)
            log_event(m_tool, "study_logged", m_topic, score=m_score)
            st.success(f"Mastery updated: {m_topic} → {m_score}%")
            st.rerun()


# ── Footer ───────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Vidya Smriti is your persistent learning memory. "
    "Activity from other SmartStudy tools feeds into this dashboard automatically."
)
