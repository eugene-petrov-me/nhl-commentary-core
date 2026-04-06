"""Generate an AI-powered game summary using OpenAI's ChatCompletion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from openai import OpenAI

from config import get_settings

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_settings().openai_api_key)
    return _client


def _load_template(name: str) -> str:
    """Load a text template from the prompts directory."""
    path = TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")


def generate_ai_summary(
    play_by_play: Dict,
    game_story: Dict,
    editorial: Optional[Dict] = None,
) -> str:
    """Generate a natural language summary for a game.

    Args:
        play_by_play (Dict): Structured play-by-play event data for the game.
        game_story (Dict): Additional narrative data for the game, including
            stars and statistics.
        editorial (Dict, optional): NHL.com editorial recap with headline,
            summary, and full body text. When provided, enriches the AI prompt
            with narrative context (game significance, player quotes, milestones).

    Returns:
        str: Summary produced by the AI model.
    """
    template = _load_template("game_summary.txt")
    editorial_text = (
        f"{editorial.get('headline', '')}\n\n{editorial.get('body', '')}".strip()
        if editorial
        else "No editorial recap available."
    )
    populated = template.format(
        play_by_play=json.dumps(play_by_play, indent=2),
        game_story=json.dumps(game_story, indent=2),
        editorial=editorial_text,
    )

    try:
        response = _get_client().responses.create(
            model=get_settings().openai_model,
            instructions="Talk like The Hockey Guy.",
            input=populated,
        )
    except Exception as exc:  # pragma: no cover - upstream exceptions vary
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    return response.output_text.strip()


__all__ = ["generate_ai_summary"]
