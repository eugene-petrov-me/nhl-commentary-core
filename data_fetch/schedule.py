import logging
from typing import List, Optional

from nhlpy import NHLClient

from config import get_settings
from models.game_schedule import GameSchedule

# Optional: only if you want to prefill the date index
try:
    from engine.date_index import mark_artifact  # your simple index helper
except Exception:  # pragma: no cover - optional dependency
    mark_artifact = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

class ScheduleFetchError(Exception):
    """Raised when fetching the schedule fails."""


def get_schedule(
    date: str,
    *,
    bucket_name: Optional[str] = None,
    mark_index: bool = True,
) -> List[GameSchedule]:
    """
    Fetch the NHL game schedule for a specific date.

    Args:
        date: 'YYYY-MM-DD'
        bucket_name: If provided and mark_index=True, seed per-date index with matchups.
        mark_index: When True and bucket_name is provided, create/update rows in the
                    index for each game with away/home but without setting any artifacts yet.

    Returns:
        List[GameSchedule]: one per game.

    Raises:
        ScheduleFetchError: On fetch errors.
    """
    try:
        client = NHLClient()
    except Exception as exc:  # pragma: no cover - defensive programming
        raise ScheduleFetchError(f"Failed to create NHL client: {exc}") from exc

    try:
        sched = client.schedule.get_schedule(date=date)
    except Exception as exc:  # pragma: no cover - defensive programming
        raise ScheduleFetchError(f"Failed to fetch schedule for {date}: {exc}") from exc

    games = sched.get("games", []) or []

    schedules: List[GameSchedule] = [
        GameSchedule(
            game_id=g.get("id"),
            season_id=g.get("season"),
            game_type=g.get("gameType"),
            home_team=(g.get("homeTeam") or {}).get("abbrev"),
            home_team_score=(g.get("homeTeam") or {}).get("score"),
            away_team=(g.get("awayTeam") or {}).get("abbrev"),
            away_team_score=(g.get("awayTeam") or {}).get("score"),
            winning_goal_scorer_id=(g.get("winningGoalScorer") or {}).get("playerId"),
        )
        for g in games
    ]

    # Seed the simple per-date index with matchups (no artifacts yet)
    if mark_index:
        bucket = bucket_name or get_settings().gcs_bucket_name
    else:
        bucket = None

    if mark_index and bucket and mark_artifact is not None:
        for s in schedules:
            try:
                mark_artifact(
                    bucket,
                    date=date,
                    game_id=s.game_id,
                    away=s.away_team,
                    home=s.home_team,
                    artifact="raw_pbp",   # set to False to ensure key exists
                    exists=False,
                )
                # Also ensure 'raw_story' key exists (False) so your
                # list_games_missing(...) works immediately.
                mark_artifact(
                    bucket,
                    date=date,
                    game_id=s.game_id,
                    artifact="raw_story",
                    exists=False,
                )
            except Exception:
                # Non-fatal; schedule fetch should not fail due to index writes
                logger.warning(
                    "Failed to seed index for game %s on %s", s.game_id, date, exc_info=True
                )

    return schedules
