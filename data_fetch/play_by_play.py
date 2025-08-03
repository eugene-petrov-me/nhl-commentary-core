from nhlpy import NHLClient
from typing import Dict, Any

client = NHLClient()

def get_play_by_play(game_id: int) -> Dict[str, Any]:
    """
    Fetch the play-by-play data for a specific NHL game.

    Args:
        game_id (int): Unique identifier for the game.

    Returns:
        Dict[str, Any]: Dictionary containing play-by-play event data.
    """
    return client.game_center.play_by_play(game_id=game_id)