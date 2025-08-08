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

