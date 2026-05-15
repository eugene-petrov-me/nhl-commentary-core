"""High-level game summarization utilities."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime, timezone
from typing import Any, Optional, Type

from models.game_summary import GameSummary
from .process_game import process_game_events
from .ai_summary import generate_ai_summary
from data_fetch.play_by_play import get_play_by_play
from data_fetch.game_story import get_game_story
from data_fetch.editorial import get_editorial, EditorialFetchError
from data_fetch.standings import get_standings, StandingsFetchError
from data_fetch.season_series import get_season_series, SeasonSeriesFetchError
from .summaries import (
    get_or_build_stats_summary,
    save_ai_summary,
    load_ai_summary,
)

logger = logging.getLogger(__name__)


def _safe_result(
    fut: Future, exc_type: Type[Exception], label: str, game_id: int
) -> Optional[Any]:
    try:
        return fut.result()
    except exc_type:
        logger.warning(
            "%s fetch failed for game %s; proceeding without it",
            label,
            game_id,
            exc_info=False,
        )
        logger.debug("%s fetch error detail for game %s", label, game_id, exc_info=True)
        return None


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

        # 2) Fetch all data in parallel, generate, cache
        with ThreadPoolExecutor(max_workers=5) as executor:
            pbp_fut = executor.submit(get_play_by_play, game_id)
            story_fut = executor.submit(get_game_story, game_id)
            editorial_fut = executor.submit(get_editorial, game_id, date=date)
            series_fut = executor.submit(get_season_series, game_id)

            pbp = pbp_fut.result()  # required — propagates on failure
            away_abbr = (pbp.get("awayTeam") or {}).get("abbrev")
            home_abbr = (pbp.get("homeTeam") or {}).get("abbrev")

            standings_fut: Optional[Future] = None
            if date and away_abbr and home_abbr:
                standings_fut = executor.submit(
                    get_standings, date, home_abbr=home_abbr, away_abbr=away_abbr
                )

            story = story_fut.result()  # required — propagates on failure

            editorial = _safe_result(
                editorial_fut, EditorialFetchError, "Editorial", game_id
            )
            season_series = _safe_result(
                series_fut, SeasonSeriesFetchError, "Season series", game_id
            )
            standings = (
                _safe_result(standings_fut, StandingsFetchError, "Standings", game_id)
                if standings_fut
                else None
            )

        ai_text = generate_ai_summary(
            pbp,
            story,
            editorial=editorial,
            standings=standings,
            season_series=season_series,
        )
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
