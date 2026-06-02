import os
os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models.user import User
from app.models.market_account import MarketAccount
from app.api.auth import router as auth_router
from app.api.market_accounts import router as market_accounts_router


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(engine, checkfirst=True)
    MarketAccount.__table__.create(engine, checkfirst=True)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()

    test_app = FastAPI()
    test_app.include_router(auth_router)
    test_app.include_router(market_accounts_router)
    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser", "email": "test@example.com", "password": "test123456"
    })
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser", "password": "test123456"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_market_account(client, auth_headers):
    response = client.post("/api/v1/accounts", json={
        "market": "CN", "currency": "CNY", "initial_capital": 500000.0
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["market"] == "CN"
    assert data["currency"] == "CNY"
    assert data["current_capital"] == 500000.0


def test_get_market_accounts(client, auth_headers):
    client.post("/api/v1/accounts", json={
        "market": "CN", "currency": "CNY", "initial_capital": 500000.0
    }, headers=auth_headers)
    client.post("/api/v1/accounts", json={
        "market": "US", "currency": "USD", "initial_capital": 100000.0, "exchange_rate": 7.2
    }, headers=auth_headers)
    response = client.get("/api/v1/accounts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["accounts"]) == 2
    assert data["total_assets_cny"] > 0


def test_get_specific_market_account(client, auth_headers):
    client.post("/api/v1/accounts", json={
        "market": "CN", "currency": "CNY", "initial_capital": 500000.0
    }, headers=auth_headers)
    response = client.get("/api/v1/accounts/CN", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["market"] == "CN"
    assert data["current_capital"] == 500000.0


def test_get_nonexistent_market_account(client, auth_headers):
    response = client.get("/api/v1/accounts/US", headers=auth_headers)
    assert response.status_code == 404


def test_update_market_account(client, auth_headers):
    client.post("/api/v1/accounts", json={
        "market": "CN", "currency": "CNY", "initial_capital": 500000.0
    }, headers=auth_headers)
    response = client.put("/api/v1/accounts/CN", json={
        "current_capital": 600000.0
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["current_capital"] == 600000.0


def test_create_duplicate_market_account(client, auth_headers):
    client.post("/api/v1/accounts", json={
        "market": "CN", "currency": "CNY", "initial_capital": 500000.0
    }, headers=auth_headers)
    response = client.post("/api/v1/accounts", json={
        "market": "CN", "currency": "CNY", "initial_capital": 300000.0
    }, headers=auth_headers)
    assert response.status_code == 400


def test_unauthenticated_access(client):
    response = client.get("/api/v1/accounts")
    assert response.status_code == 401
