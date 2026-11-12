from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    app_name: str = "SmartLedger API"
    environment: str = "development"
    database_url: str = "mysql+pymysql://smartledger_user@localhost:3306/smartledger_db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_recycle_seconds: int = 1800
    jwt_secret_key: str = "development-only-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    upload_dir: str = "backend/uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    frontend_origin: str = "http://localhost:5173"
    database_ssl_ca: str | None = None
    document_storage_backend: Literal["local", "s3"] = "local"
    object_storage_endpoint_url: str | None = None
    object_storage_bucket: str | None = None
    object_storage_access_key: str | None = None
    object_storage_secret_key: str | None = None
    object_storage_region: str = "auto"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.environment.strip().lower() != "production":
            return self

        problems = []
        secret = self.jwt_secret_key.strip()
        if len(secret) < 32 or any(
            marker in secret.lower()
            for marker in ("development-only", "replace", "placeholder", "change-me", "your-")
        ):
            problems.append("JWT_SECRET_KEY must be a private random value of at least 32 characters")

        database = make_url(self.database_url)
        if database.host in {None, "localhost", "127.0.0.1", "::1"} or not database.password:
            problems.append("DATABASE_URL must identify a remote database and include credentials")
        elif any(marker in database.password.lower() for marker in ("placeholder", "password", "change-me", "replace", "<", ">")):
            problems.append("DATABASE_URL must not contain placeholder credentials")
        if not self.database_ssl_ca:
            problems.append("DATABASE_SSL_CA must point to the trusted database CA bundle")

        frontend = urlsplit(self.frontend_origin)
        if frontend.scheme != "https" or not frontend.hostname or frontend.path not in {"", "/"} or frontend.query or frontend.fragment or frontend.username:
            problems.append("FRONTEND_ORIGIN must be an HTTPS origin")

        if self.document_storage_backend != "s3":
            problems.append("DOCUMENT_STORAGE_BACKEND must be s3 in production")
        endpoint = urlsplit(self.object_storage_endpoint_url or "")
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.path not in {"", "/"} or endpoint.query or endpoint.fragment or "<" in (self.object_storage_endpoint_url or "") or ">" in (self.object_storage_endpoint_url or ""):
            problems.append("OBJECT_STORAGE_ENDPOINT_URL must be an HTTPS S3-compatible endpoint")
        storage_values = (
            self.object_storage_bucket,
            self.object_storage_access_key,
            self.object_storage_secret_key,
            self.object_storage_region,
        )
        if not all(storage_values) or any(
            any(marker in value.lower() for marker in ("placeholder", "change-me", "replace-with", "your-", "<", ">"))
            for value in storage_values
            if value
        ):
            problems.append("S3-compatible object storage bucket and credentials are required in production")

        if problems:
            raise ValueError("Invalid production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
