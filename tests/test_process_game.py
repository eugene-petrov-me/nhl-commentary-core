import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import types

fake_nhlpy = types.SimpleNamespace(NHLClient=lambda: types.SimpleNamespace())
sys.modules['nhlpy'] = fake_nhlpy

from engine.process_game import process_game_events


def test_process_game_events_adds_three_stars(monkeypatch):
    def fake_get_play_by_play(game_id):
        return {
            "plays": [],
            "rosterSpots": [
                {
                    "playerId": 1,
                    "firstName": {"default": "John"},
                    "lastName": {"default": "Doe"},
                }
            ],
        }

    def fake_get_game_story(game_id):
        return {"summary": {"threeStars": [{"star": 1, "playerId": 1}]}}

    monkeypatch.setattr("engine.process_game.get_play_by_play", fake_get_play_by_play)
    monkeypatch.setattr("engine.process_game.get_game_story", fake_get_game_story)

    events = process_game_events(123)
    assert {"event_type": "star", "star": 1, "players": {"player_id": 1, "name": "John Doe"}} in events
