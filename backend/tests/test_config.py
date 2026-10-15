import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_inference_disabled():
    """Verify that by default, inference is disabled and starts with no external key requirement."""
    cfg = Settings(ENVIRONMENT="development")
    assert cfg.INFERENCE_ENABLED is False
    assert cfg.NEBIUS_BASE_URL == "https://api.tokenfactory.nebius.com/v1/"
    assert cfg.NEMOTRON_NANO_MODEL == "nvidia/nemotron-3-nano"
    assert cfg.NEMOTRON_SUPER_MODEL == "nvidia/nemotron-3-super"
    assert cfg.NEMOTRON_ULTRA_MODEL == "nvidia/nemotron-3-ultra"
    assert cfg.ALLOW_TIER_ESCALATION is False


def test_production_fails_fast_when_inference_enabled_without_key():
    """Verify that in production, enabling inference without a valid API key raises ValueError."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a_very_secure_random_production_jwt_key_32_chars!",
            POSTGRES_PASSWORD="secure_prod_db_password_12345!",
            S3_SECRET_KEY="secure_prod_s3_secret_12345!",
            INFERENCE_ENABLED=True,
            NEBIUS_API_KEY=None,
        )
    assert "NEBIUS_API_KEY is required" in str(exc_info.value)


def test_production_fails_fast_with_placeholder_key():
    """Verify that in production, placeholder API keys fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a_very_secure_random_production_jwt_key_32_chars!",
            POSTGRES_PASSWORD="secure_prod_db_password_12345!",
            S3_SECRET_KEY="secure_prod_s3_secret_12345!",
            INFERENCE_ENABLED=True,
            NEBIUS_API_KEY="your_nebius_api_key_placeholder",
        )
    assert "Insecure placeholder NEBIUS_API_KEY detected" in str(exc_info.value)


def test_production_fails_fast_with_empty_model_or_url():
    """Verify that empty base URL or model IDs fail fast when inference is enabled."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a_very_secure_random_production_jwt_key_32_chars!",
            POSTGRES_PASSWORD="secure_prod_db_password_12345!",
            S3_SECRET_KEY="secure_prod_s3_secret_12345!",
            INFERENCE_ENABLED=True,
            NEBIUS_API_KEY="real-prod-nebius-key-1234567890",
            NEBIUS_BASE_URL="",
        )
    assert "NEBIUS_BASE_URL cannot be empty" in str(exc_info.value)


def test_production_succeeds_with_valid_config():
    """Verify that production initializes cleanly when all required parameters are provided."""
    cfg = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a_very_secure_random_production_jwt_key_32_chars!",
        POSTGRES_PASSWORD="secure_prod_db_password_12345!",
        S3_SECRET_KEY="secure_prod_s3_secret_12345!",
        INFERENCE_ENABLED=True,
        NEBIUS_API_KEY="valid-secret-token-abcdef123456",
        NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1/",
        NEMOTRON_NANO_MODEL="nvidia/nemotron-3-nano",
    )
    assert cfg.INFERENCE_ENABLED is True
    assert cfg.NEBIUS_API_KEY.get_secret_value() == "valid-secret-token-abcdef123456"
