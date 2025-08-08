import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.generate_summary import generate_summary


def test_generate_summary_team_breakdown():
    events = [
        {"event_type": "goal", "period": 1, "team_id": 1},
        {"event_type": "shot-on-goal", "period": 1, "team_id": 2},
        {"event_type": "penalty", "period": 2, "team_id": 1},
        {"event_type": "hit", "period": 2, "team_id": 2},
    ]

    summary = generate_summary(events)

    assert "Team Comparison" in summary
    assert "- Goals: 1 - 0" in summary
    assert "- Shots on goal: 1 - 1" in summary
    assert "- Penalties: 1 - 0" in summary
    assert "- Hits: 0 - 1" in summary


def test_generate_summary_player_info():
    events = [
        {
            "event_type": "goal",
            "period": 1,
            "team_id": 1,
            "players": {
                "scorer_id": 101,
                "scorer_name": "Player One",
                "assist_ids": [102, 103],
                "assist_names": ["Assist Two", "Assist Three"],
            },
        },
        {
            "event_type": "goal",
            "period": 2,
            "team_id": 2,
            "players": {"scorer_id": 201, "scorer_name": "Player Two", "assist_ids": []},
        },
        {
            "event_type": "goal",
            "period": 3,
            "team_id": 1,
            "players": {
                "scorer_id": 101,
                "scorer_name": "Player One",
                "assist_ids": [104],
                "assist_names": ["Assist Four"],
            },
        },

        {"event_type": "star", "star": 1, "players": {"player_id": 101, "name": "Player One"}},
        {"event_type": "star", "star": 2, "players": {"player_id": 201}},
        {"event_type": "star", "star": 3, "players": {"player_id": 102}},
    ]

    summary = generate_summary(events)

    assert "3 Stars of the Game" in summary
    assert "- Star 1: Player One" in summary
    assert "- Star 2: Player 201" in summary
    assert "Game-winning goal: Player One" in summary
    assert "Top goal scorers (2): Player One" in summary
    assert "Top point scorers (2): Player One" in summary

