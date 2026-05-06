import sys
from types import SimpleNamespace

import pytest

import config

# Stub out heavy dependencies so the module imports cleanly
fake_nhlpy = SimpleNamespace(NHLClient=lambda: SimpleNamespace())
sys.modules.setdefault("nhlpy", fake_nhlpy)

class _FakeStorageClient:
    def bucket(self, *args, **kwargs):
        return SimpleNamespace(
            blob=lambda *a, **kw: SimpleNamespace(
                exists=lambda: False,
                download_as_text=lambda: "",
                upload_from_string=lambda *a, **kw: None,
            )
        )

fake_storage = SimpleNamespace(Client=_FakeStorageClient, Bucket=SimpleNamespace)
fake_exceptions = SimpleNamespace(NotFound=Exception)
fake_google_cloud = SimpleNamespace(storage=fake_storage)
fake_google_api_core = SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault("google", SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core))
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import engine.ai_summary  # noqa: E402 — must come after sys.modules stubs


TEST_SETTINGS = config.Settings(
    gcs_bucket_name="test-bucket",
    openai_api_key="test-key",
    openai_model="gpt-4o-mini",
)


def test_generate_ai_summary_includes_payloads(monkeypatch):
    play_by_play = {"events": [{"event_type": "goal", "team_name": "Flyers"}]}
    game_story = {"stars": ["Player One"]}
    expected = "Summary text"

    def fake_create(*args, **kwargs):
        input_payload = kwargs["input"]
        assert "goal" in input_payload
        assert "Player One" in input_payload
        return SimpleNamespace(output_text=expected)

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        summary = engine.ai_summary.generate_ai_summary(play_by_play, game_story)

    assert summary == expected


def test_generate_ai_summary_includes_editorial(monkeypatch):
    """When editorial is provided, its headline and body appear in the prompt."""
    editorial = {
        "headline": "Historic rivalry clash",
        "body": "The Habs and Leafs met for the 500th time.",
        "summary": "A great game.",
    }
    captured = {}

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, editorial=editorial)

    assert "Historic rivalry clash" in captured["input"]
    assert "500th time" in captured["input"]


def test_generate_ai_summary_no_editorial_uses_fallback(monkeypatch):
    """When editorial is None, the prompt includes the fallback text."""
    captured = {}

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, editorial=None)

    assert "No editorial recap available." in captured["input"]


def test_generate_ai_summary_uses_model_from_settings(monkeypatch):
    captured = {}

    def fake_create(*args, **kwargs):
        captured["model"] = kwargs.get("model")
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    custom_settings = config.Settings(
        gcs_bucket_name="test-bucket",
        openai_api_key="test-key",
        openai_model="gpt-4o",
    )
    with config.override_settings(custom_settings):
        engine.ai_summary.generate_ai_summary({}, {})

    assert captured["model"] == "gpt-4o"


def test_generate_ai_summary_includes_standings(monkeypatch):
    """Standings text appears in the prompt when standings are provided."""
    standings = [
        {
            "teamAbbrev": "MTL",
            "divisionSequence": 4,
            "divisionName": "Atlantic",
            "wins": 35, "losses": 30, "otLosses": 7,
            "points": 77, "streakCode": "W", "streakCount": 2,
        }
    ]
    captured = {}

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, standings=standings)

    assert "MTL" in captured["input"]
    assert "Atlantic" in captured["input"]
    assert "77pts" in captured["input"]


def test_generate_ai_summary_no_standings_uses_fallback(monkeypatch):
    captured = {}

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, standings=None)

    assert "Standings unavailable." in captured["input"]


def test_generate_ai_summary_includes_season_series(monkeypatch):
    """Season series text appears in the prompt when season_series is provided."""
    season_series = {
        "seasonSeriesWins": {"awayTeamWins": 2, "homeTeamWins": 1},
        "seasonSeries": [
            {
                "gameDate": "2024-10-04",
                "awayTeam": {"abbrev": "NJD", "score": 4},
                "homeTeam": {"abbrev": "BUF", "score": 1},
            }
        ],
    }
    captured = {}

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, season_series=season_series)

    assert "2-1" in captured["input"]
    assert "NJD" in captured["input"]
    assert "2024-10-04" in captured["input"]


def test_generate_ai_summary_no_series_uses_fallback(monkeypatch):
    captured = {}

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, season_series=None)

    assert "Season series data unavailable." in captured["input"]


def test_generate_ai_summary_handles_error(monkeypatch):
    def fake_create(*args, **kwargs):
        raise Exception("boom")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(engine.ai_summary, "_get_client", lambda: fake_client)

    with config.override_settings(TEST_SETTINGS):
        with pytest.raises(RuntimeError, match="boom"):
            engine.ai_summary.generate_ai_summary({}, {})


def test_missing_api_key_raises_at_settings_load(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GCS_BUCKET_NAME", raising=False)
    config.clear_overrides()
    config.reload_settings.__globals__["_default_settings"] = None  # type: ignore[index]

    # Patch _build_settings directly to simulate missing key
    original_build = config._build_settings

    def build_without_key():
        import os
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")
        return original_build()

    monkeypatch.setattr(config, "_build_settings", build_without_key)
    monkeypatch.setattr(config, "_default_settings", None)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        config.get_settings()
