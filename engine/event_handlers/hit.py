from typing import Dict, Any

def interpret_hit(event: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret a hit event and return structured LLM-ready data."""
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "hit",
        "players": {
            "hitter_id": details.get("hittingPlayerId"),
            "hittee_id": details.get("hitteePlayerId"),
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
