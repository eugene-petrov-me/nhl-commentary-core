import pytest

from gcp_ingestion import (
    check_file_exists,
    download_json,
    download_text,
    override_storage_client,
    reset_storage_client,
    upload_json,
    upload_text,
)


class FakeBlob:
    def __init__(self, name: str, store: dict[str, dict]):
        self.name = name
        self._store = store
        self._meta = store.setdefault(name, {})

    def exists(self) -> bool:
        return "data" in self._meta

    def download_as_text(self) -> str:
        if "data" not in self._meta:
            raise FileNotFoundError(self.name)
        return self._meta["data"]

    def upload_from_string(self, *, data: str, content_type: str) -> None:
        self._meta["data"] = data
        self._meta["content_type"] = content_type


class FakeBucket:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(name, self._store)


class FakeClient:
    def __init__(self) -> None:
        self.buckets: dict[str, FakeBucket] = {}

    def bucket(self, name: str) -> FakeBucket:
        return self.buckets.setdefault(name, FakeBucket())


@pytest.fixture
def fake_client():
    client = FakeClient()
    with override_storage_client(client):
        yield client
    reset_storage_client()


def test_upload_and_download_json(fake_client):
    bucket = "bucket"
    blob = "path.json"

    upload_json(bucket, blob, {"hello": "world"})

    assert check_file_exists(bucket, blob)
    assert download_json(bucket, blob) == {"hello": "world"}


def test_upload_and_download_text(fake_client):
    bucket = "bucket"
    blob = "note.txt"

    upload_text(bucket, blob, "hi", content_type="text/plain")

    assert download_text(bucket, blob) == "hi"


def test_missing_blob_returns_false(fake_client):
    assert not check_file_exists("bucket", "missing.txt")
