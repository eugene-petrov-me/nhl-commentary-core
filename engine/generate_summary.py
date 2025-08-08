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
    hit_count = sum(1 for event in events if event["event_type"] == "hit")
    faceoff_count = sum(1 for event in events if event["event_type"] == "faceoff")
    blocked_shot_count = sum(1 for event in events if event["event_type"] == "blocked-shot")
    missed_shot_count = sum(1 for event in events if event["event_type"] == "missed-shot")
    giveaway_count = sum(1 for event in events if event["event_type"] == "giveaway")
    takeaway_count = sum(1 for event in events if event["event_type"] == "takeaway")
    delayed_penalty_count = sum(1 for event in events if event["event_type"] == "delayed-penalty")

    return (
        f"Game Summary:\n"
        f"- Goals scored: {goal_count} (Reg: {goals_by_period['regulation']}, OT: {goals_by_period['overtime']}, SO: {goals_by_period['shootout']})\n"
        f"- Shots on goal: {sog_count} (Reg: {shots_by_period['regulation']}, OT: {shots_by_period['overtime']}, SO excluded)\n"
        f"- Penalties: {penalty_count}\n"
        f"- Hits: {hit_count}\n"
        f"- Faceoffs: {faceoff_count}\n"
        f"- Blocked shots: {blocked_shot_count}\n"
        f"- Missed shots: {missed_shot_count}\n"
        f"- Giveaways: {giveaway_count}\n"
        f"- Takeaways: {takeaway_count}\n"
        f"- Delayed penalties: {delayed_penalty_count}\n"
    )
