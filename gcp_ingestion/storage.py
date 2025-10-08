import json
import logging
import os
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, Iterator, Optional

from google.api_core.exceptions import NotFound
from google.cloud import storage

logger = logging.getLogger(__name__)


def _make_client() -> storage.Client:
    """
    Prefer explicit SA JSON if GOOGLE_APPLICATION_CREDENTIALS is set and valid.
    Otherwise fall back to ADC (works locally after `gcloud auth application-default login`
    and in GCP runtimes like Cloud Run when a service account is attached).
    """
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.isfile(cred_path):
        return storage.Client.from_service_account_json(cred_path)
    return storage.Client()  # ADC


@lru_cache(maxsize=1)
def _cached_client() -> storage.Client:
    return _make_client()


_override_stack: list[storage.Client] = []


def get_storage_client() -> storage.Client:
    if _override_stack:
        return _override_stack[-1]
    return _cached_client()


def reset_storage_client() -> None:
    """Clear the cached client (useful when env vars change)."""
    _cached_client.cache_clear()


@contextmanager
def override_storage_client(client: storage.Client) -> Iterator[storage.Client]:
    _override_stack.append(client)
    try:
        yield client
    finally:
        if _override_stack:
            _override_stack.pop()


def _get_bucket(bucket_name: str, *, client: Optional[storage.Client] = None) -> storage.Bucket:
    return (client or get_storage_client()).bucket(bucket_name)

def check_file_exists(
    bucket_name: str, blob_name: str, *, client: Optional[storage.Client] = None
) -> bool:
    bucket = _get_bucket(bucket_name, client=client)
    blob = bucket.blob(blob_name)
    try:
        return blob.exists()
    except NotFound:
        return False

def download_json(
    bucket_name: str, blob_name: str, *, client: Optional[storage.Client] = None
) -> Dict[str, Any]:
    bucket = _get_bucket(bucket_name, client=client)
    blob = bucket.blob(blob_name)
    text = blob.download_as_text()  # raises if missing; let caller handle
    return json.loads(text)

def upload_json(
    bucket_name: str,
    blob_name: str,
    payload: Any,
    *,
    client: Optional[storage.Client] = None,
) -> None:
    bucket = _get_bucket(bucket_name, client=client)
    # Best practice: don't auto-create buckets here. Assume infra created outside.
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        data=json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    logger.info("Uploaded JSON to gs://%s/%s", bucket_name, blob_name)

def download_text(
    bucket_name: str, blob_name: str, *, client: Optional[storage.Client] = None
) -> str:
    bucket = _get_bucket(bucket_name, client=client)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()

def upload_text(
    bucket_name: str,
    blob_name: str,
    text: str,
    content_type: str = "text/plain",
    *,
    client: Optional[storage.Client] = None,
) -> None:
    bucket = _get_bucket(bucket_name, client=client)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data=text, content_type=content_type)
    logger.info("Uploaded text to gs://%s/%s", bucket_name, blob_name)
