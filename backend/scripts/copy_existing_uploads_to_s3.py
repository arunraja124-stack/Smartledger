"""Copy local OCR uploads to the configured private S3-compatible bucket.

This script never changes database rows or deletes local files. It must only be
run after a private bucket has been created and the destination is approved.
"""

import sys
import hashlib
import mimetypes
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.database import SessionLocal
from app.models import DocumentUpload
from app.services.document_storage import DocumentStorageError, read_document, store_document
from app.services.documents import ALLOWED_EXTENSIONS, _upload_dir


def main() -> int:
    settings = get_settings()
    if settings.document_storage_backend != "s3":
        print("Set DOCUMENT_STORAGE_BACKEND=s3 and configure the private object bucket first.")
        return 2

    with SessionLocal() as db:
        documents = list(db.scalars(select(DocumentUpload).order_by(DocumentUpload.id)).all())

    upload_dir = _upload_dir()
    for document in documents:
        name = document.stored_filename
        if not name or name != Path(name).name:
            print("Copy stopped: a stored upload name is not a safe object key.")
            return 3
        local_path = upload_dir / name
        if not local_path.is_file():
            print("Copy stopped: one or more database-referenced local images are missing.")
            return 4

    local_files = sorted(
        path for path in upload_dir.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )
    if any(path.name != Path(path.name).name or path.suffix.lower() not in ALLOWED_EXTENSIONS for path in local_files):
        print("Copy stopped: local upload directory contains an unexpected file or object name.")
        return 6
    referenced_names = {document.stored_filename for document in documents}
    paths = [(path.name, path) for path in local_files]
    orphan_count = sum(name not in referenced_names for name, _ in paths)

    try:
        for name, local_path in paths:
            content = local_path.read_bytes()
            content_type = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
            store_document(name, content, local_path, content_type)
            copied_content = read_document(name, local_path)
            if hashlib.sha256(copied_content).digest() != hashlib.sha256(content).digest():
                raise DocumentStorageError("Object verification failed")
    except (OSError, DocumentStorageError):
        print("Copy failed while writing to object storage; local database and files were not changed.")
        return 5

    print(
        f"Copied {len(paths)} local images, including {orphan_count} without a database row. "
        "Local files and database rows were preserved."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
