from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
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
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ]
    )

    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_REGISTER_PER_MINUTE: int = 3
    RATE_LIMIT_EXTRACT_PER_MINUTE: int = 10
    RATE_LIMIT_ANALYZE_PER_MINUTE: int = 10

    # Phase 2 & 3: Inference & Nemotron Models (Nebius Token Factory)
    INFERENCE_ENABLED: bool = False
    NEBIUS_API_KEY: SecretStr | None = None
    NEBIUS_BASE_URL: str = "https://api.tokenfactory.nebius.com/v1/"
    NEMOTRON_NANO_MODEL: str = "nvidia/nemotron-3-nano"
    NEMOTRON_SUPER_MODEL: str = "nvidia/nemotron-3-super"
    NEMOTRON_ULTRA_MODEL: str = "nvidia/nemotron-3-ultra"
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 3
    LLM_MAX_INPUT_CHARS: int = 32000
    LLM_MAX_CONCURRENCY: int = 5
    EXTRACTION_MAX_PAGES: int = 50
    EXTRACTION_MAX_TEXT_CHARS: int = 100000
    ALLOW_TIER_ESCALATION: bool = False

    # Phase 3: Multi-Document Claim Intelligence & Cross-Validation Bounds
    TIMELINE_MAX_EVENTS: int = 100
    CONTRADICTION_CONFIDENCE_THRESHOLD: float = 0.75
    CROSS_DOC_MAX_DOCUMENTS: int = 20

    # Phase 4: Graph Fraud Ring Detection & Network Traversal
    RATE_LIMIT_FRAUD_NETWORK_PER_MINUTE: int = 30
    FRAUD_RING_MIN_SHARED_ENTITIES: int = 2
    FRAUD_RING_MAX_HOPS: int = 2

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

        if self.INFERENCE_ENABLED and self.ENVIRONMENT not in ("development", "test"):
            if not self.NEBIUS_API_KEY or not self.NEBIUS_API_KEY.get_secret_value().strip():
                raise ValueError(
                    f"NEBIUS_API_KEY is required when INFERENCE_ENABLED is True in '{self.ENVIRONMENT}' environment."
                )
            if any(
                p in self.NEBIUS_API_KEY.get_secret_value().lower()
                for p in ["placeholder", "your_", "default", "dev_"]
            ):
                raise ValueError(
                    f"Insecure placeholder NEBIUS_API_KEY detected in '{self.ENVIRONMENT}' environment."
                )
            if not self.NEBIUS_BASE_URL or not self.NEBIUS_BASE_URL.strip():
                raise ValueError("NEBIUS_BASE_URL cannot be empty when INFERENCE_ENABLED is True.")
            if not self.NEMOTRON_NANO_MODEL or not self.NEMOTRON_NANO_MODEL.strip():
                raise ValueError(
                    "NEMOTRON_NANO_MODEL cannot be empty when INFERENCE_ENABLED is True."
                )

        return self


settings = Settings()
