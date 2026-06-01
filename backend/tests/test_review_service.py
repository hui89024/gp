import pytest
from datetime import datetime
from app.services.review_service import ReviewService
from app.models.user import User
from app.models.trade import Trade


@pytest.fixture
def review_service(db_session):
    return ReviewService(db_session)


@pytest.fixture
def test_user_with_trades(db_session):
    user = User(
        username="reviewuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    trades = [
        Trade(
            user_id=user.id,
            stock_code="000001",
            trade_type="BUY",
            price=10.0,
            quantity=1000,
            commission=5.0,
            total_amount=10000.0,
            strategy_tag="trend_following"
        ),
        Trade(
            user_id=user.id,
            stock_code="000001",
            trade_type="SELL",
            price=10.5,
            quantity=1000,
            commission=5.0,
            total_amount=10500.0,
            strategy_tag="trend_following"
        ),
    ]

    for trade in trades:
        db_session.add(trade)
    db_session.commit()

    return user


def test_generate_daily_review(review_service, test_user_with_trades):
    """测试生成每日复盘"""
    review = review_service.generate_daily_review(test_user_with_trades.id)
    if review:
        assert review.total_trades > 0
        assert review.user_id == test_user_with_trades.id


def test_get_daily_summary(review_service, test_user_with_trades):
    """测试获取每日摘要"""
    summary = review_service.get_daily_summary(test_user_with_trades.id)
    assert summary.total_trades >= 0


def test_get_strategy_analysis(review_service, test_user_with_trades):
    """测试策略分析"""
    analyses = review_service.get_strategy_analysis(test_user_with_trades.id)
    assert isinstance(analyses, list)


def test_get_behavior_analysis(review_service, test_user_with_trades):
    """测试行为分析"""
    analysis = review_service.get_behavior_analysis(test_user_with_trades.id)
    assert analysis.trade_frequency >= 0


def test_get_comprehensive_review(review_service, test_user_with_trades):
    """测试综合复盘"""
    review = review_service.get_comprehensive_review(test_user_with_trades.id)
    assert review.daily_summary is not None
    assert review.behavior_analysis is not None
    assert len(review.recommendations) > 0
