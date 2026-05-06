"""Fetch season series data for a game matchup from the NHL API."""
from __future__ import annotations

import logging

from nhlpy import NHLClient

logger = logging.getLogger(__name__)


class SeasonSeriesFetchError(Exception):
    """Raised when fetching season series fails."""


def get_season_series(game_id: int) -> dict:
    """Return season series data for the matchup of the given game.

    Returns a dict with keys:
        seasonSeries: list of game dicts for every matchup this season
        seasonSeriesWins: dict with awayTeamWins and homeTeamWins
    """
    try:
        client = NHLClient()
    except Exception as exc:
        raise SeasonSeriesFetchError(f"Failed to create NHL client: {exc}") from exc

    try:
        data = client.game_center.right_rail(game_id=str(game_id))
    except Exception as exc:
        raise SeasonSeriesFetchError(
            f"Failed to fetch right_rail for game {game_id}: {exc}"
        ) from exc

    return {
        "seasonSeries": data.get("seasonSeries") or [],
        "seasonSeriesWins": data.get("seasonSeriesWins") or {},
    }


__all__ = ["SeasonSeriesFetchError", "get_season_series"]
