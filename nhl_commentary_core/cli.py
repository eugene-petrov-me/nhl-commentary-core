"""Command-line interface for nhl-commentary-core."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Iterable, Optional

try:  # pragma: no cover - optional dependency during testing
    from data_fetch.schedule import get_schedule as _get_schedule
except Exception:  # pragma: no cover - fallback when optional deps missing
    _get_schedule = None

try:  # pragma: no cover - optional dependency during testing
    from engine.summarize_game import summarize_game as _summarize_game
except Exception:  # pragma: no cover - fallback when optional deps missing
    _summarize_game = None
from models.game_schedule import GameSchedule

DEFAULT_DATE = "2025-04-01"  # Fallback date if user input is empty

logger = logging.getLogger(__name__)


class GameSelectionError(RuntimeError):
    """Raised when a requested game cannot be determined."""


@dataclass(frozen=True)
class SummaryResult:
    summary: Optional[str]
    game: GameSchedule


def get_schedule(*args, **kwargs):
    """Lazily resolve the schedule fetcher to keep optional deps optional."""

    if _get_schedule is None:  # pragma: no cover - exercised when deps missing
        raise ImportError(
            "data_fetch.schedule.get_schedule is unavailable; ensure optional dependencies "
            "are installed or monkeypatch `get_schedule` before use."
        )
    return _get_schedule(*args, **kwargs)


def summarize_game(*args, **kwargs):
    """Lazily resolve the summarizer to keep optional deps optional."""

    if _summarize_game is None:  # pragma: no cover - exercised when deps missing
        raise ImportError(
            "engine.summarize_game.summarize_game is unavailable; ensure optional dependencies "
            "are installed or monkeypatch `summarize_game` before use."
        )
    return _summarize_game(*args, **kwargs)


def _select_game(schedule: Iterable[GameSchedule], *, game_id: Optional[int]) -> GameSchedule:
    games = list(schedule)
    if not games:
        raise GameSelectionError("No games available for the requested date.")
    if game_id is None:
        if len(games) == 1:
            return games[0]
        raise GameSelectionError(
            "Multiple games scheduled; specify `game_id` for deterministic selection."
        )
    for game in games:
        if game.game_id == game_id:
            return game
    raise GameSelectionError(f"Game {game_id} not found in schedule.")


def generate_summary_for_date(
    date: str,
    *,
    game_id: Optional[int] = None,
    use_ai: bool = True,
) -> SummaryResult:
    """Programmatic entry point for summarizing a game on a given date."""

    schedule = get_schedule(date)
    game = _select_game(schedule, game_id=game_id)
    summary = summarize_game(game.game_id, use_ai=use_ai)
    return SummaryResult(summary=summary, game=game)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize an NHL game")
    parser.add_argument("--date", help="Game date (YYYY-MM-DD)")
    parser.add_argument("--game-id", type=int, help="NHL game ID to summarize")
    parser.add_argument("--ai", dest="use_ai", action="store_true", help="Use AI summary")
    parser.add_argument(
        "--rule",
        dest="use_ai",
        action="store_false",
        help="Use rule-based summary",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Fail instead of prompting for missing values.",
    )
    parser.set_defaults(use_ai=None)
    return parser


def _interactive_flow(args: argparse.Namespace) -> None:
    date = args.date or input("Enter game date (YYYY-MM-DD): ").strip() or DEFAULT_DATE
    schedule = get_schedule(date)

    if not schedule:
        print("No games scheduled for this date.")
        return

    print("Available games:")
    for idx, game in enumerate(schedule, start=1):
        print(f"{idx}. {game.away_team} at {game.home_team} (ID: {game.game_id})")

    selection = args.game_id
    if selection is None:
        selection_input = input("Select a game number: ").strip()
        try:
            selection = schedule[int(selection_input) - 1].game_id
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

    use_ai = args.use_ai
    if use_ai is None:
        choice = input("Use AI-generated summary? [Y/n]: ").strip().lower()
        use_ai = choice != "n"

    try:
        result = generate_summary_for_date(date, game_id=selection, use_ai=use_ai)
    except GameSelectionError as exc:
        print(str(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to summarize game interactively")
        print(f"❌ Failed to process game {selection}: {exc}")
        return

    game = result.game
    print(f"Processing Game ID: {game.game_id} ({game.home_team} vs {game.away_team})")
    if result.summary:
        print(result.summary)
    else:
        print(f"⚠️ No events for game {game.game_id}")


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.non_interactive:
        missing = [
            flag
            for flag, value in (
                ("--date", args.date),
                ("--game-id", args.game_id),
                ("--ai/--rule", args.use_ai),
            )
            if value is None
        ]
        if missing:
            parser.error(
                "Non-interactive mode requires explicit values for: " + ", ".join(missing)
            )
        try:
            result = generate_summary_for_date(
                args.date,
                game_id=args.game_id,
                use_ai=args.use_ai,
            )
        except Exception as exc:
            logger.exception("Failed to summarize game")
            raise SystemExit(str(exc)) from exc

        if result.summary:
            print(result.summary)
        else:
            print(f"⚠️ No events for game {result.game.game_id}")
        return

    _interactive_flow(args)


__all__ = [
    "DEFAULT_DATE",
    "GameSelectionError",
    "SummaryResult",
    "get_schedule",
    "generate_summary_for_date",
    "summarize_game",
    "main",
]
