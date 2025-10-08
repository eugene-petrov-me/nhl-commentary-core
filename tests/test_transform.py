import sys, os, types

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

fake_nhlpy = types.SimpleNamespace(NHLClient=lambda: types.SimpleNamespace())
sys.modules['nhlpy'] = fake_nhlpy

class _FakeStorageClient:
    @classmethod
    def from_service_account_json(cls, *args, **kwargs):
        return cls()

    def bucket(self, *args, **kwargs):
        return types.SimpleNamespace(
            blob=lambda *a, **kw: types.SimpleNamespace(
                exists=lambda: False,
                download_as_text=lambda: "",
                upload_from_string=lambda *a, **kw: None,
            )
        )

fake_storage = types.SimpleNamespace(Client=_FakeStorageClient, Bucket=types.SimpleNamespace)
fake_exceptions = types.SimpleNamespace(NotFound=Exception)
fake_google_cloud = types.SimpleNamespace(storage=fake_storage)
fake_google_api_core = types.SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault("google", types.SimpleNamespace(cloud=fake_google_cloud, api_core=fake_google_api_core))
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)

import engine.transform


def test_transform_handles_missing_type_desc_key():
    """A missing typeDescKey should result in an unknown event instead of errors."""
    event = {
        # No 'typeDescKey' field
        "details": {},
    }
    result = engine.transform.transform_event(event)
    assert result["event_type"] == "unknown"
    assert result["raw_data"] == event
