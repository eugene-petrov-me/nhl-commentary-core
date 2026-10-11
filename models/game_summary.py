"""Structured output model for a summarised NHL game."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class GameSummary(BaseModel):
    """Typed result returned by summarize_game and summarize_date."""

    game_id: int
    date: str | None = None  # YYYY-MM-DD
    # None until enriched via model_copy(update={...}) by callers that hold a GameSchedule
    home_team: str | None = None
    away_team: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    summary_markdown: str
    summary_type: Literal["ai", "rule_based"]
    editorial_headline: str | None = None
    editorial_summary: str | None = None
    generated_at: datetime
    cached: bool


__all__ = ["GameSummary"]
