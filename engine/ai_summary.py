"""Generate an AI-powered game summary using OpenAI's ChatCompletion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

import openai


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_template(name: str) -> str:
    """Load a text template from the prompts directory."""
    path = TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")


def generate_ai_summary(events: List[Dict]) -> str:
    """Generate a natural language summary for a game.

    Args:
        events (List[Dict]): Structured event data for the game.

    Returns:
        str: Summary produced by the AI model.
    """
    template = _load_template("game_summary.txt")
    populated = template.format(events=json.dumps(events, indent=2))

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": populated}],
    )

    return response["choices"][0]["message"]["content"].strip()


__all__ = ["generate_ai_summary"]
