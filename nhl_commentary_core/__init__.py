"""nhl-commentary-core package."""

from .cli import (
    DEFAULT_DATE,
    GameSelectionError,
    SummaryResult,
    get_schedule,
    generate_summary_for_date,
    summarize_game,
    main,
)

__all__ = [
    "DEFAULT_DATE",
    "GameSelectionError",
    "SummaryResult",
    "get_schedule",
    "generate_summary_for_date",
    "summarize_game",
    "main",
]
