"""High-level game summarization utilities."""
from typing import Optional
from .process_game import process_game_events
from .ai_summary import generate_ai_summary
from data_fetch.play_by_play import get_play_by_play 
from data_fetch.game_story import get_game_story
from .summaries import (
    get_or_build_stats_summary,
    save_ai_summary,
    load_ai_summary,
)


def summarize_game(game_id: int, date: Optional[str] = None, use_ai: bool = True) -> str:
    """Return a summary for the specified game.

    Args:
        game_id (int): NHL game identifier.
        date (str, optional): Game date in YYYY-MM-DD (for index marking).
        use_ai (bool, optional): If True (default), AI summary is returned/cached.
                                 If False, rule-based stats summary is returned/cached.

    Returns:
        str: Generated or cached summary text.
    """
    if use_ai:
        # 1) Try loading AI summary from GCS
        ai = load_ai_summary(game_id=game_id)
        if ai:
            return ai

        # 2) If none exists, fetch pbp + story, generate, cache
        pbp = get_play_by_play(game_id)
        story = get_game_story(game_id)
        ai_summary = generate_ai_summary(pbp, story)
        save_ai_summary(game_id=game_id, md=ai_summary, date=date)
        return ai_summary

    # Stats (rule-based) summary: always use the cache wrapper
    events = process_game_events(game_id)
    return get_or_build_stats_summary(game_id=game_id, events=events, date=date)


__all__ = ["summarize_game"]