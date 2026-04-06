"""Tests for data_fetch.editorial."""

import sys
from types import SimpleNamespace

import pytest

import config

# ---------------------------------------------------------------------------
# Stub heavy dependencies before any project imports
# ---------------------------------------------------------------------------

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

import data_fetch.editorial as editorial_mod  # noqa: E402

TEST_SETTINGS = config.Settings(
    gcs_bucket_name="test-bucket",
    openai_api_key="test-key",
    openai_model="gpt-4o-mini",
)

FAKE_EDITORIAL = {
    "game_id": 12345,
    "headline": "Great game headline",
    "summary": "Short summary here.",
    "body": "Full recap body text.",
    "self_url": "/v2/content/en-us/stories/nhl-great-game",
    "content_date": "2025-04-25",
}

# Forge DAPI response shapes
FORGE_INDEX_RESPONSE = {
    "items": [
        {
            "selfUrl": "/v2/content/en-us/stories/nhl-great-game",
            "headline": {"default": "Great game headline"},
            "summary": {"default": "Short summary here."},
            "contentDate": "2025-04-25",
        }
    ]
}

FORGE_STORY_RESPONSE = {
    "parts": [
        {"type": "markdown", "content": "Full recap body text."},
    ]
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_gcs(*, exists: bool, cached_value=None):
    """Build a fake gcp_ingestion module."""

    def check_file_exists(bucket, path):
        return exists

    def download_json(bucket, path):
        if cached_value is not None:
            return cached_value
        raise RuntimeError("No cached value")

    upload_calls = []

    def upload_json(bucket, path, data):
        upload_calls.append((bucket, path, data))

    fake = SimpleNamespace(
        check_file_exists=check_file_exists,
        download_json=download_json,
        upload_json=upload_json,
        upload_calls=upload_calls,
    )
    return fake


def _make_httpx_mock(index_response, story_response=None, raise_on_index=False, raise_on_story=False):
    """Return a fake httpx module."""

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    class FakeHTTPStatusError(Exception):
        pass

    call_log = []

    def fake_get(url, *, timeout, follow_redirects=True):
        call_log.append(url)
        is_index = "tags.slug" in url
        if is_index:
            if raise_on_index:
                raise FakeHTTPStatusError("404")
            return FakeResponse(index_response)
        else:
            if raise_on_story:
                raise FakeHTTPStatusError("500")
            return FakeResponse(story_response or {})

    fake_httpx = SimpleNamespace(
        get=fake_get,
        HTTPStatusError=FakeHTTPStatusError,
        call_log=call_log,
    )
    return fake_httpx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cache_hit_returns_cached_value(monkeypatch):
    """When GCS has a cached editorial, return it without hitting Forge DAPI."""
    fake_gcs = _make_fake_gcs(exists=True, cached_value=FAKE_EDITORIAL)
    monkeypatch.setattr(editorial_mod, "check_file_exists", fake_gcs.check_file_exists)
    monkeypatch.setattr(editorial_mod, "download_json", fake_gcs.download_json)
    monkeypatch.setattr(editorial_mod, "upload_json", fake_gcs.upload_json)
    monkeypatch.setattr(editorial_mod, "mark_artifact", lambda *a, **kw: None)

    with config.override_settings(TEST_SETTINGS):
        result = editorial_mod.get_editorial(12345)

    assert result == FAKE_EDITORIAL


def test_cache_miss_fetches_and_caches(monkeypatch):
    """On cache miss, fetch from Forge DAPI and upload to GCS."""
    fake_gcs = _make_fake_gcs(exists=False)
    fake_httpx = _make_httpx_mock(FORGE_INDEX_RESPONSE, FORGE_STORY_RESPONSE)

    monkeypatch.setattr(editorial_mod, "check_file_exists", fake_gcs.check_file_exists)
    monkeypatch.setattr(editorial_mod, "download_json", fake_gcs.download_json)
    monkeypatch.setattr(editorial_mod, "upload_json", fake_gcs.upload_json)
    monkeypatch.setattr(editorial_mod, "mark_artifact", lambda *a, **kw: None)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with config.override_settings(TEST_SETTINGS):
        result = editorial_mod.get_editorial(12345)

    assert result is not None
    assert result["headline"] == "Great game headline"
    assert result["body"] == "Full recap body text."
    assert result["game_id"] == 12345
    # Should have uploaded to GCS
    assert len(fake_gcs.upload_calls) == 1


def test_no_editorial_returns_none(monkeypatch):
    """When Forge DAPI returns empty items, return None (not an error)."""
    fake_gcs = _make_fake_gcs(exists=False)
    empty_index = {"items": []}
    fake_httpx = _make_httpx_mock(empty_index)

    monkeypatch.setattr(editorial_mod, "check_file_exists", fake_gcs.check_file_exists)
    monkeypatch.setattr(editorial_mod, "download_json", fake_gcs.download_json)
    monkeypatch.setattr(editorial_mod, "upload_json", fake_gcs.upload_json)
    monkeypatch.setattr(editorial_mod, "mark_artifact", lambda *a, **kw: None)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with config.override_settings(TEST_SETTINGS):
        result = editorial_mod.get_editorial(99999)

    assert result is None
    # Should NOT have uploaded anything (no data to cache)
    assert len(fake_gcs.upload_calls) == 0


def test_gcs_upload_failure_logs_warning_and_returns_data(monkeypatch):
    """GCS upload failure is a warning, not an exception; editorial is still returned."""
    fake_gcs = _make_fake_gcs(exists=False)

    def failing_upload(bucket, path, data):
        raise RuntimeError("GCS unavailable")

    fake_httpx = _make_httpx_mock(FORGE_INDEX_RESPONSE, FORGE_STORY_RESPONSE)

    monkeypatch.setattr(editorial_mod, "check_file_exists", fake_gcs.check_file_exists)
    monkeypatch.setattr(editorial_mod, "download_json", fake_gcs.download_json)
    monkeypatch.setattr(editorial_mod, "upload_json", failing_upload)
    monkeypatch.setattr(editorial_mod, "mark_artifact", lambda *a, **kw: None)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with config.override_settings(TEST_SETTINGS):
        result = editorial_mod.get_editorial(12345)

    # Data still returned despite GCS failure
    assert result is not None
    assert result["headline"] == "Great game headline"


def test_mark_artifact_called_with_raw_editorial(monkeypatch):
    """After a successful fetch, mark_artifact is called with artifact='raw_editorial'."""
    fake_gcs = _make_fake_gcs(exists=False)
    fake_httpx = _make_httpx_mock(FORGE_INDEX_RESPONSE, FORGE_STORY_RESPONSE)
    mark_calls = []

    def fake_mark(bucket, *, date, game_id, away, home, artifact, exists):
        mark_calls.append({"artifact": artifact, "game_id": game_id, "date": date})

    monkeypatch.setattr(editorial_mod, "check_file_exists", fake_gcs.check_file_exists)
    monkeypatch.setattr(editorial_mod, "download_json", fake_gcs.download_json)
    monkeypatch.setattr(editorial_mod, "upload_json", fake_gcs.upload_json)
    monkeypatch.setattr(editorial_mod, "mark_artifact", fake_mark)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with config.override_settings(TEST_SETTINGS):
        editorial_mod.get_editorial(12345, date="2025-04-25")

    assert any(c["artifact"] == "raw_editorial" for c in mark_calls)
    assert any(c["game_id"] == 12345 for c in mark_calls)


def test_force_refresh_bypasses_cache(monkeypatch):
    """force_refresh=True skips the GCS cache even when data is present."""
    fake_gcs = _make_fake_gcs(exists=True, cached_value=FAKE_EDITORIAL)
    fake_httpx = _make_httpx_mock(FORGE_INDEX_RESPONSE, FORGE_STORY_RESPONSE)

    monkeypatch.setattr(editorial_mod, "check_file_exists", fake_gcs.check_file_exists)
    monkeypatch.setattr(editorial_mod, "download_json", fake_gcs.download_json)
    monkeypatch.setattr(editorial_mod, "upload_json", fake_gcs.upload_json)
    monkeypatch.setattr(editorial_mod, "mark_artifact", lambda *a, **kw: None)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with config.override_settings(TEST_SETTINGS):
        result = editorial_mod.get_editorial(12345, force_refresh=True)

    # Should have hit Forge DAPI (freshly fetched body from story mock)
    assert result is not None
    assert result["body"] == "Full recap body text."


def test_extract_body_concatenates_markdown_parts():
    """_extract_body joins markdown parts and ignores non-markdown ones."""
    story = {
        "parts": [
            {"type": "markdown", "content": "Part one."},
            {"type": "image", "content": "ignored"},
            {"type": "markdown", "content": "Part two."},
        ]
    }
    body = editorial_mod._extract_body(story)
    assert "Part one." in body
    assert "Part two." in body
    assert "ignored" not in body


def test_extract_body_empty_parts():
    assert editorial_mod._extract_body({}) == ""
    assert editorial_mod._extract_body({"parts": []}) == ""
