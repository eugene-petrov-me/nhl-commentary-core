"""Batch game summarization for a full date."""

from __future__ import annotations

import logging
from typing import List

from data_fetch.schedule import get_schedule
from models.game_summary import GameSummary
from .summarize_game import summarize_game

logger = logging.getLogger(__name__)


def summarize_date(
    date: str,
    *,
    use_ai: bool = True,
) -> List[GameSummary]:
    """Summarize all games scheduled on a given date.

    Games that fail are logged and skipped; the returned list contains only
    successful summaries. Team and score fields are enriched from the schedule.

    Args:
        date: Game date in YYYY-MM-DD format.
        use_ai: When True (default), use the AI summary path.

    Returns:
        List of GameSummary objects, one per successfully processed game.
    """
    schedule = get_schedule(date)
    results: List[GameSummary] = []

    for game in schedule:
        try:
            summary = summarize_game(game.game_id, date=date, use_ai=use_ai)
            enriched = summary.model_copy(update={
                "home_team": game.home_team,
                "away_team": game.away_team,
                "home_score": game.home_team_score,
                "away_score": game.away_team_score,
            })
            results.append(enriched)
        except Exception:
            logger.warning(
                "Failed to summarize game %s on %s; skipping",
                game.game_id,
                date,
                exc_info=True,
            )

    return results


__all__ = ["summarize_date"]
