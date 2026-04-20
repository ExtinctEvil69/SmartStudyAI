"""Vidya Smriti — Shared learning memory layer for SmartStudy AI.

Inspired by the BrahmaVidya blueprint. Provides a persistent,
cross-tool memory system that tracks:
  - Learner profile (goals, strengths, preferences)
  - Content registry (what was studied, when, from which tool)
  - Knowledge graph events (topics mastered, quiz scores, gaps)
  - Active context (current session activity timeline)

Storage: JSON file on disk + st.session_state for live session.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_DATA_DIR = Path(os.environ.get("SMRITI_DATA_DIR", "smriti_data"))
_PROFILE_FILE = _DATA_DIR / "learner_profile.json"
_EVENTS_FILE = _DATA_DIR / "memory_events.jsonl"
_MASTERY_FILE = _DATA_DIR / "mastery.json"

_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class LearnerProfile:
    name: str = ""
    goals: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    preferred_style: str = ""  # visual, auditory, reading, kinesthetic
    grade_level: str = ""
    subjects: list[str] = field(default_factory=list)

    def save(self):
        _PROFILE_FILE.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "LearnerProfile":
        if _PROFILE_FILE.exists():
            try:
                data = json.loads(_PROFILE_FILE.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()


@dataclass
class MemoryEvent:
    """Append-only event representing a learning activity."""
    timestamp: float
    tool: str           # e.g. "QuizVerse", "NeuroRead", "NetSeek"
    event_type: str     # "content_ingested", "quiz_completed", "notes_generated", etc.
    topic: str
    details: dict = field(default_factory=dict)
    # details can include: score, num_questions, source_url, num_pages, etc.


@dataclass
class TopicMastery:
    topic: str
    score: float = 0.0       # 0-100
    attempts: int = 0
    last_studied: float = 0.0
    sources: list[str] = field(default_factory=list)  # tool names that covered this


# ---------------------------------------------------------------------------
# Event log — append-only
# ---------------------------------------------------------------------------
def log_event(
    tool: str,
    event_type: str,
    topic: str,
    **details: Any,
) -> MemoryEvent:
    """Log a learning event. Call this from any page/tool."""
    evt = MemoryEvent(
        timestamp=time.time(),
        tool=tool,
        event_type=event_type,
        topic=topic,
        details=details,
    )
    # Persist to disk
    with open(_EVENTS_FILE, "a") as f:
        f.write(json.dumps(asdict(evt)) + "\n")
    # Also keep in session for live dashboard
    _session_events().append(evt)
    return evt


def get_events(limit: int = 200) -> list[MemoryEvent]:
    """Read recent events from disk."""
    events: list[MemoryEvent] = []
    if _EVENTS_FILE.exists():
        try:
            lines = _EVENTS_FILE.read_text().strip().split("\n")
            for line in lines[-limit:]:
                if line.strip():
                    d = json.loads(line)
                    events.append(MemoryEvent(**{k: v for k, v in d.items() if k in MemoryEvent.__dataclass_fields__}))
        except Exception:
            pass
    return events


def _session_events() -> list[MemoryEvent]:
    if "smriti_events" not in st.session_state:
        st.session_state["smriti_events"] = []
    return st.session_state["smriti_events"]


# ---------------------------------------------------------------------------
# Mastery tracking
# ---------------------------------------------------------------------------
def update_mastery(topic: str, score: float, tool: str):
    """Update mastery score for a topic (weighted rolling average)."""
    mastery_map = _load_mastery()
    topic_key = topic.lower().strip()

    if topic_key in mastery_map:
        m = mastery_map[topic_key]
        # Weighted average: new scores have more weight as attempts grow
        m["attempts"] += 1
        alpha = 0.4  # weight for new score
        m["score"] = round(alpha * score + (1 - alpha) * m["score"], 1)
        m["last_studied"] = time.time()
        if tool not in m["sources"]:
            m["sources"].append(tool)
    else:
        mastery_map[topic_key] = {
            "topic": topic,
            "score": round(score, 1),
            "attempts": 1,
            "last_studied": time.time(),
            "sources": [tool],
        }

    _save_mastery(mastery_map)


def get_mastery() -> dict[str, dict]:
    """Return mastery map: {topic_key: {topic, score, attempts, last_studied, sources}}."""
    return _load_mastery()


def _load_mastery() -> dict:
    if _MASTERY_FILE.exists():
        try:
            return json.loads(_MASTERY_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_mastery(data: dict):
    _MASTERY_FILE.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Cross-tool context helpers
# ---------------------------------------------------------------------------
def get_active_topics() -> list[str]:
    """Return topics from the last 24 hours of events."""
    cutoff = time.time() - 86400
    events = get_events(500)
    topics = []
    seen = set()
    for e in reversed(events):
        if e.timestamp < cutoff:
            break
        key = e.topic.lower().strip()
        if key and key not in seen:
            topics.append(e.topic)
            seen.add(key)
    return topics


def get_tool_usage_stats() -> dict[str, int]:
    """Return {tool_name: event_count} across all time."""
    events = get_events(10000)
    stats: dict[str, int] = {}
    for e in events:
        stats[e.tool] = stats.get(e.tool, 0) + 1
    return stats


def get_study_streak() -> int:
    """Return number of consecutive days with at least one event."""
    events = get_events(10000)
    if not events:
        return 0

    # Collect unique study days
    days = set()
    for e in events:
        day = time.strftime("%Y-%m-%d", time.localtime(e.timestamp))
        days.add(day)

    if not days:
        return 0

    # Count backwards from today
    streak = 0
    import datetime
    current = datetime.date.today()
    while current.isoformat() in days:
        streak += 1
        current -= datetime.timedelta(days=1)
    return streak


def get_recommendations(profile: LearnerProfile, mastery: dict, events: list[MemoryEvent]) -> list[dict]:
    """Generate study recommendations based on memory state."""
    recs = []

    # Find weak topics
    weak = [m for m in mastery.values() if m["score"] < 60]
    weak.sort(key=lambda m: m["score"])
    for m in weak[:3]:
        recs.append({
            "type": "review",
            "icon": "🔄",
            "title": f"Review: {m['topic']}",
            "reason": f"Mastery at {m['score']}% — needs reinforcement",
            "action": "Try QuizVerse or NeuroRead for targeted practice",
        })

    # Find topics not studied recently
    stale_cutoff = time.time() - 3 * 86400  # 3 days
    stale = [m for m in mastery.values() if m["last_studied"] < stale_cutoff and m["score"] < 85]
    stale.sort(key=lambda m: m["last_studied"])
    for m in stale[:2]:
        days_ago = int((time.time() - m["last_studied"]) / 86400)
        recs.append({
            "type": "spaced_repetition",
            "icon": "⏰",
            "title": f"Revisit: {m['topic']}",
            "reason": f"Last studied {days_ago} days ago — spaced repetition window",
            "action": "Quick review via flashcards or a mini quiz",
        })

    # Suggest exploring unused tools
    used_tools = {e.tool for e in events}
    all_tools = {"NetSeek", "NeuroRead", "QuizVerse", "EduTube", "MindMapper",
                 "PrepMaster", "PaperAnalyzer", "AudioOverview", "Studio",
                 "MultiSourceSynth", "GraphiQ", "WriteWise", "CodeBuddy",
                 "DSASage", "IdeaSpark", "FeatureForge", "CodeFlow",
                 "ArchViz", "LogicTrace", "DocGen"}
    unused = all_tools - used_tools
    if unused:
        tool = sorted(unused)[0]
        recs.append({
            "type": "explore",
            "icon": "🔍",
            "title": f"Try {tool}",
            "reason": "You haven't used this tool yet",
            "action": f"Open {tool} from the sidebar to expand your learning toolkit",
        })

    # If no weaknesses, celebrate
    if not recs:
        recs.append({
            "type": "celebrate",
            "icon": "🎉",
            "title": "Great progress!",
            "reason": "All tracked topics above 60% mastery",
            "action": "Add new topics or challenge yourself with harder content",
        })

    return recs
