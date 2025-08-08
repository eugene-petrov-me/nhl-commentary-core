from typing import Dict, Any

def interpret_delayed_penalty(event: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret a delayed-penalty event and return structured LLM-ready data."""
    details = event.get("details", {})
    period = event.get("periodDescriptor", {}).get("number")
    time = event.get("timeInPeriod")

    return {
        "event_type": "delayed-penalty",
        "team_id": details.get("eventOwnerTeamId"),
        "period": period,
        "time": time,
        "zone": details.get("zoneCode"),
        "location": {
            "x": details.get("xCoord"),
            "y": details.get("yCoord"),
        },
    }
