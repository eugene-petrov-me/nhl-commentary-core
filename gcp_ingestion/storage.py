import os
from google.cloud import storage

def upload_to_gcs(bucket_name: str, source_file: str, destination_blob: str) -> None:
    """
    Upload a local file to a Google Cloud Storage bucket.
    
    Args:
        bucket_name (str): The name of the bucket.
        source_file (str): Path to the file to upload.
        destination_blob (str): Destination path in the bucket.
    """
    if not source_file or not os.path.isfile(source_file):
        raise FileNotFoundError(f"Source file does not exist: {source_file}")

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Check if bucket exists (no extra API calls if bucket is known)
    if not bucket.exists():
        print(f"Bucket {bucket_name} doesn't exist. Creating it.")
        client.create_bucket(bucket_name)
        print(f"Bucket {bucket_name} created.")

    blob = bucket.blob(destination_blob)

    try:
        blob.upload_from_filename(source_file)
        print(f"✅ Uploaded {source_file} → gs://{bucket_name}/{destination_blob}")
    except Exception as e:
        print(f"❌ Failed to upload {source_file} → {destination_blob}: {e}")
        raise
