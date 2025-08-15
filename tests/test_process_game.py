import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

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
                    "teamId": 10,
                }
            ],
            "homeTeam": {"id": 10, "name": {"default": "Oilers"}, "abbrev": "EDM"},
            "awayTeam": {"id": 20, "name": {"default": "Stars"}, "abbrev": "DAL"},
        }

    def fake_get_game_story(game_id):
        return {
            "summary": {
                "threeStars": [
                    {
                        "star": 1,
                        "playerId": 1,
                        "position": "C",
                        "goals": 2,
                        "assists": 1,
                        "points": 3,
                        "teamAbbrev": "EDM",
                    }
                ]
            }
        }

    monkeypatch.setattr("engine.process_game.get_play_by_play", fake_get_play_by_play)
    monkeypatch.setattr("engine.process_game.get_game_story", fake_get_game_story)

    events = process_game_events(123)
    assert {
        "event_type": "star",
        "star": 1,
        "team_id": 10,
        "team_name": "Oilers",
        "players": {
            "player_id": 1,
            "name": "John Doe",
            "team_id": 10,
            "position": "C",
            "stats": {"goals": 2, "assists": 1, "points": 3},
        },
    } in events

def test_process_game_events_adds_goal_names(monkeypatch):
    def fake_get_play_by_play(game_id):
        return {
            "plays": [
                {
                    "typeDescKey": "goal",
                    "details": {
                        "scoringPlayerId": 1,
                        "assist1PlayerId": 2,
                        "assist2PlayerId": 3,
                        "goalieInNetId": 4,
                        "eventOwnerTeamId": 5,
                    },
                    "periodDescriptor": {"number": 1},
                    "timeInPeriod": "10:00",
                }
            ],
            "rosterSpots": [
                {"playerId": 1, "firstName": {"default": "John"}, "lastName": {"default": "Doe"}},
                {"playerId": 2, "firstName": {"default": "Jane"}, "lastName": {"default": "Smith"}},
                {"playerId": 3, "firstName": {"default": "Bob"}, "lastName": {"default": "Jones"}},
            ],
            "homeTeam": {"id": 5, "name": {"default": "Sharks"}, "abbrev": "SJS"},
            "awayTeam": {"id": 6, "name": {"default": "Kings"}, "abbrev": "LAK"},
        }

    def fake_get_game_story(game_id):
        return {"summary": {"threeStars": []}}

    monkeypatch.setattr("engine.process_game.get_play_by_play", fake_get_play_by_play)
    monkeypatch.setattr("engine.process_game.get_game_story", fake_get_game_story)

    events = process_game_events(456)
    goal_event = events[0]
    players = goal_event["players"]
    assert players["scorer_name"] == "John Doe"
    assert players["assist_names"] == ["Jane Smith", "Bob Jones"]
    assert goal_event["team_name"] == "Sharks"
