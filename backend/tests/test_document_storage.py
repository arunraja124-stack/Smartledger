from pathlib import Path
from types import SimpleNamespace

from app.services import document_storage


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, **kwargs):
        self.objects[kwargs["Key"]] = (kwargs["Body"], kwargs["ContentType"])

    def get_object(self, **kwargs):
        from io import BytesIO

        return {"Body": BytesIO(self.objects[kwargs["Key"]][0])}

    def delete_object(self, **kwargs):
        self.objects.pop(kwargs["Key"], None)


def test_s3_storage_round_trip_is_private_and_uses_object_key(monkeypatch, tmp_path: Path):
    settings = SimpleNamespace(document_storage_backend="s3", object_storage_bucket="private-bucket")
    fake = FakeS3()
    monkeypatch.setattr(document_storage, "get_settings", lambda: settings)
    monkeypatch.setattr(document_storage, "_s3_client", lambda: fake)
    local_path = tmp_path / "unused.png"

    document_storage.store_document("opaque-key.png", b"image bytes", local_path, "image/png")
    assert document_storage.read_document("opaque-key.png", local_path) == b"image bytes"
    assert not local_path.exists()
    document_storage.delete_document("opaque-key.png", local_path)
    assert fake.objects == {}


def test_local_storage_keeps_existing_file_workflow(monkeypatch, tmp_path: Path):
    settings = SimpleNamespace(document_storage_backend="local")
    monkeypatch.setattr(document_storage, "get_settings", lambda: settings)
    local_path = tmp_path / "uploads" / "image.png"

    document_storage.store_document("image.png", b"image bytes", local_path, "image/png")
    assert document_storage.read_document("image.png", local_path) == b"image bytes"
    document_storage.delete_document("image.png", local_path)
    assert not local_path.exists()
