import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.market_account import MarketAccount


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine, checkfirst=True)
    MarketAccount.__table__.create(engine, checkfirst=True)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_create_market_account(db_session):
    user = User(
        username="testuser", email="test@example.com",
        password_hash="hashed_password",
        initial_capital=1000000.0, current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    cn_account = MarketAccount(
        user_id=user.id, market="CN", currency="CNY",
        initial_capital=1000000.0, current_capital=1000000.0, exchange_rate=1.0
    )
    db_session.add(cn_account)
    db_session.commit()

    saved_account = db_session.query(MarketAccount).filter(
        MarketAccount.user_id == user.id, MarketAccount.market == "CN"
    ).first()
    assert saved_account is not None
    assert saved_account.currency == "CNY"
    assert saved_account.current_capital == 1000000.0


def test_multiple_markets(db_session):
    user = User(
        username="testuser", email="test@example.com",
        password_hash="hashed_password",
        initial_capital=1000000.0, current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    accounts = [
        MarketAccount(user_id=user.id, market="CN", currency="CNY", initial_capital=500000.0, current_capital=500000.0),
        MarketAccount(user_id=user.id, market="HK", currency="HKD", initial_capital=300000.0, current_capital=300000.0, exchange_rate=0.9),
        MarketAccount(user_id=user.id, market="US", currency="USD", initial_capital=200000.0, current_capital=200000.0, exchange_rate=7.2),
    ]
    db_session.add_all(accounts)
    db_session.commit()

    user_accounts = db_session.query(MarketAccount).filter(MarketAccount.user_id == user.id).all()
    assert len(user_accounts) == 3
    markets = [a.market for a in user_accounts]
    assert "CN" in markets
    assert "HK" in markets
    assert "US" in markets
