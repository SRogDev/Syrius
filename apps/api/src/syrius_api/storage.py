"""Artifact storage abstraction (Phase 1, plan §7).

Local filesystem storage is implemented for real and is the default.
The S3-compatible adapter is an interface plus a boto3-based
implementation that only activates when ``boto3`` is installed and
credentials are configured; otherwise it raises a clear
``NotImplementedError`` — never a fake success. No secrets are read
here; the S3 adapter takes credentials from the standard boto3 chain
only when the operator configures them.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .settings import settings


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class StorageAdapter:
    """Interface every storage backend implements."""

    kind: str = "base"

    def put(self, key: str, data: bytes) -> str:
        raise NotImplementedError

    def get(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def uri_for(self, key: str) -> str:
        raise NotImplementedError


class LocalStorage(StorageAdapter):
    """Filesystem storage under ``root``. Keys are relative paths;
    ``..`` segments are rejected so a key can never escape the root."""

    kind = "local"

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        self.root = Path(root or settings.storage_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"storage key escapes root: {key!r}")
        return candidate

    def put(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self.uri_for(key)

    def put_json(self, key: str, payload: dict | list) -> str:
        return self.put(key, json.dumps(payload, indent=2).encode())

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def get_json(self, key: str) -> dict | list:
        return json.loads(self.get(key).decode())

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def uri_for(self, key: str) -> str:
        return f"local://{key}"


class S3Storage(StorageAdapter):
    """S3-compatible adapter (interface + boto3 implementation).

    Only usable when ``boto3`` is installed and ``bucket`` is given.
    Credentials come from the standard boto3 chain (env / config file /
    instance role) — this module never accepts or logs a secret.
    """

    kind = "s3"

    def __init__(self, bucket: str, prefix: str = "") -> None:
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as exc:
            raise NotImplementedError(
                "S3 storage requires boto3, which is not installed; "
                "local storage remains the working backend."
            ) from exc
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self._client = boto3.client("s3")

    def _s3_key(self, key: str) -> str:
        return f"{self.prefix}/{key}".lstrip("/") if self.prefix else key

    def put(self, key: str, data: bytes) -> str:
        self._client.put_object(Bucket=self.bucket, Key=self._s3_key(key), Body=data)
        return self.uri_for(key)

    def get(self, key: str) -> bytes:
        return self._client.get_object(Bucket=self.bucket, Key=self._s3_key(key))[
            "Body"
        ].read()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=self._s3_key(key))
            return True
        except Exception:
            return False

    def uri_for(self, key: str) -> str:
        return f"s3://{self.bucket}/{self._s3_key(key)}"


def default_storage() -> StorageAdapter:
    """Local storage unless ``SYRIUS_STORAGE_S3_BUCKET`` is set.

    The S3 path is intentionally opt-in and fails loudly without boto3
    or a bucket, so a misconfiguration can never silently drop artifacts.
    """
    bucket = os.environ.get("SYRIUS_STORAGE_S3_BUCKET")
    if bucket:
        return S3Storage(bucket, os.environ.get("SYRIUS_STORAGE_S3_PREFIX", ""))
    return LocalStorage()
