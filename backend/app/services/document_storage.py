from pathlib import Path

from app.core.config import get_settings


class DocumentStorageError(Exception):
    """Raised when the configured document storage cannot complete an operation."""


def _s3_client():
    settings = get_settings()
    try:
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=settings.object_storage_endpoint_url,
            aws_access_key_id=settings.object_storage_access_key,
            aws_secret_access_key=settings.object_storage_secret_key,
            region_name=settings.object_storage_region,
        )
    except Exception as error:
        raise DocumentStorageError("Object storage client is unavailable") from error


def store_document(key: str, content: bytes, local_path: Path, content_type: str) -> None:
    settings = get_settings()
    if settings.document_storage_backend == "s3":
        try:
            _s3_client().put_object(
                Bucket=settings.object_storage_bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        except Exception as error:
            raise DocumentStorageError("Object storage upload failed") from error
        return

    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
    except OSError as error:
        raise DocumentStorageError("Local document storage write failed") from error


def read_document(key: str, local_path: Path) -> bytes:
    settings = get_settings()
    if settings.document_storage_backend == "s3":
        try:
            response = _s3_client().get_object(Bucket=settings.object_storage_bucket, Key=key)
            return response["Body"].read()
        except Exception as error:
            raise DocumentStorageError("Object storage read failed") from error

    try:
        return local_path.read_bytes()
    except OSError as error:
        raise DocumentStorageError("Local document storage read failed") from error


def delete_document(key: str, local_path: Path) -> None:
    settings = get_settings()
    if settings.document_storage_backend == "s3":
        try:
            _s3_client().delete_object(Bucket=settings.object_storage_bucket, Key=key)
        except Exception as error:
            raise DocumentStorageError("Object storage delete failed") from error
        return

    try:
        local_path.unlink(missing_ok=True)
    except OSError as error:
        raise DocumentStorageError("Local document storage delete failed") from error
