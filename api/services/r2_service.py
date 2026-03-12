"""
Cloudflare R2 Upload Service for Spectra AI.

Uploads rendered video files to Cloudflare R2 so they have
publicly accessible URLs — required by Instagram/Meta APIs.
"""

import os
import uuid
import mimetypes
import boto3
from botocore.config import Config

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "ads")
R2_PUBLIC_URL_PREFIX = os.getenv(
    "R2_PUBLIC_URL_PREFIX",
    "https://pub-9fe2ddd08fba47c690b74358bf173d97.r2.dev",
)

_client = None


def _get_s3_client():
    """Lazy-init a boto3 S3 client pointed at Cloudflare R2."""
    global _client
    if _client is not None:
        return _client

    if not R2_ACCOUNT_ID or not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        raise RuntimeError(
            "R2 credentials not configured. "
            "Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in .env"
        )

    _client = boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    return _client


def upload_video_to_r2(local_path: str, campaign_id: str = "") -> str:
    """
    Upload a local video file to Cloudflare R2.

    Returns the public URL of the uploaded file.
    Raises FileNotFoundError if local_path doesn't exist.
    """
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Video file not found: {local_path}")

    client = _get_s3_client()

    ext = os.path.splitext(local_path)[1] or ".mp4"
    content_type = mimetypes.guess_type(local_path)[0] or "video/mp4"

    # Build a unique key: videos/<campaign_id>/<uuid>.<ext>
    unique_name = f"{uuid.uuid4().hex}{ext}"
    if campaign_id:
        key = f"videos/{campaign_id}/{unique_name}"
    else:
        key = f"videos/{unique_name}"

    client.upload_file(
        Filename=local_path,
        Bucket=R2_BUCKET_NAME,
        Key=key,
        ExtraArgs={"ContentType": content_type},
    )

    public_url = f"{R2_PUBLIC_URL_PREFIX.rstrip('/')}/{key}"
    return public_url


def upload_file_to_r2(local_path: str, folder: str = "assets") -> str:
    """
    Generic file upload to R2.  Returns public URL.
    """
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")

    client = _get_s3_client()

    ext = os.path.splitext(local_path)[1]
    content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    key = f"{folder}/{unique_name}"

    client.upload_file(
        Filename=local_path,
        Bucket=R2_BUCKET_NAME,
        Key=key,
        ExtraArgs={"ContentType": content_type},
    )

    return f"{R2_PUBLIC_URL_PREFIX.rstrip('/')}/{key}"
