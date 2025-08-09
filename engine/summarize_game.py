"""High-level game summarization utilities."""

from .process_game import process_game_events
from .ai_summary import generate_ai_summary
from .generate_summary import generate_summary


def summarize_game(game_id: int, use_ai: bool = True) -> str:
    """Return a summary for the specified game.

    Args:
        game_id (int): NHL game identifier.
        use_ai (bool, optional): If ``True`` (default), an AI model is used to
            craft a natural language summary. If ``False``, a rule-based
            summary is produced.

    Returns:
        str: Generated summary text.
    """
    events = process_game_events(game_id)
    if use_ai:
        return generate_ai_summary(events)
    return generate_summary(events)


__all__ = ["summarize_game"]
