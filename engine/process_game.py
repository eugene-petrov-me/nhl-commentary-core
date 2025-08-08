from data_fetch.play_by_play import get_play_by_play
from data_fetch.game_story import get_game_story
from engine.transform import transform_event
from typing import List, Dict, Any


def process_game_events(game_id: int) -> List[Dict[str, Any]]:
    raw_data = get_play_by_play(game_id)
    events = raw_data.get("plays", [])

    roster_spots = raw_data.get("rosterSpots", [])
    player_map = {
        spot.get("playerId"): f"{spot.get('firstName', {}).get('default', '')} {spot.get('lastName', {}).get('default', '')}".strip()
        for spot in roster_spots
    }

    transformed_events = [transform_event(e) for e in events]

    story = get_game_story(game_id)
    stars = story.get("summary", {}).get("threeStars", [])
    for star in stars:
        pid = star.get("playerId")
        transformed_events.append(
            {
                "event_type": "star",
                "star": star.get("star"),
                "players": {"player_id": pid, "name": player_map.get(pid)},
            }
        )

    return transformed_events
