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


# Build google.genai stub before the google namespace so it can be included as an attr
fake_genai_types = SimpleNamespace(GenerateContentConfig=SimpleNamespace)
fake_genai = SimpleNamespace(Client=SimpleNamespace, types=fake_genai_types)

fake_storage = SimpleNamespace(Client=_FakeStorageClient, Bucket=SimpleNamespace)
fake_exceptions = SimpleNamespace(NotFound=Exception, GoogleAPIError=Exception)
fake_google_cloud = SimpleNamespace(storage=fake_storage)
fake_google_api_core = SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault(
    "google",
    SimpleNamespace(
        cloud=fake_google_cloud, api_core=fake_google_api_core, genai=fake_genai
    ),
)
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)
sys.modules.setdefault("google.genai", fake_genai)
sys.modules.setdefault("google.genai.types", fake_genai_types)

import engine.ai_summary  # must come after sys.modules stubs

TEST_SETTINGS = config.Settings(
    gcs_bucket_name="test-bucket",
    vertex_project="test-project",
    vertex_location="us-central1",
    vertex_model="gemini-3.8-flash",
)


def _fake_client(expected: str = "ok"):
    return SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kw: SimpleNamespace(text=expected)
        )
    )


def test_generate_ai_summary_includes_payloads(monkeypatch):
    play_by_play = {"events": [{"event_type": "goal", "team_name": "Flyers"}]}
    game_story = {"stars": ["Player One"]}
    expected = "Summary text"

    captured = {}

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        assert "goal" in captured["prompt"]
        assert "Player One" in captured["prompt"]
        return SimpleNamespace(text=expected)

    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=fake_generate)
    )
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

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, editorial=editorial)

    assert "Historic rivalry clash" in captured["prompt"]
    assert "500th time" in captured["prompt"]


def test_generate_ai_summary_no_editorial_uses_fallback(monkeypatch):
    """When editorial is None, the prompt includes the fallback text."""
    captured = {}

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, editorial=None)

    assert "No editorial recap available." in captured["prompt"]


def test_generate_ai_summary_uses_model_from_settings(monkeypatch):
    """generate_content is called with the model name from settings."""
    captured = {}

    def fake_generate(**kw):
        captured["model"] = kw.get("model")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    custom_settings = config.Settings(
        gcs_bucket_name="test-bucket",
        vertex_project="test-project",
        vertex_location="us-central1",
        vertex_model="gemini-3.8-flash",
    )
    with config.override_settings(custom_settings):
        engine.ai_summary.generate_ai_summary({}, {})

    assert captured["model"] == "gemini-3.8-flash"


def test_generate_ai_summary_includes_standings(monkeypatch):
    """Standings text appears in the prompt when standings are provided."""
    standings = [
        {
            "teamAbbrev": "MTL",
            "divisionSequence": 4,
            "divisionName": "Atlantic",
            "wins": 35,
            "losses": 30,
            "otLosses": 7,
            "points": 77,
            "streakCode": "W",
            "streakCount": 2,
        }
    ]
    captured = {}

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, standings=standings)

    assert "MTL" in captured["prompt"]
    assert "Atlantic" in captured["prompt"]
    assert "77pts" in captured["prompt"]


def test_generate_ai_summary_no_standings_uses_fallback(monkeypatch):
    captured = {}

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, standings=None)

    assert "Standings unavailable." in captured["prompt"]


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

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, season_series=season_series)

    assert "2-1" in captured["prompt"]
    assert "NJD" in captured["prompt"]
    assert "2024-10-04" in captured["prompt"]


def test_generate_ai_summary_no_series_uses_fallback(monkeypatch):
    captured = {}

    def fake_generate(**kw):
        captured["prompt"] = kw.get("contents", "")
        return SimpleNamespace(text="ok")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with config.override_settings(TEST_SETTINGS):
        engine.ai_summary.generate_ai_summary({}, {}, season_series=None)

    assert "Season series data unavailable." in captured["prompt"]


def test_generate_ai_summary_handles_error(monkeypatch):
    def fake_generate(**kw):
        raise ConnectionError("boom")

    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate)),
    )

    with (
        config.override_settings(TEST_SETTINGS),
        pytest.raises(RuntimeError, match="boom"),
    ):
        engine.ai_summary.generate_ai_summary({}, {})


@pytest.mark.parametrize("text", [None, "", "   \n\t "])
def test_generate_ai_summary_empty_response_raises(monkeypatch, text):
    # Gemini returns text=None when a response is blocked (e.g. safety filters)
    monkeypatch.setattr(
        engine.ai_summary,
        "_get_client",
        lambda: SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda **kw: SimpleNamespace(text=text)
            )
        ),
    )

    with (
        config.override_settings(TEST_SETTINGS),
        pytest.raises(RuntimeError, match="empty response"),
    ):
        engine.ai_summary.generate_ai_summary({}, {})
