from typing import List, Dict

def generate_summary(events: List[Dict]) -> str:
    """
    Generate a basic game summary from structured NHL events.

    Args:
        events (List[Dict]): List of structured event dictionaries.

    Returns:
        str: Simple text summary of the game.
    """
    goal_count = sum(1 for event in events if event["event_type"] == "goal")
    sog_count = sum(1 for event in events if event["event_type"] in ["shot-on-goal", "goal"])
    penalty_count = sum(1 for event in events if event["event_type"] == "penalty")

    return (
        f"Game Summary:\n"
        f"- Goals scored: {goal_count}\n"
        f"- Shots on goal: {sog_count}\n"
        f"- Penalties: {penalty_count}\n"
    )
