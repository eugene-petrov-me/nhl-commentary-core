"""Generate an AI-powered game summary using OpenAI's ChatCompletion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from os import getenv
from openai import OpenAI

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"

load_dotenv()
api_key = getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")
client = OpenAI(api_key=api_key)

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

    try:
        response = client.responses.create(
            model="gpt-5-nano",
            instructions="Talk like The Hockey Guy.",
            input=populated,
        )
    except Exception as exc:  # pragma: no cover - upstream exceptions vary
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    return response.output_text.strip()


__all__ = ["generate_ai_summary"]
