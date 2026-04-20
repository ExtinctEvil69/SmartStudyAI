"""Vidya Smriti — 4-dimensional shared memory layer for BrahmaVidya.

Dimensions:
  1. Learner Profile  — name, goals, strengths, preferences
  2. Knowledge Graph   — topic mastery tracking per tool
  3. Content Registry  — ingested content log (docs, URLs, transcripts)
  4. Active Context    — append-only event log for cross-tool continuity

Persistence: JSON files under smriti_data/ (hackathon-friendly).
No Streamlit dependency — pure Python + JSON.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "smriti_data"
DATA_DIR.mkdir(exist_ok=True)

PROFILE_PATH = DATA_DIR / "learner_profile.json"
MASTERY_PATH = DATA_DIR / "mastery.json"
EVENTS_PATH = DATA_DIR / "memory_events.jsonl"
CONTENT_PATH = DATA_DIR / "content_registry.json"


# ── Learner Profile ─────────────────────────────────────────────────────────

@dataclass
class LearnerProfile:
    name: str = ""
    goals: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    preferred_style: str = "visual"
    created_at: str = ""
    updated_at: str = ""

    def save(self) -> None:
        self.updated_at = _now_iso()
        if not self.created_at:
            self.created_at = self.updated_at
        PROFILE_PATH.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "LearnerProfile":
        if PROFILE_PATH.exists():
            data = json.loads(PROFILE_PATH.read_text())
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()


# ── Knowledge Graph (Topic Mastery) ──────────────────────────────────────────

@dataclass
class TopicMastery:
    topic: str
    score: float = 0.0          # 0-100
    attempts: int = 0
    last_tool: str = ""
    last_updated: str = ""


def update_mastery(topic: str, score: float, tool: str) -> TopicMastery:
    """Update mastery for a topic using exponential moving average."""
    data = _load_mastery()
    key = topic.lower().strip()
    existing = data.get(key, {"topic": topic, "score": 0.0, "attempts": 0})
    n = existing["attempts"]
    old = existing["score"]
    new_score = old * (n / (n + 1)) + score * (1 / (n + 1)) if n > 0 else score
    entry = {
        "topic": topic,
        "score": round(new_score, 1),
        "attempts": n + 1,
        "last_tool": tool,
        "last_updated": _now_iso(),
    }
    data[key] = entry
    MASTERY_PATH.write_text(json.dumps(data, indent=2))
    return TopicMastery(**entry)


def get_mastery(topic: str | None = None) -> dict | list[dict]:
    data = _load_mastery()
    if topic:
        return data.get(topic.lower().strip(), {})
    return sorted(data.values(), key=lambda x: x.get("score", 0), reverse=True)


def _load_mastery() -> dict:
    if MASTERY_PATH.exists():
        return json.loads(MASTERY_PATH.read_text())
    return {}


# ── Memory Event Log ─────────────────────────────────────────────────────────

@dataclass
class MemoryEvent:
    id: str = ""
    tool: str = ""
    action: str = ""
    subject: str = ""
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)


def log_event(tool: str, action: str, subject: str, **metadata) -> MemoryEvent:
    """Append an event to the memory log."""
    evt = MemoryEvent(
        id=uuid.uuid4().hex[:12],
        tool=tool,
        action=action,
        subject=subject,
        timestamp=_now_iso(),
        metadata=metadata,
    )
    with open(EVENTS_PATH, "a") as f:
        f.write(json.dumps(asdict(evt)) + "\n")
    return evt


def get_events(tool: str | None = None, limit: int = 50) -> list[dict]:
    """Read recent events, optionally filtered by tool."""
    if not EVENTS_PATH.exists():
        return []
    lines = EVENTS_PATH.read_text().strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]
    if tool:
        events = [e for e in events if e.get("tool") == tool]
    return list(reversed(events[-limit:]))


# ── Content Registry ─────────────────────────────────────────────────────────

def register_content(source_type: str, title: str, tool: str, **metadata) -> dict:
    """Register ingested content (PDF, URL, transcript, etc.)."""
    registry = _load_content_registry()
    entry = {
        "id": uuid.uuid4().hex[:12],
        "source_type": source_type,
        "title": title,
        "tool": tool,
        "ingested_at": _now_iso(),
        **metadata,
    }
    registry.append(entry)
    CONTENT_PATH.write_text(json.dumps(registry, indent=2))
    log_event(tool, "content_registered", title, source_type=source_type)
    return entry


def get_content_registry() -> list[dict]:
    return _load_content_registry()


def _load_content_registry() -> list[dict]:
    if CONTENT_PATH.exists():
        return json.loads(CONTENT_PATH.read_text())
    return []


# ── Cross-tool Recommendations ──────────────────────────────────────────────

def get_recommendations() -> list[str]:
    """Generate simple recommendations based on memory state."""
    recs: list[str] = []
    mastery = get_mastery()
    events = get_events(limit=100)

    # Weak topics
    if isinstance(mastery, list):
        weak = [t for t in mastery if t.get("score", 0) < 50]
        for t in weak[:3]:
            recs.append(f"Review **{t['topic']}** — current mastery {t['score']}%")

    # Tool diversity
    tools_used = {e.get("tool") for e in events}
    all_tools = {"NetSeek", "EduTube", "QuizForge", "NeuroRead", "MindMapper", "PrepMaster"}
    unused = all_tools - tools_used
    if unused:
        recs.append(f"Try **{', '.join(list(unused)[:2])}** to diversify your study approach")

    # Study streak
    streak = get_study_streak()
    if streak >= 3:
        recs.append(f"Great streak! {streak} consecutive days of studying")
    elif streak == 0:
        recs.append("Start a study session to build your streak")

    if not recs:
        recs.append("Keep up the great work! Explore new topics to expand your knowledge.")
    return recs


def get_study_streak() -> int:
    """Count consecutive days with at least one event."""
    events = get_events(limit=500)
    if not events:
        return 0
    dates = set()
    for e in events:
        ts = e.get("timestamp", "")
        if ts:
            dates.add(ts[:10])
    if not dates:
        return 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    streak = 0
    from datetime import timedelta
    current = datetime.strptime(today, "%Y-%m-%d")
    while current.strftime("%Y-%m-%d") in dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_tool_usage_stats() -> dict[str, int]:
    """Count events per tool."""
    events = get_events(limit=1000)
    stats: dict[str, int] = {}
    for e in events:
        tool = e.get("tool", "unknown")
        stats[tool] = stats.get(tool, 0) + 1
    return stats


def get_dashboard_data() -> dict:
    """Aggregate all memory data for the dashboard."""
    profile = LearnerProfile.load()
    mastery_data = get_mastery()
    events = get_events(limit=20)
    content = get_content_registry()
    streak = get_study_streak()
    usage = get_tool_usage_stats()
    recs = get_recommendations()
    return {
        "profile": asdict(profile),
        "mastery": mastery_data if isinstance(mastery_data, list) else [],
        "recent_events": events,
        "content_count": len(content),
        "content_registry": content[-10:],
        "streak": streak,
        "tool_usage": usage,
        "recommendations": recs,
        "total_events": sum(usage.values()) if usage else 0,
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
