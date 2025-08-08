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

    # Player-focused information
    stars = {}
    goals_by_player = defaultdict(int)
    assists_by_player = defaultdict(int)
    goal_sequence = []  # (team_id, scorer_id) to determine GWG

    for event in events:
        if event["event_type"] == "goal":
            scorer = event.get("players", {}).get("scorer_id")
            if scorer is not None:
                goals_by_player[scorer] += 1
                goal_sequence.append((event.get("team_id"), scorer))
            for assist in event.get("players", {}).get("assist_ids", []):
                if assist is not None:
                    assists_by_player[assist] += 1
        elif event["event_type"] == "star":
            star_rank = event.get("star")
            player_id = event.get("players", {}).get("player_id")
            if star_rank is not None and player_id is not None:
                stars[star_rank] = player_id

    if stars:
        summary += "3 Stars of the Game:\n"
        for rank in sorted(stars.keys()):
            summary += f"- Star {rank}: Player {stars[rank]}\n"

    # Determine game-winning goal
    gwg = None
    if len(teams) == 2 and team_stats[teams[0]]["goals"] != team_stats[teams[1]]["goals"]:
        winner = max(teams, key=lambda t: team_stats[t]["goals"])
        loser = min(teams, key=lambda t: team_stats[t]["goals"])
        losing_goals = team_stats[loser]["goals"]
        count = 0
        for team_id, scorer in goal_sequence:
            if team_id == winner:
                count += 1
                if count == losing_goals + 1:
                    gwg = scorer
                    break
    if gwg is not None:
        summary += f"Game-winning goal: Player {gwg}\n"

    if goals_by_player:
        max_goals = max(goals_by_player.values())
        top_goal_players = [pid for pid, g in goals_by_player.items() if g == max_goals]
        summary += (
            f"Top goal scorers ({max_goals}): "
            + ", ".join(f"Player {pid}" for pid in sorted(top_goal_players))
            + "\n"
        )

    points_by_player = defaultdict(int)
    for pid, g in goals_by_player.items():
        points_by_player[pid] += g
    for pid, a in assists_by_player.items():
        points_by_player[pid] += a
    if points_by_player:
        max_points = max(points_by_player.values())
        top_point_players = [pid for pid, p in points_by_player.items() if p == max_points]
        summary += (
            f"Top point scorers ({max_points}): "
            + ", ".join(f"Player {pid}" for pid in sorted(top_point_players))
            + "\n"
        )

    return summary
