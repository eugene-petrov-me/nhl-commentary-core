from typing import Dict, Any

def interpret_faceoff(event: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret a faceoff event and return structured LLM-ready data."""
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "faceoff",
        "players": {
            "winner_id": details.get("winningPlayerId"),
            "loser_id": details.get("losingPlayerId"),
        },
        "team_id": details.get("eventOwnerTeamId"),
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord"),
        },
    }
