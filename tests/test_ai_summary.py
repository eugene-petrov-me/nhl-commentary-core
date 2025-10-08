import sys, os, importlib
from types import SimpleNamespace

import pytest

# Ensure module can import without hitting the network
os.environ.setdefault("OPENAI_API_KEY", "test-key")

fake_nhlpy = SimpleNamespace(NHLClient=lambda: SimpleNamespace())
sys.modules['nhlpy'] = fake_nhlpy

class _FakeStorageClient:
    @classmethod
    def from_service_account_json(cls, *args, **kwargs):
        return cls()

    def bucket(self, *args, **kwargs):
        return SimpleNamespace(
            blob=lambda *a, **kw: SimpleNamespace(
                exists=lambda: False,
                download_as_text=lambda: "",
                upload_from_string=lambda *a, **kw: None,
            )
        )

fake_storage = SimpleNamespace(Client=_FakeStorageClient, Bucket=SimpleNamespace)
fake_exceptions = SimpleNamespace(NotFound=Exception)
fake_google_cloud = SimpleNamespace(storage=fake_storage)
fake_google_api_core = SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault("google", SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core))
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import engine.ai_summary


def test_generate_ai_summary_includes_payloads(monkeypatch):
    play_by_play = {"events": [{"event_type": "goal", "team_name": "Flyers"}]}
    game_story = {"stars": ["Player One"]}
    expected = "Summary text"

    def fake_create(*args, **kwargs):
        input_payload = kwargs["input"]
        assert "goal" in input_payload
        assert "Player One" in input_payload
        return SimpleNamespace(output_text=expected)

    monkeypatch.setattr(engine.ai_summary.client.responses, "create", fake_create)


    summary = engine.ai_summary.generate_ai_summary(play_by_play, game_story)
    assert summary == expected


def test_generate_ai_summary_handles_error(monkeypatch):
    play_by_play = {"events": []}
    game_story = {"stars": []}

    def fake_create(*args, **kwargs):
        raise Exception("boom")

    monkeypatch.setattr(engine.ai_summary.client.responses, "create", fake_create)

    with pytest.raises(RuntimeError, match="boom"):
        engine.ai_summary.generate_ai_summary(play_by_play, game_story)


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        importlib.reload(engine.ai_summary)

    # Restore for subsequent tests
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    importlib.reload(engine.ai_summary)
