import openai
from openai.resources.responses import Responses

# Ensure OpenAI client can be instantiated during tests
os.environ["OPENAI_API_KEY"] = "test"

from engine.ai_summary import generate_ai_summary


def test_generate_ai_summary_includes_events(monkeypatch):
    events = [{"event_type": "goal", "team_name": "Flyers", "period": 1}]
    expected = "Summary text"

    def fake_create(self, *args, **kwargs):
        assert "input" in kwargs
        assert "goal" in kwargs["input"]

        class Response:
            output_text = expected

        return Response()

    monkeypatch.setattr(Responses, "create", fake_create)

    summary = generate_ai_summary(events)
    assert summary == expected
