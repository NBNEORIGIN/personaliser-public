from __future__ import annotations
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
import datetime as dt

from ..settings import settings

try:
    import boto3  # type: ignore
    from botocore.client import Config as BotoConfig  # type: ignore
except Exception:  # boto3 optional
    boto3 = None
    BotoConfig = None  # type: ignore


@dataclass
class PresignUpload:
    url: str
    fields: Optional[Dict[str, Any]] = None


class Storage:
    def presign_upload(self, key: str, content_type: str) -> PresignUpload:
        raise NotImplementedError

    def presign_get(self, key: str, expires_s: int) -> str:
        raise NotImplementedError

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError


class LocalStorage(Storage):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key

    def presign_upload(self, key: str, content_type: str) -> PresignUpload:
        # For local, just return a dummy URL; upload should be handled by server-side endpoint if needed.
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        return PresignUpload(url=f"/static/{key}")

    def presign_get(self, key: str, expires_s: int) -> str:
        return f"/static/{key}"

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3Storage(Storage):
    def __init__(self, *, bucket: str, region: Optional[str], endpoint_url: Optional[str], access_key: Optional[str], secret_key: Optional[str]) -> None:
        if boto3 is None:
            raise RuntimeError("boto3 is required for S3 storage")
        session = boto3.session.Session()
        self.client = session.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=BotoConfig(signature_version="s3v4") if BotoConfig else None,
        )
        self.bucket = bucket

    def presign_upload(self, key: str, content_type: str) -> PresignUpload:
        # Use POST policy for browser uploads
        conditions = [
            {"bucket": self.bucket},
            ["starts-with", "$key", key],
            {"Content-Type": content_type},
        ]
        fields = {"Content-Type": content_type}
        policy = self.client.generate_presigned_post(
            Bucket=self.bucket,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=settings.PRESIGN_EXPIRES_S,
        )
        return PresignUpload(url=policy["url"], fields=policy["fields"])

    def presign_get(self, key: str, expires_s: int) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_s,
        )

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


def get_storage() -> Storage:
    if settings.STORAGE_BACKEND.lower() == "s3":
        if not settings.S3_BUCKET:
            raise RuntimeError("S3_BUCKET must be set for S3 storage")
        return S3Storage(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key=settings.S3_ACCESS_KEY_ID,
            secret_key=settings.S3_SECRET_ACCESS_KEY,
        )
    return LocalStorage(settings.DATA_DIR)


def make_upload_key(prefix: str = "uploads") -> str:
    now = dt.datetime.utcnow()
    return f"{prefix}/{now:%Y}/{now:%m}/{now:%d}/{uuid4().hex}"


# Photo helpers
def put_photo_local(path_src: Path, dest_name: str) -> str:
    """Copy a local source photo into PHOTOS_DIR and return the static path."""
    dest = settings.PHOTOS_DIR / dest_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = path_src.read_bytes()
    dest.write_bytes(data)
    return f"/static/photos/{dest_name}"


def save_photo_local(path_src: Path, dest_name: str) -> str:
    """Alias for clarity: copy a local source photo into PHOTOS_DIR and return the static URL."""
    return put_photo_local(path_src, dest_name)


def upload_photo_and_presign(path_src: Path, dest_name: str) -> str:
    """Upload photo to storage (S3) and return a presigned URL for GET."""
    storage = get_storage()
    key = f"photos/{dest_name}"
    # naive content-type inference
    ext = path_src.suffix.lower()
    ctype = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(ext, "application/octet-stream")
    storage.put_bytes(key, path_src.read_bytes(), content_type=ctype)
    return storage.presign_get(key, expires_s=settings.PRESIGN_EXPIRES_S)


def put_artifact(job_id: str, path: Path) -> str:
    """Store an artifact file under jobs/<job_id>/ and return a URL or static path.

    Picks content-type by file suffix. Uses the configured storage backend.
    """
    storage = get_storage()
    name = path.name
    key = f"jobs/{job_id}/{name}"
    # naive content-type inference
    ext = path.suffix.lower()
    ctype = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".csv": "text/csv",
        ".json": "application/json",
    }.get(ext, "application/octet-stream")
    storage.put_bytes(key, path.read_bytes(), content_type=ctype)
    if settings.STORAGE_BACKEND.lower() == "s3":
        return storage.presign_get(key, settings.PRESIGN_EXPIRES_S)
    return f"/static/{key}"
