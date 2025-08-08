from typing import Dict, Any

def interpret_blocked_shot(event: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret a blocked-shot event and return structured LLM-ready data."""
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "blocked-shot",
        "players": {
            "blocker_id": details.get("blockingPlayerId"),
            "shooter_id": details.get("shootingPlayerId"),
        },
        "team_id": details.get("eventOwnerTeamId"),
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "reason": details.get("reason"),
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord"),
        },
    }
