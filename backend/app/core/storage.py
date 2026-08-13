import boto3
from botocore.client import Config

from app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket_exists() -> None:
    client = get_s3_client()
    existing = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    if settings.minio_bucket not in existing:
        client.create_bucket(Bucket=settings.minio_bucket)


def upload_file(key: str, data: bytes, content_type: str) -> str:
    """Upload file lên MinIO, trả về object key để lưu vào Job.jd_file_path."""
    client = get_s3_client()
    ensure_bucket_exists()
    client.put_object(Bucket=settings.minio_bucket, Key=key, Body=data, ContentType=content_type)
    return key