import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.summarize_game import summarize_game


def test_summarize_game_rule_based(monkeypatch):
    def fake_process_game_events(game_id):
        assert game_id == 1
        return ["event"]

    def fake_generate_summary(events):
        assert events == ["event"]
        return "rule summary"

    def fake_generate_ai_summary(events):
        raise AssertionError("AI summary should not be called")

    monkeypatch.setattr("engine.summarize_game.process_game_events", fake_process_game_events)
    monkeypatch.setattr("engine.summarize_game.generate_summary", fake_generate_summary)
    monkeypatch.setattr("engine.summarize_game.generate_ai_summary", fake_generate_ai_summary)

    summary = summarize_game(1, use_ai=False)
    assert summary == "rule summary"


def test_summarize_game_ai(monkeypatch):
    def fake_process_game_events(game_id):
        assert game_id == 2
        return ["event"]

    def fake_generate_summary(events):
        raise AssertionError("Rule-based summary should not be called")

    def fake_generate_ai_summary(events):
        assert events == ["event"]
        return "ai summary"

    monkeypatch.setattr("engine.summarize_game.process_game_events", fake_process_game_events)
    monkeypatch.setattr("engine.summarize_game.generate_summary", fake_generate_summary)
    monkeypatch.setattr("engine.summarize_game.generate_ai_summary", fake_generate_ai_summary)

    summary = summarize_game(2, use_ai=True)
    assert summary == "ai summary"
