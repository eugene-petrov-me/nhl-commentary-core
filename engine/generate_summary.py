from typing import List, Dict

def generate_summary(events: List[Dict]) -> str:
    """
    Generate a basic game summary from structured NHL events.

    Args:
        events (List[Dict]): List of structured event dictionaries.

    Returns:
        str: Simple text summary of the game.
    """
    goals_by_period = {
      "regulation": sum(1 for event in events if event["event_type"] in ["goal"] and event["period"] in [1, 2, 3]),
      "overtime": sum(1 for event in events if event["event_type"] in ["goal"] and event["period"] == 4),
      "shootout": sum(1 for event in events if event["event_type"] in ["goal"] and event["period"] == 5),
    }

    goal_count = goals_by_period["regulation"] + goals_by_period["overtime"] + goals_by_period["shootout"]

    shots_by_period = {
      "regulation": sum(1 for event in events if event["event_type"] in ["shot-on-goal", "goal"] and event["period"] in [1, 2, 3]),
      "overtime": sum(1 for event in events if event["event_type"] in ["shot-on-goal", "goal"] and event["period"] == 4),
      "shootout": sum(1 for event in events if event["event_type"] in ["shot-on-goal", "goal"] and event["period"] == 5),
    }
    
    sog_count = shots_by_period["regulation"] + shots_by_period["overtime"]
    
    penalty_count = sum(1 for event in events if event["event_type"] == "penalty")

    return (
        f"Game Summary:\n"
        f"- Goals scored: {goal_count} (Reg: {goals_by_period['regulation']}, OT: {goals_by_period['overtime']}, SO: {goals_by_period['shootout']})\n"
        f"- Shots on goal: {sog_count} (Reg: {shots_by_period['regulation']}, OT: {shots_by_period['overtime']}, SO excluded)\n"
        f"- Penalties: {penalty_count}\n"
    )
