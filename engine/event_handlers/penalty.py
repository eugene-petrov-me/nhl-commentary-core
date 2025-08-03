from typing import Dict, Any

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
