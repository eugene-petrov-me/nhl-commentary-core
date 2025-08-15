from nhlpy import NHLClient
from models.game_schedule import GameSchedule
from typing import List


class ScheduleFetchError(Exception):
    """Raised when fetching the schedule fails."""


def get_schedule(date: str) -> List[GameSchedule]:
    """Fetch the NHL game schedule for a specific date.

    Args:
        date (str): The date in 'YYYY-MM-DD' format.

    Returns:
        List[GameSchedule]: A list of GameSchedule objects containing game metadata.

    Raises:
        ScheduleFetchError: If the schedule cannot be retrieved for the given date.
    """
    try:
        client = NHLClient()
        schedule = client.schedule.get_schedule(date=date)
    except Exception as exc:  # pragma: no cover - defensive programming
        raise ScheduleFetchError(
            f"Failed to fetch schedule for {date}: {exc}"
        ) from exc

    games = schedule.get("games", [])
    return [
        GameSchedule(
            game_id=game.get("id"),
            season_id=game.get("season"),
            game_type=game.get("gameType"),
            home_team=game.get("homeTeam", {}).get("abbrev"),
            home_team_score=game.get("homeTeam", {}).get("score"),
            away_team=game.get("awayTeam", {}).get("abbrev"),
            away_team_score=game.get("awayTeam", {}).get("score"),
            winning_goal_scorer_id=game.get("winningGoalScorer", {}).get("playerId"),
        )
        for game in games
    ]
