from nhlpy import NHLClient
from dataclasses import dataclass
import json
import pandas as pd
from typing import List, Dict, Any, Optional

# Initialize the NHL client
client = NHLClient()

@dataclass
class GameSchedule:
    """
    Data structure representing a single NHL game's metadata.

    Attributes:
        game_id (int): Unique identifier for the game.
        season_id (int): NHL season the game belongs to.
        game_type (int): Type of game (1=preseason, 2=regular, 3=playoffs).
        home_team (str): Abbreviation of the home team.
        home_team_score (Optional[int]): Final score of the home team.
        away_team (str): Abbreviation of the away team.
        away_team_score (Optional[int]): Final score of the away team.
        winning_goal_scorer_id (Optional[int]): Player ID of the winning goal scorer.
    """
    game_id: int
    season_id: int
    game_type: int
    home_team: str
    home_team_score: Optional[int]
    away_team: str
    away_team_score: Optional[int]
    winning_goal_scorer_id: Optional[int]


def get_schedule(date: str) -> List[GameSchedule]:
    """
    Fetch the NHL game schedule for a specific date.

    Args:
        date (str): The date in 'YYYY-MM-DD' format.

    Returns:
        List[GameSchedule]: A list of GameSchedule objects containing game metadata.
    """
    schedule = client.schedule.get_schedule(date=date)
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
            winning_goal_scorer_id=game.get("winningGoalScorer", {}).get("playerId")
        )
        for game in games
    ]


def get_play_by_play(game_id: int) -> Dict[str, Any]:
    """
    Fetch the play-by-play data for a specific NHL game.

    Args:
        game_id (int): Unique identifier for the game.

    Returns:
        Dict[str, Any]: Dictionary containing play-by-play event data.
    """
    return client.game_center.play_by_play(game_id=game_id)


def interpret_goal(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret a goal event and return structured LLM-ready data.

    Args:
        event (Dict[str, Any]): Raw event data from the API.

    Returns:
        Dict[str, Any]: Normalized dictionary describing the goal event.
    """
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "goal",
        "players": {
            "scorer_id": details.get("scoringPlayerId"),
            "assist_ids": [
                details.get("assist1PlayerId"),
                details.get("assist2PlayerId")
            ]
        },
        "goalie_id": details.get("goalieInNetId"),
        "team_id": details.get("eventOwnerTeamId"),
        "score": {
            "home": details.get("homeScore", 0),
            "away": details.get("awayScore", 0)
        },
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "shot_type": details.get("shotType"),
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord")
        },
        "highlight": details.get("highlightClipSharingUrl")
    }


def interpret_shot_on_goal(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret a shot-on-goal event and return structured LLM-ready data.

    Args:
        event (Dict[str, Any]): Raw event data from the API.

    Returns:
        Dict[str, Any]: Normalized dictionary describing the shot-on-goal event.
    """
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "shot-on-goal",
        "players": {
            "shooter_id": details.get("shootingPlayerId")
        },
        "goalie_id": details.get("goalieInNetId"),
        "team_id": details.get("eventOwnerTeamId"),
        "shot_on_goals": {
            "home": details.get("homeSOG", 0),
            "away": details.get("awaySOG", 0)
        },
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "shot_type": details.get("shotType"),
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord")
        }
    }


def interpret_penalty(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret a penalty event and return structured LLM-ready data.

    Args:
        event (Dict[str, Any]): Raw event data from the API.

    Returns:
        Dict[str, Any]: Normalized dictionary describing the penalty event.
    """
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "penalty",
        "players": {
            "committed_player_id": details.get("committedByPlayerId"),
            "drawn_player_id": details.get("drawnByPlayerId")
        },
        "team_id": details.get("eventOwnerTeamId"),
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "penalty": {
            "type": details.get("typeCode"),
            "reason": details.get("descKey"),
            "duration": details.get("duration"),
        },
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord")
        }
    }


# Define the event interpreters
EVENT_HANDLERS = {
    "goal": interpret_goal,
    "shot-on-goal": interpret_shot_on_goal,
    "penalty": interpret_penalty,
    # Add more mappings as needed...
}

def transform_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a raw event into a structured format using the appropriate handler.

    Args:
        event (Dict[str, Any]): Raw event data from the API.

    Returns:
        Dict[str, Any]: Normalized dictionary describing the event.
    """
    event_type = event.get("typeDescKey").lower()
    handler = EVENT_HANDLERS.get(event_type)

    if handler:
        return handler(event)
    
    return {"event_type": "unknown", "raw_data": event}