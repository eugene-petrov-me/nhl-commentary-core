from nhlpy import NHLClient
from typing import Any, Dict


class GameStoryFetchError(Exception):
    """Raised when fetching a game's story fails."""


def get_game_story(game_id: int) -> Dict[str, Any]:
    """Fetch the game story data for a specific NHL game.

    Args:
        game_id (int): Unique identifier for the game.

    Returns:
        Dict[str, Any]: Dictionary containing game story data, including three stars.

    Raises:
        GameStoryFetchError: If the story data cannot be retrieved.
    """
    try:
        client = NHLClient()
        return client.game_center.game_story(game_id=game_id)
    except Exception as exc:  # pragma: no cover - defensive programming
        raise GameStoryFetchError(
            f"Failed to fetch game story for game {game_id}: {exc}"
        ) from exc

