import pytest
from app.services.account_service import AccountService
from app.models.user import User


@pytest.fixture
def account_service(db_session):
    return AccountService(db_session)


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


def test_create_user(account_service):
    """测试创建用户"""
    user = account_service.create_user("newuser", 500000.0)
    assert user.username == "newuser"
    assert user.initial_capital == 500000.0
    assert user.current_capital == 500000.0


def test_get_user(account_service, test_user):
    """测试获取用户"""
    user = account_service.get_user(test_user.id)
    assert user is not None
    assert user.username == "testuser"


def test_get_account_overview(account_service, test_user):
    """测试获取账户概览"""
    overview = account_service.get_account_overview(test_user.id)
    assert overview.total_assets == 1000000.0
    assert overview.available_capital == 1000000.0
    assert overview.market_value == 0.0
