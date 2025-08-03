from typing import Dict, Any
from .event_handlers import EVENT_HANDLERS

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