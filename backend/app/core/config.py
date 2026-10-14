from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL Database
    POSTGRES_USER: str = "claimguard"
    POSTGRES_PASSWORD: str = "claimguard_dev_password"
    POSTGRES_DB: str = "claimguard"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = (
        "postgresql+asyncpg://claimguard:claimguard_dev_password@localhost:5432/claimguard"
    )

    # FalkorDB
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_PASSWORD: str = ""
    FALKORDB_GRAPH_NAME: str = "claimguard"

    # S3 / MinIO Object Storage
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_BUCKET_NAME: str = "claimguard-documents"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    PRESIGNED_URL_EXPIRE_SECONDS: int = 300

    # Security & JWT
    JWT_SECRET_KEY: str = "dev_jwt_secret_key_minimum_32_characters_long_for_security"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Upload Constraints
    MAX_UPLOAD_SIZE_BYTES: int = 26214400  # 25 MB
    ALLOWED_MIME_TYPES: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "text/plain",
            "message/rfc822",
        ]
    )

    # Cross-Origin Resource Sharing
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )

    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_REGISTER_PER_MINUTE: int = 3

    @field_validator("ALLOWED_MIME_TYPES", "CORS_ORIGINS", mode="before")
    @classmethod
    def parse_comma_separated_or_json(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Fail fast if critical default/placeholder secrets are used outside dev/test environments."""
        if self.ENVIRONMENT not in ("development", "test"):
            placeholder_indicators = [
                "dev_",
                "placeholder",
                "your_",
                "default",
                "claimguard_dev_password",
                "minioadmin",
            ]
            # JWT secret validation
            if len(self.JWT_SECRET_KEY) < 32 or any(
                p in self.JWT_SECRET_KEY.lower() for p in placeholder_indicators
            ):
                raise ValueError(
                    f"Insecure JWT_SECRET_KEY detected for environment '{self.ENVIRONMENT}'. "
                    "A cryptographically strong secret of at least 32 characters is required."
                )

            # Postgres password validation
            if any(p in self.POSTGRES_PASSWORD.lower() for p in placeholder_indicators):
                raise ValueError(
                    f"Insecure POSTGRES_PASSWORD detected for environment '{self.ENVIRONMENT}'. "
                    "Production requires a dedicated secure password."
                )

            # S3 secret validation
            if any(p in self.S3_SECRET_KEY.lower() for p in placeholder_indicators):
                raise ValueError(
                    f"Insecure S3_SECRET_KEY detected for environment '{self.ENVIRONMENT}'."
                )

        return self


settings = Settings()
