import sys, os, importlib
from types import SimpleNamespace

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Ensure module can import without hitting the network
os.environ.setdefault("OPENAI_API_KEY", "test-key")

import engine.ai_summary as ai_summary


def test_generate_ai_summary_includes_events(monkeypatch):
    events = [{"event_type": "goal", "team_name": "Flyers", "period": 1}]
    expected = "Summary text"

    def fake_create(*args, **kwargs):
        assert "goal" in kwargs["input"]
        return SimpleNamespace(output_text=expected)

    monkeypatch.setattr(ai_summary.client.responses, "create", fake_create)

    summary = ai_summary.generate_ai_summary(events)
    assert summary == expected


def test_generate_ai_summary_handles_error(monkeypatch):
    events = [{"event_type": "goal"}]

    def fake_create(*args, **kwargs):
        raise Exception("boom")

    monkeypatch.setattr(ai_summary.client.responses, "create", fake_create)

    with pytest.raises(RuntimeError, match="boom"):
        ai_summary.generate_ai_summary(events)


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        importlib.reload(ai_summary)

    # Restore for subsequent tests
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    importlib.reload(ai_summary)

