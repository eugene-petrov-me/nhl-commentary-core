"""Fetch current standings for two teams from the NHL API."""
from __future__ import annotations

import logging
from typing import List

from nhlpy import NHLClient

logger = logging.getLogger(__name__)


class StandingsFetchError(Exception):
    """Raised when fetching standings fails."""


def get_standings(date: str, *, home_abbr: str, away_abbr: str) -> List[dict]:
    """Return standings entries for the home and away teams.

    Filters the full league standings to the two teams. Returns an empty list
    if the API returns no data for the given date.
    """
    try:
        client = NHLClient()
    except Exception as exc:
        raise StandingsFetchError(f"Failed to create NHL client: {exc}") from exc

    try:
        data = client.standings.get_standings(date=date)
    except Exception as exc:
        raise StandingsFetchError(f"Failed to fetch standings for {date}: {exc}") from exc

    all_standings = data.get("standings") or []
    abbrevs = {home_abbr, away_abbr}
    return [
        s for s in all_standings
        if _abbrev(s) in abbrevs
    ]


def _abbrev(entry: dict) -> str:
    """Extract team abbreviation from a standings entry (handles dict or string)."""
    raw = entry.get("teamAbbrev", "")
    if isinstance(raw, dict):
        return raw.get("default", "")
    return raw


__all__ = ["StandingsFetchError", "get_standings"]
