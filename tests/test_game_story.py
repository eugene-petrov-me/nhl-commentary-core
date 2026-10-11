"""Tests for data_fetch.game_story cache-read fallback."""

import pytest

import config
from data_fetch import game_story

TEST_SETTINGS = config.Settings(
    gcs_bucket_name="test-bucket",
    vertex_project="test-project",
    vertex_location="us-central1",
    vertex_model="gemini-3.8-flash",
)

CACHED_STORY = {"summary": {"threeStars": []}, "gameDate": "2025-04-25"}
LIVE_STORY = {"summary": {"threeStars": ["live"]}, "gameDate": "2025-04-25"}


class _FakeGoogleAPIError(Exception):
    """Stand-in for GoogleAPIError, independent of any sys.modules stubs."""


def _patch(monkeypatch, download_json, mark=lambda *a, **kw: None):
    calls = {"api": 0, "upload": 0}

    class DummyGameCenter:
        def game_story(self, game_id):
            calls["api"] += 1
            return LIVE_STORY

    class DummyClient:
        def __init__(self):
            self.game_center = DummyGameCenter()

    def upload_json(*a, **kw):
        calls["upload"] += 1

    monkeypatch.setattr(game_story, "GoogleAPIError", _FakeGoogleAPIError)
    monkeypatch.setattr(game_story, "NHLClient", DummyClient)
    monkeypatch.setattr(game_story, "check_file_exists", lambda *a, **kw: True)
    monkeypatch.setattr(game_story, "download_json", download_json)
    monkeypatch.setattr(game_story, "upload_json", upload_json)
    monkeypatch.setattr(game_story, "mark_artifact", mark)
    return calls


def test_cache_hit_returns_cached(monkeypatch):
    calls = _patch(monkeypatch, lambda b, p: CACHED_STORY)

    with config.override_settings(TEST_SETTINGS):
        result = game_story.get_game_story(1, mark_index=False)

    assert result == CACHED_STORY
    assert calls["api"] == 0


@pytest.mark.parametrize(
    "exc", [_FakeGoogleAPIError("gcs down"), ValueError("bad json")]
)
def test_cache_read_gcs_or_json_error_logs_warning_and_uses_api(
    monkeypatch, caplog, exc
):
    def download_json(bucket, path):
        raise exc

    calls = _patch(monkeypatch, download_json)

    with config.override_settings(TEST_SETTINGS), caplog.at_level("WARNING"):
        result = game_story.get_game_story(1, mark_index=False)

    assert result == LIVE_STORY
    assert calls["api"] == 1
    assert calls["upload"] == 1
    assert "Failed to read game story cache for game 1" in caplog.text


def test_cache_read_unexpected_error_raises(monkeypatch):
    def download_json(bucket, path):
        raise RuntimeError("bug")

    calls = _patch(monkeypatch, download_json)

    with (
        config.override_settings(TEST_SETTINGS),
        pytest.raises(RuntimeError, match="bug"),
    ):
        game_story.get_game_story(1, mark_index=False)

    assert calls["api"] == 0


def test_cache_hit_index_failure_returns_cached_without_refetch(monkeypatch, caplog):
    """A failing date-index update must not discard a good cache hit."""

    def failing_mark(*a, **kw):
        raise _FakeGoogleAPIError("index write failed")

    calls = _patch(monkeypatch, lambda b, p: CACHED_STORY, mark=failing_mark)

    with config.override_settings(TEST_SETTINGS), caplog.at_level("WARNING"):
        result = game_story.get_game_story(1, date="2025-04-25")

    assert result == CACHED_STORY
    assert calls["api"] == 0
    assert calls["upload"] == 0
    assert "Failed to mark raw_story index" in caplog.text
