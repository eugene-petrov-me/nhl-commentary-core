"""Backward-compatible entrypoint for the CLI."""

from nhl_commentary_core import cli as _cli
from nhl_commentary_core.cli import SummaryResult

DEFAULT_DATE = _cli.DEFAULT_DATE
GameSelectionError = _cli.GameSelectionError
get_schedule = _cli.get_schedule
summarize_game = _cli.summarize_game
main = _cli.main


def generate_summary_for_date(
    date: str,
    *,
    game_id: int | None = None,
    use_ai: bool = True,
) -> SummaryResult:
    """Retained programmatic API compatible with older imports."""

    schedule = get_schedule(date)
    game = _cli._select_game(schedule, game_id=game_id)  # type: ignore[attr-defined]
    summary = summarize_game(game.game_id, use_ai=use_ai)
    return SummaryResult(summary=summary, game=game)


__all__ = [
    "DEFAULT_DATE",
    "GameSelectionError",
    "SummaryResult",
    "get_schedule",
    "generate_summary_for_date",
    "summarize_game",
    "main",
]


if __name__ == "__main__":
    main()
