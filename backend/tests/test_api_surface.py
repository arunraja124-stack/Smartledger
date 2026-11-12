import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Base


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_swagger_and_health_are_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/health").json()["status"] == "ok"


def test_protected_register_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/employees")

    assert response.status_code == 401


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        data={"username": "not-a-user@example.com", "password": "invalid-password"},
    )

    assert response.status_code == 401
