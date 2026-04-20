"""Structured output schemas and validation helpers for SmartStudy AI.

This mirrors the project-plan requirement for a function-calling layer even
though the current runtime uses prompt-guided JSON generation rather than a
native tool-calling API.
"""

from __future__ import annotations

from typing import Any


SCHEMAS: dict[str, dict[str, Any]] = {
    "quiz": {
        "type": "object",
        "required": ["quiz_title", "questions"],
        "properties": {
            "quiz_title": {"type": "string"},
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["question", "type", "correct_answer", "explanation"],
                    "properties": {
                        "question": {"type": "string"},
                        "type": {"type": "string"},
                        "options": {"type": "array"},
                        "correct_answer": {"type": "string"},
                        "explanation": {"type": "string"},
                        "difficulty": {"type": "string"},
                        "bloom_level": {"type": "string"},
                    },
                },
            },
        },
    },
    "flashcards": {
        "type": "object",
        "required": ["title", "cards"],
        "properties": {
            "title": {"type": "string"},
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["front", "back"],
                    "properties": {
                        "front": {"type": "string"},
                        "back": {"type": "string"},
                        "tags": {"type": "array"},
                    },
                },
            },
        },
    },
    "study_plan": {
        "type": "object",
        "required": ["goal", "weeks"],
        "properties": {
            "goal": {"type": "string"},
            "weeks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["week", "focus_topics", "activities"],
                    "properties": {
                        "week": {"type": "integer"},
                        "focus_topics": {"type": "array"},
                        "activities": {"type": "array"},
                        "checkpoint": {"type": "string"},
                    },
                },
            },
        },
    },
    "citations": {
        "type": "object",
        "required": ["answer", "sources"],
        "properties": {
            "answer": {"type": "string"},
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["source_id", "title"],
                    "properties": {
                        "source_id": {"type": "string"},
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "excerpt": {"type": "string"},
                    },
                },
            },
        },
    },
}


def get_schema(schema_name: str) -> dict[str, Any]:
    if schema_name not in SCHEMAS:
        raise KeyError(f"Unknown schema: {schema_name}")
    return SCHEMAS[schema_name]


def build_json_instruction(schema_name: str) -> str:
    schema = get_schema(schema_name)
    return (
        f"Return valid JSON that matches the `{schema_name}` schema exactly. "
        f"Required keys: {', '.join(schema.get('required', []))}. "
        "Do not include markdown fences or explanatory text outside the JSON object."
    )


def validate_required_fields(payload: dict[str, Any], schema_name: str) -> tuple[bool, list[str]]:
    schema = get_schema(schema_name)
    missing = [field for field in schema.get("required", []) if field not in payload]
    return len(missing) == 0, missing
