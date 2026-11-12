import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_or_incomplete_secrets() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None, environment="production")


def test_production_accepts_private_tls_database_and_s3_configuration() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret_key="a-private-random-secret-value-with-at-least-32-chars",
        database_url="mysql+pymysql://smartledger:private-pass@db.example.net:4000/smartledger_db",
        database_ssl_ca="/etc/ssl/certs/ca-certificates.crt",
        frontend_origin="https://smartledger.example.com",
        document_storage_backend="s3",
        object_storage_endpoint_url="https://account-id.r2.cloudflarestorage.com",
        object_storage_bucket="smartledger-private-documents",
        object_storage_access_key="private-access-key-value",
        object_storage_secret_key="private-secret-key-value",
        object_storage_region="auto",
    )
    assert settings.environment == "production"
