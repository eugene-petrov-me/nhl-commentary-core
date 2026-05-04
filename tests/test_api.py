"""Tests for api.app routes."""
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import config

# Stub heavy deps before any project imports
fake_nhlpy = SimpleNamespace(NHLClient=lambda: SimpleNamespace())
sys.modules.setdefault("nhlpy", fake_nhlpy)


class _FakeStorageClient:
    def bucket(self, *a, **kw):
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
sys.modules.setdefault(
    "google",
    SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core),
)
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import api.app as app_mod  # noqa: E402
from api.app import app  # noqa: E402
from data_fetch.game_story import GameStoryFetchError  # noqa: E402
from data_fetch.play_by_play import PlayByPlayFetchError  # noqa: E402
from data_fetch.schedule import ScheduleFetchError  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from models.game_summary import GameSummary  # noqa: E402

TEST_SETTINGS = config.Settings(
    gcs_bucket_name="test-bucket",
    openai_api_key="test-key",
    openai_model="gpt-4o-mini",
)

NOW = datetime.now(timezone.utc)
client = TestClient(app)


def _make_summary(game_id: int = 1) -> GameSummary:
    return GameSummary(
        game_id=game_id,
        summary_markdown=f"Summary for {game_id}",
        summary_type="ai",
        generated_at=NOW,
        cached=False,
    )


# --- GET /v1/games/{game_id}/summary ---


def test_get_game_summary_returns_200(monkeypatch):
    monkeypatch.setattr(app_mod, "summarize_game", lambda game_id, date, use_ai: _make_summary(game_id))
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/42/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["game_id"] == 42
    assert body["summary_type"] == "ai"
    assert "summary_markdown" in body


def test_get_game_summary_forwards_query_params(monkeypatch):
    received: dict = {}

    def fake_summarize(game_id, date, use_ai):
        received["game_id"] = game_id
        received["date"] = date
        received["use_ai"] = use_ai
        return _make_summary(game_id)

    monkeypatch.setattr(app_mod, "summarize_game", fake_summarize)
    with config.override_settings(TEST_SETTINGS):
        client.get("/v1/games/99/summary?date=2025-04-25&use_ai=false")
    assert received["game_id"] == 99
    assert received["date"] == "2025-04-25"
    assert received["use_ai"] is False


def test_get_game_summary_pbp_error_returns_502(monkeypatch):
    def fake_summarize(*a, **kw):
        raise PlayByPlayFetchError("NHL API down")

    monkeypatch.setattr(app_mod, "summarize_game", fake_summarize)
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/1/summary")
    assert response.status_code == 502
    assert "NHL API down" in response.json()["detail"]


def test_get_game_summary_story_error_returns_502(monkeypatch):
    def fake_summarize(*a, **kw):
        raise GameStoryFetchError("story fetch failed")

    monkeypatch.setattr(app_mod, "summarize_game", fake_summarize)
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/1/summary")
    assert response.status_code == 502


def test_get_game_summary_openai_error_returns_503(monkeypatch):
    def fake_summarize(*a, **kw):
        raise RuntimeError("OpenAI quota exceeded")

    monkeypatch.setattr(app_mod, "summarize_game", fake_summarize)
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/1/summary")
    assert response.status_code == 503
    assert "OpenAI quota exceeded" in response.json()["detail"]


# --- GET /v1/games/date/{date}/summaries ---


def test_get_date_summaries_returns_200(monkeypatch):
    summaries = [_make_summary(1), _make_summary(2)]
    monkeypatch.setattr(app_mod, "summarize_date", lambda date, use_ai: summaries)
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/date/2025-04-25/summaries")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["game_id"] == 1
    assert body[1]["game_id"] == 2


def test_get_date_summaries_empty_list(monkeypatch):
    monkeypatch.setattr(app_mod, "summarize_date", lambda date, use_ai: [])
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/date/2025-04-25/summaries")
    assert response.status_code == 200
    assert response.json() == []


def test_get_date_summaries_forwards_use_ai(monkeypatch):
    received: dict = {}

    def fake_summarize_date(date, use_ai):
        received["use_ai"] = use_ai
        return []

    monkeypatch.setattr(app_mod, "summarize_date", fake_summarize_date)
    with config.override_settings(TEST_SETTINGS):
        client.get("/v1/games/date/2025-04-25/summaries?use_ai=false")
    assert received["use_ai"] is False


def test_get_date_summaries_schedule_error_returns_502(monkeypatch):
    def fake_summarize_date(*a, **kw):
        raise ScheduleFetchError("schedule fetch failed")

    monkeypatch.setattr(app_mod, "summarize_date", fake_summarize_date)
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/date/2025-04-25/summaries")
    assert response.status_code == 502
    assert "schedule fetch failed" in response.json()["detail"]


def test_get_date_summaries_invalid_date_returns_422():
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/date/not-a-date/summaries")
    assert response.status_code == 422


def test_get_date_summaries_impossible_date_returns_422():
    with config.override_settings(TEST_SETTINGS):
        response = client.get("/v1/games/date/2025-13-01/summaries")
    assert response.status_code == 422
