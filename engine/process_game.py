from data_fetch.play_by_play import get_play_by_play
from engine.transform import transform_event
from typing import List, Dict, Any

def process_game_events(game_id: int) -> List[Dict[str, Any]]:
    raw_data = get_play_by_play(game_id)
    events = raw_data.get("plays", [])
    return [transform_event(e) for e in events]
