"""nhl-commentary-core package."""

from .cli import (
    DEFAULT_DATE,
    GameSelectionError,
    SummaryResult,
    generate_summary_for_date,
    get_schedule,
    main,
    summarize_game,
)

__all__ = [
    "DEFAULT_DATE",
    "GameSelectionError",
    "SummaryResult",
    "generate_summary_for_date",
    "get_schedule",
    "main",
    "summarize_game",
]
