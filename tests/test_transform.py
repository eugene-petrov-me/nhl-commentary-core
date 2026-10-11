import os
import sys
import types

os.environ.setdefault("VERTEX_PROJECT", "test-project")

fake_nhlpy = types.SimpleNamespace(NHLClient=lambda: types.SimpleNamespace())
sys.modules["nhlpy"] = fake_nhlpy


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


fake_storage = types.SimpleNamespace(
    Client=_FakeStorageClient, Bucket=types.SimpleNamespace
)
fake_exceptions = types.SimpleNamespace(
    NotFound=Exception, GoogleAPIError=type("GoogleAPIError", (Exception,), {})
)
fake_genai_types = types.SimpleNamespace(GenerateContentConfig=types.SimpleNamespace)
fake_genai = types.SimpleNamespace(Client=types.SimpleNamespace, types=fake_genai_types)
fake_google_cloud = types.SimpleNamespace(storage=fake_storage)
fake_google_api_core = types.SimpleNamespace(exceptions=fake_exceptions)
sys.modules.setdefault(
    "google",
    types.SimpleNamespace(
        cloud=fake_google_cloud, api_core=fake_google_api_core, genai=fake_genai
    ),
)
sys.modules.setdefault("google.cloud", fake_google_cloud)
sys.modules.setdefault("google.cloud.storage", fake_storage)
sys.modules.setdefault("google.api_core", fake_google_api_core)
sys.modules.setdefault("google.api_core.exceptions", fake_exceptions)
sys.modules.setdefault("google.genai", fake_genai)
sys.modules.setdefault("google.genai.types", fake_genai_types)

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
