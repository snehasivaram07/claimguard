
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging import logger


class S3ClientManager:
    """Manages the lifecycle and connection of the Boto3 S3 / MinIO client."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
        use_ssl: bool | None = None,
        bucket_name: str | None = None,
    ):
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.region = region or settings.S3_REGION
        self.use_ssl = use_ssl if use_ssl is not None else settings.S3_USE_SSL
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self._client = None

    def get_client(self):
        """Returns or initializes the thread-safe Boto3 S3 client."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                use_ssl=self.use_ssl,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            )
        return self._client

    def ensure_bucket_exists(self) -> bool:
        """Verifies or creates the application's default storage bucket."""
        client = self.get_client()
        try:
            client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            err_code = e.response.get("Error", {}).get("Code")
            if err_code in ("404", "NoSuchBucket"):
                try:
                    client.create_bucket(Bucket=self.bucket_name)
                    logger.info("Created S3 bucket: %s", self.bucket_name)
                    return True
                except Exception as create_err:
                    logger.error("Failed to create S3 bucket %s: %s", self.bucket_name, create_err)
                    return False
            logger.warning("Bucket head_bucket check note: %s", e)
            return False

    def check_health(self) -> bool:
        """Lightweight readiness probe verifying communication with S3 endpoint."""
        try:
            client = self.get_client()
            client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.warning("S3 health check failure: %s", e)
            return False


s3_manager = S3ClientManager()


def get_s3_client():
    return s3_manager.get_client()
