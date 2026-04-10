"""High-level game summarization utilities."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from models.game_summary import GameSummary
from .process_game import process_game_events
from .ai_summary import generate_ai_summary
from data_fetch.play_by_play import get_play_by_play
from data_fetch.game_story import get_game_story
from data_fetch.editorial import get_editorial, EditorialFetchError
from .summaries import (
    get_or_build_stats_summary,
    save_ai_summary,
    load_ai_summary,
)

logger = logging.getLogger(__name__)


def summarize_game(
    game_id: int,
    date: Optional[str] = None,
    use_ai: bool = True,
) -> GameSummary:
    """Return a structured summary for the specified game.

    Args:
        game_id: NHL game identifier.
        date: Game date in YYYY-MM-DD (for GCS index marking).
        use_ai: If True (default), AI summary is returned/cached.
                If False, rule-based stats summary is returned/cached.

    Returns:
        GameSummary with summary_markdown and metadata.
    """
    now = datetime.now(timezone.utc)

    if use_ai:
        # 1) Try loading from GCS cache
        cached_text = load_ai_summary(game_id=game_id)
        if cached_text:
            return GameSummary(
                game_id=game_id,
                date=date,
                summary_markdown=cached_text,
                summary_type="ai",
                generated_at=now,
                cached=True,
            )

        # 2) Fetch all data, generate, cache
        pbp = get_play_by_play(game_id)
        story = get_game_story(game_id)

        editorial = None
        try:
            editorial = get_editorial(game_id, date=date)
        except EditorialFetchError:
            logger.warning(
                "Editorial fetch failed for game %s; proceeding without it",
                game_id,
                exc_info=True,
            )

        ai_text = generate_ai_summary(pbp, story, editorial=editorial)
        save_ai_summary(game_id=game_id, md=ai_text, date=date)

        return GameSummary(
            game_id=game_id,
            date=date,
            summary_markdown=ai_text,
            summary_type="ai",
            editorial_headline=editorial.get("headline") if editorial else None,
            editorial_summary=editorial.get("summary") if editorial else None,
            generated_at=now,
            cached=False,
        )

    # Rule-based path
    events = process_game_events(game_id)
    stats_text = get_or_build_stats_summary(game_id=game_id, events=events, date=date)

    return GameSummary(
        game_id=game_id,
        date=date,
        summary_markdown=stats_text,
        summary_type="rule_based",
        generated_at=now,
        cached=False,
    )


__all__ = ["summarize_game"]
