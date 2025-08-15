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
    assert "- Team 1: G 1, SOG 1, PIM 1" in summary
    assert "- Team 2: G 0, SOG 1, PIM 0" in summary


def test_generate_summary_player_info():
    events = [
        {
            "event_type": "goal",
            "period": 1,
            "team_id": 1,
            "team_name": "Flyers",
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
            "team_name": "Penguins",
            "players": {"scorer_id": 201, "scorer_name": "Player Two", "assist_ids": []},
        },
        {
            "event_type": "goal",
            "period": 3,
            "team_id": 1,
            "team_name": "Flyers",
            "players": {
                "scorer_id": 101,
                "scorer_name": "Player One",
                "assist_ids": [104],
                "assist_names": ["Assist Four"],
            },
        },

        {
            "event_type": "star",
            "star": 1,
            "team_id": 1,
            "team_name": "Flyers",
            "players": {
                "player_id": 101,
                "name": "Player One",
                "team_id": 1,
                "position": "C",
                "stats": {"goals": 2, "assists": 0, "points": 2},
            },
        },
        {
            "event_type": "star",
            "star": 2,
            "team_id": 2,
            "team_name": "Penguins",
            "players": {
                "player_id": 201,
                "name": "Player Two",
                "team_id": 2,
                "position": "G",
                "stats": {"goalsAgainstAverage": 1.0, "savePctg": 0.95},
            },
        },
        {
            "event_type": "star",
            "star": 3,
            "team_id": 1,
            "team_name": "Flyers",
            "players": {
                "player_id": 102,
                "name": "Assist Two",
                "team_id": 1,
                "position": "D",
                "stats": {"goals": 0, "assists": 1, "points": 1},
            },
        },
    ]

    summary = generate_summary(events)

    assert "3 Stars of the Game" in summary
    assert "- Star 1: Player One (C) - Goals: 2, Assists: 0, Points: 2" in summary
    assert "- Star 2: Player Two (G) - GAA: 1.0, SV%: 0.95" in summary
    assert "- Star 3: Assist Two (D) - Goals: 0, Assists: 1, Points: 1" in summary
    assert "Top goal scorers (2): Player One" in summary
    assert "Top point scorers (2 pts): Player One" in summary

