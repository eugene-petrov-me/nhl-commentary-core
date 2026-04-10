import sys, os, types
from datetime import datetime, timezone

fake_nhlpy = types.SimpleNamespace(NHLClient=lambda: types.SimpleNamespace())
sys.modules['nhlpy'] = fake_nhlpy

class _FakeStorageClient:
    @classmethod
    def from_service_account_json(cls, *args, **kwargs):
        return cls()

    def bucket(self, *args, **kwargs):
        return types.SimpleNamespace(
            blob=lambda *a, **kw: types.SimpleNamespace(
                exists=lambda: False,
                download_as_text=lambda: "",
                upload_from_string=lambda *a, **kw: None,
            )
        )

fake_storage = types.SimpleNamespace(Client=_FakeStorageClient, Bucket=types.SimpleNamespace)
fake_exceptions = types.SimpleNamespace(NotFound=Exception)
fake_google_cloud = types.SimpleNamespace(storage=fake_storage)
fake_google_api_core = types.SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault("google", types.SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core))
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import engine.summarize_game
from models.game_summary import GameSummary


def _make_summary(markdown: str = "test summary", summary_type: str = "rule_based") -> GameSummary:
    return GameSummary(
        game_id=1,
        summary_markdown=markdown,
        summary_type=summary_type,
        generated_at=datetime.now(timezone.utc),
        cached=False,
    )


def test_summarize_game_rule_based(monkeypatch):
    def fake_process_game_events(game_id):
        assert game_id == 1
        return ["event"]

    def fake_get_or_build_stats_summary(game_id, events, date=None):
        assert events == ["event"]
        return "rule summary"

    def fake_generate_ai_summary(*args, **kwargs):
        raise AssertionError("AI summary should not be called")

    monkeypatch.setattr("engine.summarize_game.process_game_events", fake_process_game_events)
    monkeypatch.setattr("engine.summarize_game.get_or_build_stats_summary", fake_get_or_build_stats_summary)
    monkeypatch.setattr("engine.summarize_game.generate_ai_summary", fake_generate_ai_summary)

    result = engine.summarize_game.summarize_game(1, use_ai=False)

    assert isinstance(result, GameSummary)
    assert result.summary_markdown == "rule summary"
    assert result.summary_type == "rule_based"
    assert result.cached is False


def test_summarize_game_ai(monkeypatch):
    def fake_generate_ai_summary(play_by_play, game_story, editorial=None):
        assert play_by_play == ["event"]
        assert game_story == {"story": "data"}
        return "ai summary"

    monkeypatch.setattr("engine.summarize_game.process_game_events", lambda gid: ["event"])
    monkeypatch.setattr("engine.summarize_game.get_or_build_stats_summary",
                        lambda **kw: (_ for _ in ()).throw(AssertionError("should not be called")))
    monkeypatch.setattr("engine.summarize_game.generate_ai_summary", fake_generate_ai_summary)
    monkeypatch.setattr("engine.summarize_game.get_play_by_play", lambda game_id: ["event"])
    monkeypatch.setattr("engine.summarize_game.get_game_story", lambda game_id: {"story": "data"})
    monkeypatch.setattr("engine.summarize_game.get_editorial", lambda game_id, **kw: None)
    monkeypatch.setattr("engine.summarize_game.load_ai_summary", lambda game_id: None)
    monkeypatch.setattr("engine.summarize_game.save_ai_summary", lambda **kw: None)

    result = engine.summarize_game.summarize_game(2, use_ai=True)

    assert isinstance(result, GameSummary)
    assert result.summary_markdown == "ai summary"
    assert result.summary_type == "ai"
    assert result.cached is False


def test_summarize_game_ai_cache_hit(monkeypatch):
    monkeypatch.setattr("engine.summarize_game.load_ai_summary", lambda game_id: "cached text")

    result = engine.summarize_game.summarize_game(3, use_ai=True)

    assert result.summary_markdown == "cached text"
    assert result.cached is True


def test_summarize_game_ai_includes_editorial_fields(monkeypatch):
    editorial = {"headline": "Big win", "summary": "Short recap.", "body": "Long body."}

    monkeypatch.setattr("engine.summarize_game.load_ai_summary", lambda game_id: None)
    monkeypatch.setattr("engine.summarize_game.get_play_by_play", lambda gid: {})
    monkeypatch.setattr("engine.summarize_game.get_game_story", lambda gid: {})
    monkeypatch.setattr("engine.summarize_game.get_editorial", lambda gid, **kw: editorial)
    monkeypatch.setattr("engine.summarize_game.generate_ai_summary",
                        lambda pbp, story, editorial=None: "summary")
    monkeypatch.setattr("engine.summarize_game.save_ai_summary", lambda **kw: None)

    result = engine.summarize_game.summarize_game(4, use_ai=True)

    assert result.editorial_headline == "Big win"
    assert result.editorial_summary == "Short recap."


def test_summarize_game_fetch_failure_propagates(monkeypatch):
    """Fetch errors propagate out of summarize_game so batch.py can catch and skip."""
    monkeypatch.setattr("engine.summarize_game.load_ai_summary", lambda game_id: None)
    monkeypatch.setattr("engine.summarize_game.get_play_by_play",
                        lambda gid: (_ for _ in ()).throw(RuntimeError("network error")))

    import pytest
    with pytest.raises(RuntimeError, match="network error"):
        engine.summarize_game.summarize_game(5, use_ai=True)
