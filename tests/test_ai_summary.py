import openai
from engine.ai_summary import generate_ai_summary


def test_generate_ai_summary_includes_events(monkeypatch):
    events = [{"event_type": "goal", "team_name": "Flyers", "period": 1}]
    expected = "Summary text"

    def fake_create(*args, **kwargs):
        assert "messages" in kwargs
        content = "\n".join(m["content"] for m in kwargs["messages"])
        assert "goal" in content
        return {"choices": [{"message": {"content": expected}}]}

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)

    summary = generate_ai_summary(events)
    assert summary == expected
