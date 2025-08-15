from typing import List, Dict
from collections import defaultdict

def generate_summary(events: List[Dict]) -> str:
    """
    Compact game summary:
    - Header with metadata (game type, venue, matchup, final score with (OT)/(SO) when applicable)
    - Team comparison (away-home) using team abbreviations
    - 3 Stars (if present)
    - Top goal scorers & top point scorers

    Notes:
    - Team SOG counts goals + shot-on-goal in regulation + OT (periods 1-4).
    - Team 'Goals' in the comparison table are Reg+OT only (SO excluded).
    - Final Score shows (OT) or (SO) when needed.
    """
    # ---------- Metadata ----------
    metadata = next((e for e in events if e.get("event_type") == "metadata"), None)
    home_team = metadata.get("home_team") if metadata else {}
    away_team = metadata.get("away_team") if metadata else {}

    GAME_TYPE = {1: "Preseason", 2: "Regular Season", 3: "Playoffs"}
    game_type = GAME_TYPE.get(metadata.get("game_type") if metadata else None, "Unknown")
    venue = ", ".join([v for v in [
        metadata.get("venue") if metadata else None,
        metadata.get("venue_location") if metadata else None
    ] if v])

    home_id  = home_team.get("id")
    away_id  = away_team.get("id")
    home_ab  = home_team.get("abbrev", "HOME")
    away_ab  = away_team.get("abbrev", "AWY")

    # ---------- Team-level aggregation ----------
    stat_keys = {
        "goal":           "goals",
        "shot-on-goal":   "shots_on_goal",  # recalculated with period filter below
        "penalty":        "penalties",
        "hit":            "hits",
        "faceoff":        "faceoffs",
        "blocked-shot":   "blocked_shots",
        "missed-shot":    "missed_shots",
        "giveaway":       "giveaways",
        "takeaway":       "takeaways",
        "delayed-penalty":"delayed_penalties",
    }

    team_stats = defaultdict(lambda: {
        "goals": 0,            # Reg+OT (we'll enforce by counting only p in 1..4)
        "shots_on_goal": 0,    # Reg+OT, goals count as SOG
        "penalties": 0,
        "hits": 0,
        "faceoffs": 0,
        "blocked_shots": 0,
        "missed_shots": 0,
        "giveaways": 0,
        "takeaways": 0,
        "delayed_penalties": 0,
    })

    # Tally per-team with correct period filters
    for e in events:
        etype = e.get("event_type")
        tid   = e.get("team_id")
        per   = e.get("period")

        if tid is None:
            continue

        # Raw counters (no period filter except where noted)
        key = stat_keys.get(etype)
        if key and key not in ("goals", "shots_on_goal"):
            team_stats[tid][key] += 1

        # Goals: Reg+OT only
        if etype == "goal" and per in (1, 2, 3, 4):
            team_stats[tid]["goals"] += 1

        # SOG: Reg+OT only; goals count as SOG
        if etype in ("goal", "shot-on-goal") and per in (1, 2, 3, 4):
            team_stats[tid]["shots_on_goal"] += 1

    # ---------- Determine (OT)/(SO) for final score ----------
    # Default no suffix
    win_type = ""

    if home_team.get("score") is not None and away_team.get("score") is not None and home_id in team_stats and away_id in team_stats:
        final_home = home_team["score"]
        final_away = away_team["score"]

        regot_home = team_stats[home_id]["goals"]  # Reg+OT goals only (from events)
        regot_away = team_stats[away_id]["goals"]

        if final_home != final_away:
            if regot_home != regot_away:
                # Decided in regulation (or in OT but your event goals counted already)
                # To be precise: if there was a goal in period 4 and totals differ at that point, it's OT.
                # We'll explicitly check for any period-4 goal to label OT when Reg-only tie existed.
                reg_tie = sum(1 for e in events if e.get("event_type") == "goal" and e.get("period") in (1,2,3) and e.get("team_id") == home_id) == \
                          sum(1 for e in events if e.get("event_type") == "goal" and e.get("period") in (1,2,3) and e.get("team_id") == away_id)
                ot_goal_happened = any(e.get("event_type") == "goal" and e.get("period") == 4 for e in events)
                if reg_tie and ot_goal_happened:
                    win_type = "(OT)"
                else:
                    win_type = ""  # regulation
            else:
                # Reg+OT goals tied, but final differs -> decided in SO
                win_type = "(SO)"

    # ---------- Header ----------
    lines = []
    lines.append("Game Summary:")
    lines.append("------------------")
    lines.append(f"Game Type: {game_type}")
    if venue:
        lines.append(f"Venue: {venue}")
    lines.append(f"{away_ab} @ {home_ab}")
    if away_team.get("score") is not None and home_team.get("score") is not None:
        lines.append(f"Final Score: {away_team['score']} - {home_team['score']} {win_type}".strip())
    lines.append("------------------")

    # ---------- Team Comparison (Away–Home order) ----------
    if away_id in team_stats and home_id in team_stats:
        A, H = away_id, home_id
        lines.append("Team Comparison:")
        lines.append(f"- Goals ({away_ab}-{home_ab}): {team_stats[A]['goals']} - {team_stats[H]['goals']}")
        lines.append(f"- Shots on goal ({away_ab}-{home_ab}): {team_stats[A]['shots_on_goal']} - {team_stats[H]['shots_on_goal']}")
        lines.append(f"- Penalties ({away_ab}-{home_ab}): {team_stats[A]['penalties']} - {team_stats[H]['penalties']}")
        lines.append(f"- Hits ({away_ab}-{home_ab}): {team_stats[A]['hits']} - {team_stats[H]['hits']}")
        lines.append(f"- Faceoffs ({away_ab}-{home_ab}): {team_stats[A]['faceoffs']} - {team_stats[H]['faceoffs']}")
        lines.append(f"- Blocked shots ({away_ab}-{home_ab}): {team_stats[A]['blocked_shots']} - {team_stats[H]['blocked_shots']}")
        lines.append(f"- Missed shots ({away_ab}-{home_ab}): {team_stats[A]['missed_shots']} - {team_stats[H]['missed_shots']}")
        lines.append(f"- Giveaways ({away_ab}-{home_ab}): {team_stats[A]['giveaways']} - {team_stats[H]['giveaways']}")
        lines.append(f"- Takeaways ({away_ab}-{home_ab}): {team_stats[A]['takeaways']} - {team_stats[H]['takeaways']}")
        lines.append(f"- Delayed penalties ({away_ab}-{home_ab}): {team_stats[A]['delayed_penalties']} - {team_stats[H]['delayed_penalties']}")
    else:
        # Fallback if metadata missing: list whatever teams we saw
        if team_stats:
            lines.append("Team Comparison:")
            for tid, s in team_stats.items():
                tag = f"Team {tid}"
                lines.append(f"- {tag}: G {s['goals']}, SOG {s['shots_on_goal']}, PIM {s['penalties']}")

    summary = "\n".join(lines) + "\n"

    # ---------- Stars & Leaders ----------
    stars = {}
    goals_by_player   = defaultdict(int)
    assists_by_player = defaultdict(int)
    player_names = {}
    player_teams = {}

    for e in events:
        etype = e.get("event_type")
        tid   = e.get("team_id")

        if etype == "goal":
            players = e.get("players") or {}
            scorer  = players.get("scorer_id")
            if scorer is not None:
                goals_by_player[scorer] += 1
                if tid is not None:
                    player_teams[scorer] = tid
                nm = players.get("scorer_name")
                if nm:
                    player_names[scorer] = nm

            for aid in (players.get("assist_ids") or []):
                if aid is not None:
                    assists_by_player[aid] += 1
                    if tid is not None:
                        player_teams[aid] = tid
            for aid, nm in zip(players.get("assist_ids") or [], players.get("assist_names") or []):
                if aid is not None and nm:
                    player_names[aid] = nm

        elif etype == "star":
            rank = e.get("star")
            p    = e.get("players") or {}
            pid  = p.get("player_id")
            if rank is not None and pid is not None:
                stars[rank] = {
                    "id": pid,
                    "name": p.get("name"),
                    "position": p.get("position"),
                    "stats": p.get("stats", {}),
                }
                if p.get("name"):
                    player_names[pid] = p["name"]
                if p.get("team_id") is not None:
                    player_teams[pid] = p["team_id"]

    def fmt_player(pid: int) -> str:
        nm = player_names.get(pid, f"Player {pid}")
        tid = player_teams.get(pid)
        if tid == home_id:
            return f"{nm} ({home_ab})"
        if tid == away_id:
            return f"{nm} ({away_ab})"
        return nm

    if stars:
        summary += "3 Stars of the Game:\n"
        for rank in sorted(stars.keys()):
            p = stars[rank]
            line = f"- Star {rank}: {fmt_player(p['id'])}"
            if p.get("position"):
                line += f" ({p['position']})"
            st = p.get("stats") or {}
            parts = []
            if "goalsAgainstAverage" in st or "savePctg" in st:
                if "goalsAgainstAverage" in st:
                    parts.append(f"GAA: {st['goalsAgainstAverage']}")
                if "savePctg" in st:
                    parts.append(f"SV%: {st['savePctg']}")
            else:
                if "goals" in st:
                    parts.append(f"Goals: {st['goals']}")
                if "assists" in st:
                    parts.append(f"Assists: {st['assists']}")
                if "points" in st:
                    parts.append(f"Points: {st['points']}")
            if parts:
                line += " - " + ", ".join(parts)
            summary += line + "\n"

    if goals_by_player:
        max_g = max(goals_by_player.values())
        leaders = [pid for pid, g in goals_by_player.items() if g == max_g]
        summary += "Top goal scorers (" + str(max_g) + "): " + ", ".join(fmt_player(pid) for pid in sorted(leaders)) + "\n"

    points_by_player = defaultdict(int)
    for pid, g in goals_by_player.items():
        points_by_player[pid] += g
    for pid, a in assists_by_player.items():
        points_by_player[pid] += a
    if points_by_player:
        max_p = max(points_by_player.values())
        leaders = [pid for pid, p in points_by_player.items() if p == max_p]
        summary += "Top point scorers (" + str(max_p) + " pts): " + ", ".join(fmt_player(pid) for pid in sorted(leaders)) + "\n"

    return summary