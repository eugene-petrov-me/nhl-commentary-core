from nhlpy import NHLClient
from typing import Any, Dict


class PlayByPlayFetchError(Exception):
    """Raised when fetching play-by-play data fails."""


def get_play_by_play(game_id: int) -> Dict[str, Any]:
    """Fetch the play-by-play data for a specific NHL game.

    Args:
        game_id (int): Unique identifier for the game.

    Returns:
        Dict[str, Any]: Dictionary containing play-by-play event data.

    Raises:
        PlayByPlayFetchError: If the play-by-play data cannot be retrieved.
    """
    try:
        client = NHLClient()
        return client.game_center.play_by_play(game_id=game_id)
    except Exception as exc:  # pragma: no cover - defensive programming
        raise PlayByPlayFetchError(
            f"Failed to fetch play-by-play for game {game_id}: {exc}"
        ) from exc

