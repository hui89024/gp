import pytest
from datetime import datetime, timedelta
from app.services.trading_engine import TradingEngine
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade


@pytest.fixture
def trading_engine(db_session):
    return TradingEngine(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_buy_stock(trading_engine, test_user):
    """测试买入股票"""
    result = trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )

    assert result.success is True
    assert result.trade.stock_code == "000001"
    assert result.trade.quantity == 1000
    assert result.position.quantity == 1000


def test_sell_stock(trading_engine, test_user):
    """测试卖出股票"""
    # 先买入
    trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )

    # 再卖出
    result = trading_engine.sell(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=11.0,
        quantity=500
    )

    assert result.success is True
    assert result.trade.quantity == 500
    assert result.position.quantity == 500


def test_insufficient_funds(trading_engine, test_user):
    """测试资金不足"""
    result = trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=1000.0,
        quantity=10000
    )

    assert result.success is False
    assert "资金不足" in result.message


def test_insufficient_position(trading_engine, test_user):
    """测试持仓不足"""
    result = trading_engine.sell(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )

    assert result.success is False
    assert "持仓不足" in result.message


def test_t1_restriction(trading_engine, test_user):
    """测试T+1限制"""
    # 买入
    trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )

    # 当天卖出（应该失败）
    result = trading_engine.sell(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=11.0,
        quantity=1000
    )

    assert result.success is False
    assert "T+1" in result.message
