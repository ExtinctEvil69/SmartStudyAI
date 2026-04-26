"""Pluggable data sources for SFT dataset construction.

Each module exposes:
    fetch(spec) -> list[dict]      # raw documents (text, metadata)
    name: str                       # short identifier for log output

Then build_master_dataset.py routes documents through the generators
in fine_tuning.generators (qa/quiz/notes/summary/agent_plan/exam_*).
"""
