import json
import os
from typing import Any, Dict
from google.cloud import storage
from google.api_core.exceptions import NotFound

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

_client: storage.Client = _make_client()

def _get_bucket(bucket_name: str) -> storage.Bucket:
    return _client.bucket(bucket_name)

def check_file_exists(bucket_name: str, blob_name: str) -> bool:
    bucket = _get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        return blob.exists()
    except NotFound:
        return False

def download_json(bucket_name: str, blob_name: str) -> Dict[str, Any]:
    bucket = _get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    text = blob.download_as_text()  # raises if missing; let caller handle
    return json.loads(text)

def upload_json(bucket_name: str, blob_name: str, payload: Any) -> None:
    bucket = _get_bucket(bucket_name)
    # Best practice: don't auto-create buckets here. Assume infra created outside.
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        data=json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    print(f"✅ Uploaded JSON → gs://{bucket_name}/{blob_name}")

def download_text(bucket_name: str, blob_name: str) -> str:
    bucket = _get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()

def upload_text(bucket_name: str, blob_name: str, text: str, content_type: str = "text/plain") -> None:
    bucket = _get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data=text, content_type=content_type)
    print(f"✅ Uploaded text → gs://{bucket_name}/{blob_name}")