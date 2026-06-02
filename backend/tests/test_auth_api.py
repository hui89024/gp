import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.api.deps import get_db


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


def test_register(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password" not in data


def test_login(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "test123456"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "wrong_password"
    })
    assert response.status_code == 401


def test_get_current_user(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })
    login_response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "test123456"
    })
    token = login_response.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_register_duplicate_username(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test1@example.com",
        "password": "test123456"
    })
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test2@example.com",
        "password": "test123456"
    })
    assert response.status_code == 400


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser1",
        "email": "test@example.com",
        "password": "test123456"
    })
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser2",
        "email": "test@example.com",
        "password": "test123456"
    })
    assert response.status_code == 400


def test_refresh_token(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })
    login_response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "test123456"
    })
    refresh_token = login_response.json()["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
