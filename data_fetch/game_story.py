from nhlpy import NHLClient
from typing import Dict, Any

client = NHLClient()

def get_game_story(game_id: int) -> Dict[str, Any]:
    """Fetch the game story data for a specific NHL game.

    Args:
        game_id (int): Unique identifier for the game.

    Returns:
        Dict[str, Any]: Dictionary containing game story data, including three stars.
    """
    return client.game_center.game_story(game_id=game_id)
