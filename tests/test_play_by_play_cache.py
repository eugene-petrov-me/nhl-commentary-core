import config
from data_fetch import play_by_play


def test_get_play_by_play_uses_cache(monkeypatch):
    called = {"client": False}

    def fake_client():  # pragma: no cover - should not be hit
        called["client"] = True
        raise AssertionError("Client should not be instantiated when cache is hit")

    monkeypatch.setattr(play_by_play, "NHLClient", fake_client)
    monkeypatch.setattr(play_by_play, "check_file_exists", lambda *args, **kwargs: True)
    monkeypatch.setattr(play_by_play, "download_json", lambda *args, **kwargs: {"plays": []})
    monkeypatch.setattr(
        play_by_play,
        "upload_json",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Should not upload on cache hit")),
    )

    with config.override_settings(config.Settings(gcs_bucket_name="test-bucket")):
        payload = play_by_play.get_play_by_play(123, mark_index=False)

    assert payload == {"plays": []}
    assert not called["client"]


def test_get_play_by_play_marks_index(monkeypatch):
    calls = []

    def fake_mark(bucket, *, date, game_id, away=None, home=None, artifact, exists):
        calls.append((bucket, date, game_id, away, home, artifact, exists))

    class DummyGameCenter:
        def play_by_play(self, game_id):
            return {
                "plays": [],
                "gameDate": "2025-04-25T23:00:00Z",
                "awayTeam": {"abbrev": "COL"},
                "homeTeam": {"abbrev": "MTL"},
            }

    class DummyClient:
        def __init__(self):
            self.game_center = DummyGameCenter()

    monkeypatch.setattr(play_by_play, "mark_artifact", fake_mark)
    monkeypatch.setattr(play_by_play, "NHLClient", DummyClient)
    monkeypatch.setattr(play_by_play, "check_file_exists", lambda *args, **kwargs: False)
    monkeypatch.setattr(play_by_play, "upload_json", lambda *args, **kwargs: None)

    with config.override_settings(config.Settings(gcs_bucket_name="bucket")):
        play_by_play.get_play_by_play(456, mark_index=True)

    assert calls
    bucket, date, game_id, away, home, artifact, exists = calls[-1]
    assert bucket == "bucket"
    assert date == "2025-04-25"
    assert game_id == 456
    assert away == "COL"
    assert home == "MTL"
    assert artifact == "raw_pbp"
    assert exists is True
