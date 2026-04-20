"""Obsidian vault export — generates .md files compatible with Obsidian.

All study artifacts (flashcards, study guides, quiz results, mind maps)
can be exported to an Obsidian vault with:
- YAML frontmatter for metadata
- Wiki-links [[]] for cross-referencing
- Mermaid diagrams (rendered natively in Obsidian)
- Tags for organization
"""

import json
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path(__file__).parent.parent / "data" / "obsidian_vault"


def _ensure_vault():
    VAULT_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()[:80]


def export_flashcards(title: str, cards: list[dict], tags: list[str] | None = None) -> Path:
    """Export flashcards as an Obsidian-compatible markdown file.

    Uses the Obsidian Spaced Repetition plugin format:
    Question
    ?
    Answer
    """
    _ensure_vault()
    now = datetime.now().isoformat(timespec="seconds")
    tag_str = ", ".join(f'"{t}"' for t in (tags or ["flashcards"]))

    lines = [
        "---",
        f"title: {title}",
        f"type: flashcards",
        f"created: {now}",
        f"tags: [{tag_str}]",
        f"card_count: {len(cards)}",
        "---",
        "",
        f"# {title}",
        "",
    ]

    for i, card in enumerate(cards, 1):
        front = card.get("front", "")
        back = card.get("back", "")
        card_tags = card.get("tags", [])
        tag_line = " ".join(f"#{t}" for t in card_tags) if card_tags else ""
        lines.extend([
            f"### Card {i} {tag_line}",
            front,
            "?",
            back,
            "",
        ])

    path = VAULT_DIR / f"{_sanitize_filename(title)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_study_guide(title: str, content: str, tags: list[str] | None = None) -> Path:
    """Export a study guide as an Obsidian markdown file."""
    _ensure_vault()
    now = datetime.now().isoformat(timespec="seconds")
    tag_str = ", ".join(f'"{t}"' for t in (tags or ["study-guide"]))

    md = f"""---
title: {title}
type: study-guide
created: {now}
tags: [{tag_str}]
---

{content}
"""
    path = VAULT_DIR / f"{_sanitize_filename(title)}.md"
    path.write_text(md, encoding="utf-8")
    return path


def export_quiz_results(
    title: str,
    questions: list[dict],
    score: int | None = None,
    total: int | None = None,
    tags: list[str] | None = None,
) -> Path:
    """Export quiz results as an Obsidian markdown file."""
    _ensure_vault()
    now = datetime.now().isoformat(timespec="seconds")
    tag_str = ", ".join(f'"{t}"' for t in (tags or ["quiz"]))

    lines = [
        "---",
        f"title: {title}",
        f"type: quiz-results",
        f"created: {now}",
        f"tags: [{tag_str}]",
    ]
    if score is not None and total is not None:
        lines.append(f"score: {score}/{total}")
    lines.extend(["---", "", f"# {title}", ""])

    if score is not None and total is not None:
        pct = round(score / total * 100) if total > 0 else 0
        lines.append(f"**Score: {score}/{total} ({pct}%)**\n")

    for i, q in enumerate(questions, 1):
        lines.append(f"## Q{i}: {q.get('question', '')}")
        if q.get("options"):
            for opt in q["options"]:
                lines.append(f"- {opt}")
        lines.append(f"\n**Correct Answer:** {q.get('correct_answer', '')}")
        if q.get("user_answer"):
            emoji = "+" if q.get("is_correct") else "x"
            lines.append(f"**Your Answer:** {q['user_answer']} [{emoji}]")
        if q.get("explanation"):
            lines.append(f"\n> [!info] Explanation\n> {q['explanation']}")
        lines.append("")

    path = VAULT_DIR / f"{_sanitize_filename(title)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_mind_map(title: str, mermaid_code: str, tags: list[str] | None = None) -> Path:
    """Export a mind map as Obsidian markdown with embedded Mermaid diagram."""
    _ensure_vault()
    now = datetime.now().isoformat(timespec="seconds")
    tag_str = ", ".join(f'"{t}"' for t in (tags or ["mind-map"]))

    md = f"""---
title: {title}
type: mind-map
created: {now}
tags: [{tag_str}]
---

# {title}

```mermaid
{mermaid_code}
```
"""
    path = VAULT_DIR / f"{_sanitize_filename(title)}.md"
    path.write_text(md, encoding="utf-8")
    return path


def export_study_plan(title: str, content: str, tags: list[str] | None = None) -> Path:
    """Export a study plan as an Obsidian markdown file."""
    return export_study_guide(title, content, tags or ["study-plan"])


def list_vault_files() -> list[Path]:
    """List all files in the Obsidian vault."""
    _ensure_vault()
    return sorted(VAULT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
