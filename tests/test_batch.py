"""Tests for engine.batch.summarize_date."""

import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import config

# Stub heavy deps before any project imports
fake_nhlpy = SimpleNamespace(NHLClient=lambda: SimpleNamespace())
sys.modules.setdefault("nhlpy", fake_nhlpy)

class _FakeStorageClient:
    def bucket(self, *a, **kw):
        return SimpleNamespace(blob=lambda *a, **kw: SimpleNamespace(
            exists=lambda: False,
            download_as_text=lambda: "",
            upload_from_string=lambda *a, **kw: None,
        ))

fake_storage = SimpleNamespace(Client=_FakeStorageClient, Bucket=SimpleNamespace)
fake_exceptions = SimpleNamespace(NotFound=Exception)
fake_google_cloud = SimpleNamespace(storage=fake_storage)
fake_google_api_core = SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault("google", SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core))
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import engine.batch as batch_mod  # noqa: E402
from models.game_schedule import GameSchedule
from models.game_summary import GameSummary

TEST_SETTINGS = config.Settings(
    gcs_bucket_name="test-bucket",
    openai_api_key="test-key",
    openai_model="gpt-4o-mini",
)

NOW = datetime.now(timezone.utc)


def _make_game(game_id: int, home: str = "MTL", away: str = "COL") -> GameSchedule:
    return GameSchedule(
        game_id=game_id,
        season_id="20242025",
        game_type="R",
        home_team=home,
        home_team_score=3,
        away_team=away,
        away_team_score=2,
        winning_goal_scorer_id=None,
    )


def _make_summary(game_id: int) -> GameSummary:
    return GameSummary(
        game_id=game_id,
        summary_markdown=f"Summary for {game_id}",
        summary_type="ai",
        generated_at=NOW,
        cached=False,
    )


def test_single_game_success(monkeypatch):
    game = _make_game(100)
    monkeypatch.setattr(batch_mod, "get_schedule", lambda date: [game])
    monkeypatch.setattr(batch_mod, "summarize_game", lambda game_id, date, use_ai: _make_summary(game_id))

    with config.override_settings(TEST_SETTINGS):
        results = batch_mod.summarize_date("2025-04-25")

    assert len(results) == 1
    assert results[0].game_id == 100
    # Enriched with schedule data
    assert results[0].home_team == "MTL"
    assert results[0].away_team == "COL"
    assert results[0].home_score == 3
    assert results[0].away_score == 2


def test_multiple_games(monkeypatch):
    games = [_make_game(1), _make_game(2), _make_game(3)]
    monkeypatch.setattr(batch_mod, "get_schedule", lambda date: games)
    monkeypatch.setattr(batch_mod, "summarize_game", lambda game_id, date, use_ai: _make_summary(game_id))

    with config.override_settings(TEST_SETTINGS):
        results = batch_mod.summarize_date("2025-04-25")

    assert len(results) == 3
    assert {r.game_id for r in results} == {1, 2, 3}


def test_partial_failure_continues(monkeypatch):
    """One failing game is skipped; others succeed."""
    games = [_make_game(10), _make_game(11), _make_game(12)]

    def fake_summarize(game_id, date, use_ai):
        if game_id == 11:
            raise RuntimeError("game 11 exploded")
        return _make_summary(game_id)

    monkeypatch.setattr(batch_mod, "get_schedule", lambda date: games)
    monkeypatch.setattr(batch_mod, "summarize_game", fake_summarize)

    with config.override_settings(TEST_SETTINGS):
        results = batch_mod.summarize_date("2025-04-25")

    assert len(results) == 2
    assert {r.game_id for r in results} == {10, 12}


def test_empty_schedule(monkeypatch):
    monkeypatch.setattr(batch_mod, "get_schedule", lambda date: [])

    with config.override_settings(TEST_SETTINGS):
        results = batch_mod.summarize_date("2025-04-25")

    assert results == []
