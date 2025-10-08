import pytest

import main
from models.game_schedule import GameSchedule


def make_game(game_id: int) -> GameSchedule:
    return GameSchedule(
        game_id=game_id,
        season_id="20242025",
        game_type="R",
        home_team="MTL",
        home_team_score=3,
        away_team="COL",
        away_team_score=2,
        winning_goal_scorer_id=42,
    )


def test_generate_summary_for_date_requires_game_id_for_multiple_games(monkeypatch):
    monkeypatch.setattr(main, "get_schedule", lambda date: [make_game(1), make_game(2)])
    with pytest.raises(main.GameSelectionError):
        main.generate_summary_for_date("2025-04-25")


def test_generate_summary_for_date_returns_summary(monkeypatch):
    monkeypatch.setattr(main, "get_schedule", lambda date: [make_game(99)])
    monkeypatch.setattr(main, "summarize_game", lambda game_id, use_ai: f"summary-{game_id}-{use_ai}")
    result = main.generate_summary_for_date("2025-04-25", use_ai=False)
    assert result.summary == "summary-99-False"
    assert result.game.game_id == 99


def test_non_interactive_requires_arguments(monkeypatch):
    with pytest.raises(SystemExit):
        main.main(["--non-interactive"])
