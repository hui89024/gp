import pytest
from datetime import datetime, timedelta
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)


def test_hash_password():
    password = "test123456"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_wrong():
    password = "test123456"
    hashed = hash_password(password)
    assert not verify_password("wrong_password", hashed)


def test_create_access_token():
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)


def test_create_refresh_token():
    data = {"sub": "1", "username": "testuser"}
    token = create_refresh_token(data)
    assert token is not None
    assert isinstance(token, str)


def test_decode_token_valid():
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "testuser"


def test_decode_token_expired():
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    payload = decode_token(token)
    assert payload is None


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_user_model_with_auth(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("test123456"),
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(User).filter(User.username == "testuser").first()
    assert saved_user is not None
    assert saved_user.email == "test@example.com"
    assert verify_password("test123456", saved_user.password_hash)
