import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models import Base, Employee, User


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            User(email="admin@example.com", full_name="Existing Admin", password_hash=hash_password("admin-password"), role="Admin", is_active=True),
            Employee(employee_code="KEEP-1", full_name="Existing Employee"),
        ])
        session.commit()

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_creates_staff_staff_login_and_admin_controls_account(client: TestClient) -> None:
    admin_headers = login(client, "ADMIN@example.com", "admin-password")
    created = client.post("/api/users", headers=admin_headers, json={
        "full_name": "New Staff", "email": "staff@example.com", "password": "staff-password", "role": "Staff",
    })
    assert created.status_code == 201
    staff = created.json()
    assert staff["role"] == "Staff"
    assert "password_hash" not in staff

    staff_headers = login(client, "staff@example.com", "staff-password")
    assert client.get("/api/auth/me", headers=staff_headers).json()["email"] == "staff@example.com"
    assert client.get("/api/employees", headers=staff_headers).status_code == 200
    assert client.get("/api/users", headers=staff_headers).status_code == 403
    assert client.get("/api/reports/attendance", headers=staff_headers).status_code == 403
    assert client.post("/api/users", headers=staff_headers, json={
        "full_name": "Escalated", "email": "escalated@example.com", "password": "staff-password", "role": "Admin",
    }).status_code == 403

    assert client.post("/api/users", headers=admin_headers, json={
        "full_name": "Duplicate", "email": "STAFF@example.com", "password": "staff-password", "role": "Staff",
    }).status_code == 409
    assert client.patch(f"/api/users/{staff['id']}", headers=admin_headers, json={"is_active": False}).status_code == 200
    assert client.post("/api/auth/login", data={"username": "staff@example.com", "password": "staff-password"}).status_code == 401
    assert client.patch(f"/api/users/{staff['id']}", headers=admin_headers, json={"is_active": True}).status_code == 200
    assert login(client, "staff@example.com", "staff-password")

    reset = client.post(f"/api/users/{staff['id']}/reset-password", headers=admin_headers, json={})
    assert reset.status_code == 200
    temporary_password = reset.json()["temporary_password"]
    assert login(client, "staff@example.com", temporary_password)
    assert client.post("/api/auth/login", data={"username": "staff@example.com", "password": "wrong-password"}).status_code == 401


def test_registration_disabled_and_final_admin_protected(client: TestClient) -> None:
    admin_headers = login(client, "admin@example.com", "admin-password")
    assert client.post("/api/auth/register", json={
        "full_name": "Self Signup", "email": "signup@example.com", "password": "some-password",
    }).status_code == 403
    admin_id = client.get("/api/auth/me", headers=admin_headers).json()["id"]
    response = client.patch(f"/api/users/{admin_id}", headers=admin_headers, json={"is_active": False})
    assert response.status_code == 400


def test_user_management_does_not_change_existing_business_records(client: TestClient) -> None:
    headers = login(client, "admin@example.com", "admin-password")
    before = client.get("/api/employees", headers=headers).json()["total"]
    created = client.post("/api/users", headers=headers, json={
        "full_name": "Staff", "email": "staff@example.com", "password": "staff-password",
    })
    assert created.status_code == 201
    after = client.get("/api/employees", headers=headers).json()["total"]
    assert after == before
