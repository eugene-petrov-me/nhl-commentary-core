"""Tests for engine.date_index index-read fallback."""

import pytest

from engine import date_index


class _FakeGoogleAPIError(Exception):
    """Stand-in for GoogleAPIError, independent of any sys.modules stubs."""


def _patch(monkeypatch, download_json, exists=True):
    monkeypatch.setattr(date_index, "GoogleAPIError", _FakeGoogleAPIError)
    monkeypatch.setattr(date_index, "check_file_exists", lambda *a, **kw: exists)
    monkeypatch.setattr(date_index, "download_json", download_json)


def test_load_returns_existing_index(monkeypatch):
    doc = {"date": "2025-04-25", "games": [{"game_id": 1}]}
    _patch(monkeypatch, lambda b, p: doc)

    assert date_index._load_date_index("bucket", "2025-04-25") == doc


def test_load_missing_index_returns_fresh(monkeypatch):
    def download_json(*a, **kw):  # pragma: no cover - should not be hit
        raise AssertionError("should not download a missing index")

    _patch(monkeypatch, download_json, exists=False)

    assert date_index._load_date_index("bucket", "2025-04-25") == {
        "date": "2025-04-25",
        "games": [],
    }


@pytest.mark.parametrize(
    "exc", [_FakeGoogleAPIError("gcs down"), ValueError("bad json")]
)
def test_load_unreadable_index_logs_warning_and_returns_fresh(monkeypatch, caplog, exc):
    def download_json(bucket, path):
        raise exc

    _patch(monkeypatch, download_json)

    with caplog.at_level("WARNING"):
        doc = date_index._load_date_index("bucket", "2025-04-25")

    assert doc == {"date": "2025-04-25", "games": []}
    assert "Unreadable date index for 2025-04-25" in caplog.text


def test_load_unexpected_error_raises(monkeypatch):
    def download_json(bucket, path):
        raise RuntimeError("bug")

    _patch(monkeypatch, download_json)

    with pytest.raises(RuntimeError, match="bug"):
        date_index._load_date_index("bucket", "2025-04-25")
