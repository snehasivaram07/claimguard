import hashlib
import re
from pathlib import Path
from typing import Any, BinaryIO

from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging import logger
from app.storage.s3_client import get_s3_client


class HashingStreamWrapper:
    """Wraps a readable binary stream to incrementally compute SHA-256 and enforce size limits."""

    def __init__(self, stream: BinaryIO, max_size_bytes: int | None = None):
        self.stream = stream
        self.max_size_bytes = max_size_bytes
        self.hasher = hashlib.sha256()
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self.stream.read(size)
        if chunk:
            self.bytes_read += len(chunk)
            if self.max_size_bytes and self.bytes_read > self.max_size_bytes:
                raise ValueError(
                    f"Uploaded file exceeds maximum allowed size of {self.max_size_bytes} bytes"
                )
            self.hasher.update(chunk)
        return chunk

    @property
    def hexdigest(self) -> str:
        return self.hasher.hexdigest()


class StorageService:
    """S3-compatible object storage service handling streaming, hashing, and presigned access."""

    def __init__(self, client=None, bucket_name: str | None = None):
        self._client = client
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME

    @property
    def client(self):
        if self._client is None:
            self._client = get_s3_client()
        return self._client

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes user-supplied filename to prevent path traversal and shell injection."""
        # Normalize Windows backslashes and extract the base filename
        normalized = filename.replace("\\", "/")
        base_name = Path(normalized).name.strip()
        # Remove any null bytes or invalid characters
        clean_name = re.sub(r"[^\w\.\-]", "_", base_name)
        if not clean_name or set(clean_name) <= {".", "_"}:
            clean_name = "unnamed_document"
        return clean_name[:128]

    @classmethod
    def build_object_key(
        cls,
        owner_id: str,
        claim_id: str,
        document_id: str,
        original_filename: str,
    ) -> str:
        """Constructs non-guessable, strictly namespaced object key."""
        sanitized = cls.sanitize_filename(original_filename)
        return f"{owner_id}/{claim_id}/{document_id}/{sanitized}"

    def put_object_stream(
        self,
        stream: BinaryIO,
        object_key: str,
        content_type: str = "application/octet-stream",
        max_size_bytes: int | None = None,
    ) -> dict[str, Any]:
        """Streams raw bytes into object storage while calculating SHA-256 on the fly."""
        max_allowed = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES
        wrapped_stream = HashingStreamWrapper(stream, max_size_bytes=max_allowed)

        extra_args = {
            "ContentType": content_type,
        }

        # Upload without buffering entire payload in memory
        self.client.upload_fileobj(
            Fileobj=wrapped_stream,
            Bucket=self.bucket_name,
            Key=object_key,
            ExtraArgs=extra_args,
        )

        return {
            "object_key": object_key,
            "content_hash": wrapped_stream.hexdigest,
            "size_bytes": wrapped_stream.bytes_read,
        }

    def get_object_stream(self, object_key: str):
        """Retrieves object byte stream directly from S3."""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            return response["Body"]
        except ClientError as e:
            logger.error("Error retrieving object stream for %s: %s", object_key, e)
            raise

    def delete_object(self, object_key: str) -> bool:
        """Deletes an object from storage (used during compensation and cleanup)."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            logger.info("Successfully deleted object from storage: %s", object_key)
            return True
        except ClientError as e:
            logger.error("Failed to delete object %s: %s", object_key, e)
            return False

    def generate_presigned_download_url(
        self,
        object_key: str,
        original_filename: str | None = None,
        expires_in: int | None = None,
    ) -> str:
        """Generates a short-lived presigned download URL (default 5 minutes)."""
        expiry = expires_in or settings.PRESIGNED_URL_EXPIRE_SECONDS
        params = {
            "Bucket": self.bucket_name,
            "Key": object_key,
        }

        if original_filename:
            sanitized = self.sanitize_filename(original_filename)
            params["ResponseContentDisposition"] = f'attachment; filename="{sanitized}"'

        url = self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expiry,
        )
        return url


storage_service = StorageService()
