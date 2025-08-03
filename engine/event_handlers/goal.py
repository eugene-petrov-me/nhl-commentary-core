from typing import Dict, Any

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
