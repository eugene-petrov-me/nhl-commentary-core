from typing import List, Dict
from collections import defaultdict

def generate_summary(events: List[Dict]) -> str:
    """
    Generate a basic game summary from structured NHL events.

    Args:
        events (List[Dict]): List of structured event dictionaries.

    Returns:
        str: Simple text summary of the game.
    """
    goals_by_period = {
      "regulation": sum(1 for event in events if event["event_type"] == "goal" and event["period"] in [1, 2, 3]),
      "overtime": sum(1 for event in events if event["event_type"] == "goal" and event["period"] == 4),
      "shootout": sum(1 for event in events if event["event_type"] == "goal" and event["period"] == 5),
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

    # Breakdown by team
    stat_keys = {
        "goal": "goals",
        "shot-on-goal": "shots_on_goal",
        "penalty": "penalties",
        "hit": "hits",
        "faceoff": "faceoffs",
        "blocked-shot": "blocked_shots",
        "missed-shot": "missed_shots",
        "giveaway": "giveaways",
        "takeaway": "takeaways",
        "delayed-penalty": "delayed_penalties",
    }

    team_stats = defaultdict(lambda: {
        "goals": 0,
        "shots_on_goal": 0,
        "penalties": 0,
        "hits": 0,
        "faceoffs": 0,
        "blocked_shots": 0,
        "missed_shots": 0,
        "giveaways": 0,
        "takeaways": 0,
        "delayed_penalties": 0,
    })

    for event in events:
        team_id = event.get("team_id")
        if team_id is None:
            continue
        key = stat_keys.get(event["event_type"])
        if key is None:
            continue
        team_stats[team_id][key] += 1
        if event["event_type"] == "goal":
            team_stats[team_id]["shots_on_goal"] += 1

    summary = (
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

    teams = sorted(team_stats.keys())
    if teams:
        if len(teams) == 2:
            t1, t2 = teams
            summary += (
                "Team Comparison:\n"
                f"- Goals: {team_stats[t1]['goals']} - {team_stats[t2]['goals']}\n"
                f"- Shots on goal: {team_stats[t1]['shots_on_goal']} - {team_stats[t2]['shots_on_goal']}\n"
                f"- Penalties: {team_stats[t1]['penalties']} - {team_stats[t2]['penalties']}\n"
                f"- Hits: {team_stats[t1]['hits']} - {team_stats[t2]['hits']}\n"
                f"- Faceoffs: {team_stats[t1]['faceoffs']} - {team_stats[t2]['faceoffs']}\n"
                f"- Blocked shots: {team_stats[t1]['blocked_shots']} - {team_stats[t2]['blocked_shots']}\n"
                f"- Missed shots: {team_stats[t1]['missed_shots']} - {team_stats[t2]['missed_shots']}\n"
                f"- Giveaways: {team_stats[t1]['giveaways']} - {team_stats[t2]['giveaways']}\n"
                f"- Takeaways: {team_stats[t1]['takeaways']} - {team_stats[t2]['takeaways']}\n"
                f"- Delayed penalties: {team_stats[t1]['delayed_penalties']} - {team_stats[t2]['delayed_penalties']}\n"
            )
        else:
            summary += "Team Breakdown:\n"
            for team in teams:
                stats = team_stats[team]
                summary += (
                    f"Team {team}:\n"
                    f"  Goals: {stats['goals']}\n"
                    f"  Shots on goal: {stats['shots_on_goal']}\n"
                    f"  Penalties: {stats['penalties']}\n"
                    f"  Hits: {stats['hits']}\n"
                    f"  Faceoffs: {stats['faceoffs']}\n"
                    f"  Blocked shots: {stats['blocked_shots']}\n"
                    f"  Missed shots: {stats['missed_shots']}\n"
                    f"  Giveaways: {stats['giveaways']}\n"
                    f"  Takeaways: {stats['takeaways']}\n"
                    f"  Delayed penalties: {stats['delayed_penalties']}\n"
                )

    return summary
