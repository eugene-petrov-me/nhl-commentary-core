"""Tests for engine.summaries date-index marking."""

import pytest

import engine.date_index
from engine import summaries


class _FakeGoogleAPIError(Exception):
    """Stand-in for GoogleAPIError, independent of any sys.modules stubs."""


def _patch_mark(monkeypatch, mark):
    monkeypatch.setattr(summaries, "GoogleAPIError", _FakeGoogleAPIError)
    monkeypatch.setattr(engine.date_index, "mark_artifact", mark)


def test_mark_calls_mark_artifact(monkeypatch):
    calls = []
    _patch_mark(monkeypatch, lambda bucket, **kw: calls.append((bucket, kw)))

    summaries._mark("summary_ai", bucket="b", date="2025-04-25", game_id=1)

    assert calls == [
        (
            "b",
            {
                "date": "2025-04-25",
                "game_id": 1,
                "artifact": "summary_ai",
                "exists": True,
            },
        )
    ]


def test_mark_without_date_is_noop(monkeypatch):
    def mark(*a, **kw):  # pragma: no cover - should not be hit
        raise AssertionError("should not mark without a date")

    _patch_mark(monkeypatch, mark)

    summaries._mark("summary_ai", bucket="b", date=None, game_id=1)


def test_mark_gcs_error_logs_warning(monkeypatch, caplog):
    def mark(*a, **kw):
        raise _FakeGoogleAPIError("gcs down")

    _patch_mark(monkeypatch, mark)

    with caplog.at_level("WARNING"):
        summaries._mark("summary_ai", bucket="b", date="2025-04-25", game_id=1)

    assert "Failed to mark summary_ai index for game 1 on 2025-04-25" in caplog.text


def test_mark_unexpected_error_raises(monkeypatch):
    def mark(*a, **kw):
        raise RuntimeError("bug")

    _patch_mark(monkeypatch, mark)

    with pytest.raises(RuntimeError, match="bug"):
        summaries._mark("summary_ai", bucket="b", date="2025-04-25", game_id=1)
