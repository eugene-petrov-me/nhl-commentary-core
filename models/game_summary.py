"""Structured output model for a summarised NHL game."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class GameSummary(BaseModel):
    """Typed result returned by summarize_game and summarize_date."""

    game_id: int
    date: Optional[str] = None          # YYYY-MM-DD
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    summary_markdown: str
    summary_type: Literal["ai", "rule_based"]
    editorial_headline: Optional[str] = None
    editorial_summary: Optional[str] = None
    generated_at: datetime
    cached: bool


__all__ = ["GameSummary"]
