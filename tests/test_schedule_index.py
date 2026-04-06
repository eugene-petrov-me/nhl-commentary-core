import config
from data_fetch import schedule


class DummyScheduleService:
    def __init__(self, payload):
        self._payload = payload

    def get_schedule(self, *, date):
        return self._payload


class DummyClient:
    def __init__(self, payload):
        self.schedule = DummyScheduleService(payload)


def test_get_schedule_seeds_index(monkeypatch):
    payload = {
        "games": [
            {
                "id": 1,
                "season": "20242025",
                "gameType": "R",
                "homeTeam": {"abbrev": "MTL", "score": 3},
                "awayTeam": {"abbrev": "COL", "score": 2},
                "winningGoalScorer": {"playerId": 42},
            }
        ]
    }

    calls = []

    def fake_mark(bucket, *, date, game_id, away=None, home=None, artifact, exists):
        calls.append((bucket, date, game_id, away, home, artifact, exists))

    monkeypatch.setattr(schedule, "mark_artifact", fake_mark)
    monkeypatch.setattr(schedule, "NHLClient", lambda: DummyClient(payload))

    with config.override_settings(config.Settings(gcs_bucket_name="bucket", openai_api_key="k", openai_model="gpt-4o-mini")):
        games = schedule.get_schedule("2025-04-25", mark_index=True)

    assert len(games) == 1
    assert calls  # raw_pbp and raw_story entries
    artifacts = {(artifact, exists) for _, _, _, _, _, artifact, exists in calls}
    assert ("raw_pbp", False) in artifacts
    assert ("raw_story", False) in artifacts
