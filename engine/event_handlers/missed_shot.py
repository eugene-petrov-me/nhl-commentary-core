from typing import Dict, Any

def interpret_missed_shot(event: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret a missed-shot event and return structured LLM-ready data."""
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "missed-shot",
        "players": {
            "shooter_id": details.get("shootingPlayerId"),
        },
        "goalie_id": details.get("goalieInNetId"),
        "team_id": details.get("eventOwnerTeamId"),
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "shot_type": details.get("shotType"),
        "reason": details.get("reason"),
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord"),
        },
    }
