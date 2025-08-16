from data_fetch.play_by_play import get_play_by_play
from data_fetch.game_story import get_game_story
from engine.transform import transform_event
from typing import List, Dict, Any


def process_game_events(game_id: int) -> List[Dict[str, Any]]:
    raw_data = get_play_by_play(game_id)
    events = raw_data.get("plays", [])

    roster_spots = raw_data.get("rosterSpots", [])
    player_map: Dict[int, str] = {}
    player_team_map: Dict[int, int] = {}
    for spot in roster_spots:
        pid = spot.get("playerId")
        player_map[pid] = f"{spot.get('firstName', {}).get('default', '')} {spot.get('lastName', {}).get('default', '')}".strip()
        player_team_map[pid] = spot.get("teamId")

    team_name_map: Dict[int, str] = {}
    abbrev_to_id: Dict[str, int] = {}
    for side in ["homeTeam", "awayTeam"]:
        team = raw_data.get(side, {}) or {}
        tid = team.get("id")
        if tid is None:
            continue
        name = (
            (team.get("name") or {}).get("default")
            or (team.get("commonName") or {}).get("default")
            or team.get("abbrev")
            or f"Team {tid}"
        )
        team_name_map[tid] = name
        abbrev = team.get("abbrev")
        if abbrev:
            abbrev_to_id[abbrev] = tid

    transformed_events = [transform_event(e) for e in events]

    for event in transformed_events:
        team_id = event.get("team_id")
        if team_id in team_name_map:
            event["team_name"] = team_name_map[team_id]

        if event.get("event_type") == "goal":
            players = event.get("players", {})
            scorer_id = players.get("scorer_id")
            if scorer_id is not None:
                players["scorer_name"] = player_map.get(scorer_id)
            assist_ids = players.get("assist_ids", [])
            players["assist_names"] = [player_map.get(aid) for aid in assist_ids]

    story = get_game_story(game_id)
    for side in ["homeTeam", "awayTeam"]:
        team = story.get(side, {}) or {}
        tid = team.get("id")
        if tid and tid not in team_name_map:
            name = (
                (team.get("name") or {}).get("default")
                or (team.get("commonName") or {}).get("default")
                or team.get("abbrev")
                or f"Team {tid}"
            )
            team_name_map[tid] = name

    stars = story.get("summary", {}).get("threeStars", [])
    for star in stars:
        pid = star.get("playerId")
        team_id = player_team_map.get(pid) or abbrev_to_id.get(star.get("teamAbbrev"))
        stats = {
            key: star.get(key)
            for key in ["goalsAgainstAverage", "savePctg", "goals", "assists", "points"]
            if star.get(key) is not None
        }
        transformed_events.append(
            {
                "event_type": "star",
                "star": star.get("star"),
                "team_id": team_id,
                "team_name": team_name_map.get(team_id),
                "players": {
                    "player_id": pid,
                    "name": player_map.get(pid),
                    "team_id": team_id,
                    "position": star.get("position"),
                    "stats": stats,
                },
            }
        )

    game_metadata = {
        "event_type": "metadata",
        "game_id": game_id,
        "game_type": story.get("gameType"),
        "venue": story.get("venue", {}).get("default"),
        "venue_location": story.get("venueLocation", {}).get("default"),
        "home_team": {
            "id": story.get("homeTeam", {}).get("id"),
            "name": (story.get("homeTeam", {}).get("name") or {}).get("default"),
            "abbrev": story.get("homeTeam", {}).get("abbrev"),
            "place_name": (story.get("homeTeam", {}).get("placeName") or {}).get("default"),
            "score": story.get("homeTeam", {}).get("score"),
            "sog": story.get("homeTeam", {}).get("sog"),
            "logo": story.get("homeTeam", {}).get("logo"),
        },
        "away_team": {
            "id": story.get("awayTeam", {}).get("id"),
            "name": (story.get("awayTeam", {}).get("name") or {}).get("default"),
            "abbrev": story.get("awayTeam", {}).get("abbrev"),
            "place_name": (story.get("awayTeam", {}).get("placeName") or {}).get("default"),
            "score": story.get("awayTeam", {}).get("score"),
            "sog": story.get("awayTeam", {}).get("sog"),
            "logo": story.get("awayTeam", {}).get("logo"),
        },
    }
    transformed_events.append(game_metadata)

    return transformed_events
