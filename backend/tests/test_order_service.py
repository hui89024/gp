import pytest
from datetime import datetime
from app.services.order_service import OrderService
from app.services.matching_engine import MarketData
from app.models.user import User
from app.models.market_account import MarketAccount
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderType, OrderDirection, TimeInForce


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testorderuser",
        email="testorder@example.com",
        hashed_password="hashedpassword",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def cn_account(db_session, test_user):
    """创建A股账户"""
    account = MarketAccount(
        user_id=test_user.id,
        market="CN",
        currency="CNY",
        initial_capital=100000.0,
        current_capital=100000.0,
        exchange_rate=1.0
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def order_service(db_session):
    return OrderService(db_session)


@pytest.fixture
def sample_market_data():
    return MarketData(
        stock_code="600000",
        current_price=10.0,
        bid_price=9.98,
        ask_price=10.02,
        volume=1000000
    )


class TestCreateOrder:
    """创建订单测试"""

    def test_create_market_order(self, order_service, test_user, cn_account):
        """创建市价单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            stock_name="浦发银行",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        assert order.id is not None
        assert order.status == "PENDING"
        assert order.market == "CN"
        assert order.stock_code == "600000"
        assert order.order_type == "MARKET"
        assert order.direction == "BUY"

    def test_create_limit_order(self, order_service, test_user, cn_account):
        """创建限价单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.LIMIT,
            direction=OrderDirection.SELL,
            price=10.5,
            quantity=200,
            time_in_force=TimeInForce.GTC
        )
        order = order_service.create_order(test_user.id, order_data)
        assert order.price == 10.5
        assert order.quantity == 200
        assert order.time_in_force == "GTC"

    def test_create_stop_loss_order(self, order_service, test_user, cn_account):
        """创建止损单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.STOP_LOSS,
            direction=OrderDirection.SELL,
            stop_price=9.0,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        assert order.stop_price == 9.0
        assert order.order_type == "STOP_LOSS"

    def test_create_order_invalid_quantity(self, order_service, test_user, cn_account):
        """无效数量 - A股不是100的倍数"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=50
        )
        with pytest.raises(ValueError, match="无效的交易数量"):
            order_service.create_order(test_user.id, order_data)

    def test_create_order_no_account(self, order_service, test_user):
        """没有对应市场账户"""
        order_data = OrderCreate(
            market="HK",
            stock_code="00700",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        with pytest.raises(ValueError, match="未找到"):
            order_service.create_order(test_user.id, order_data)

    def test_create_order_with_strategy_tag(self, order_service, test_user, cn_account):
        """带策略标签的订单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            strategy_tag="momentum_v1"
        )
        order = order_service.create_order(test_user.id, order_data)
        assert order.strategy_tag == "momentum_v1"


class TestExecuteOrder:
    """执行订单测试"""

    def test_execute_market_buy_order(self, order_service, test_user, cn_account, sample_market_data):
        """执行市价买入单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        result = order_service.execute_order(order.id, sample_market_data)
        assert result["success"] is True
        assert result["price"] > 0
        assert result["quantity"] == 100
        assert result["commission"] > 0

    def test_execute_market_sell_order(self, order_service, test_user, cn_account, sample_market_data):
        """执行市价卖出单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.SELL,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        result = order_service.execute_order(order.id, sample_market_data)
        assert result["success"] is True

    def test_execute_limit_order_filled(self, order_service, test_user, cn_account):
        """执行限价单 - 成交"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.LIMIT,
            direction=OrderDirection.BUY,
            price=10.05,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        market_data = MarketData(
            stock_code="600000",
            current_price=10.0,
            bid_price=9.98,
            ask_price=10.02,
            volume=1000000
        )
        result = order_service.execute_order(order.id, market_data)
        assert result["success"] is True

    def test_execute_limit_order_not_filled(self, order_service, test_user, cn_account):
        """执行限价单 - 未成交"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.LIMIT,
            direction=OrderDirection.BUY,
            price=9.90,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        market_data = MarketData(
            stock_code="600000",
            current_price=10.0,
            bid_price=9.98,
            ask_price=10.02,
            volume=1000000
        )
        result = order_service.execute_order(order.id, market_data)
        assert result["success"] is False
        assert "未达到成交条件" in result["message"]

    def test_execute_nonexistent_order(self, order_service, sample_market_data):
        """执行不存在的订单"""
        result = order_service.execute_order(99999, sample_market_data)
        assert result["success"] is False
        assert result["message"] == "订单不存在"

    def test_execute_non_pending_order(self, order_service, test_user, cn_account, sample_market_data):
        """执行非PENDING状态订单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        # 先执行一次
        order_service.execute_order(order.id, sample_market_data)
        # 再执行一次 - 应该失败
        result = order_service.execute_order(order.id, sample_market_data)
        assert result["success"] is False
        assert result["message"] == "订单状态错误"


class TestPositionUpdate:
    """持仓更新测试"""

    def test_buy_creates_position(self, order_service, test_user, cn_account, sample_market_data):
        """买入创建新持仓"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        result = order_service.execute_order(order.id, sample_market_data)
        assert result["success"] is True

        # 检查持仓
        from app.models.position import Position
        position = order_service.db.query(Position).filter(
            Position.user_id == test_user.id,
            Position.stock_code == "600000"
        ).first()
        assert position is not None
        assert position.quantity == 100

    def test_buy_increases_position(self, order_service, test_user, cn_account, sample_market_data):
        """买入增加持仓"""
        # 第一次买入
        order_data1 = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order1 = order_service.create_order(test_user.id, order_data1)
        order_service.execute_order(order1.id, sample_market_data)

        # 第二次买入
        order_data2 = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order2 = order_service.create_order(test_user.id, order_data2)
        order_service.execute_order(order2.id, sample_market_data)

        from app.models.position import Position
        position = order_service.db.query(Position).filter(
            Position.user_id == test_user.id,
            Position.stock_code == "600000"
        ).first()
        assert position.quantity == 200

    def test_sell_removes_position(self, order_service, test_user, cn_account, sample_market_data):
        """全部卖出删除持仓"""
        # 买入
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        order_service.execute_order(order.id, sample_market_data)

        # 卖出
        sell_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.SELL,
            quantity=100
        )
        sell_order = order_service.create_order(test_user.id, sell_data)
        order_service.execute_order(sell_order.id, sample_market_data)

        from app.models.position import Position
        position = order_service.db.query(Position).filter(
            Position.user_id == test_user.id,
            Position.stock_code == "600000"
        ).first()
        assert position is None


class TestAccountUpdate:
    """账户资金更新测试"""

    def test_buy_decreases_capital(self, order_service, test_user, cn_account, sample_market_data):
        """买入减少资金"""
        initial_capital = cn_account.current_capital
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        result = order_service.execute_order(order.id, sample_market_data)

        order_service.db.refresh(cn_account)
        expected_cost = result["price"] * 100 + result["commission"]
        assert cn_account.current_capital == pytest.approx(initial_capital - expected_cost, rel=1e-2)

    def test_sell_increases_capital(self, order_service, test_user, cn_account, sample_market_data):
        """卖出增加资金"""
        # 先买入
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        order_service.execute_order(order.id, sample_market_data)

        order_service.db.refresh(cn_account)
        capital_after_buy = cn_account.current_capital

        # 卖出
        sell_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.SELL,
            quantity=100
        )
        sell_order = order_service.create_order(test_user.id, sell_data)
        result = order_service.execute_order(sell_order.id, sample_market_data)

        order_service.db.refresh(cn_account)
        expected_increase = result["price"] * 100 - result["commission"]
        assert cn_account.current_capital == pytest.approx(capital_after_buy + expected_increase, rel=1e-2)


class TestGetOrders:
    """查询订单测试"""

    def test_get_orders_by_user(self, order_service, test_user, cn_account):
        """按用户查询订单"""
        # 创建几个订单
        for _ in range(3):
            order_data = OrderCreate(
                market="CN",
                stock_code="600000",
                order_type=OrderType.MARKET,
                direction=OrderDirection.BUY,
                quantity=100
            )
            order_service.create_order(test_user.id, order_data)

        orders = order_service.get_orders(test_user.id)
        assert len(orders) == 3

    def test_get_orders_by_market(self, order_service, test_user, cn_account):
        """按市场查询订单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order_service.create_order(test_user.id, order_data)

        orders = order_service.get_orders(test_user.id, market="CN")
        assert len(orders) == 1

        orders = order_service.get_orders(test_user.id, market="HK")
        assert len(orders) == 0

    def test_get_orders_by_status(self, order_service, test_user, cn_account, sample_market_data):
        """按状态查询订单"""
        # 创建并执行一个订单
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        order_service.execute_order(order.id, sample_market_data)

        # 创建一个待执行订单
        order_service.create_order(test_user.id, order_data)

        filled_orders = order_service.get_orders(test_user.id, status="FILLED")
        assert len(filled_orders) == 1

        pending_orders = order_service.get_orders(test_user.id, status="PENDING")
        assert len(pending_orders) == 1


class TestCancelOrder:
    """取消订单测试"""

    def test_cancel_pending_order(self, order_service, test_user, cn_account):
        """取消待执行订单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.LIMIT,
            direction=OrderDirection.BUY,
            price=9.0,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        result = order_service.cancel_order(order.id, test_user.id)
        assert result["success"] is True

        # 验证状态
        orders = order_service.get_orders(test_user.id, status="CANCELLED")
        assert len(orders) == 1

    def test_cancel_nonexistent_order(self, order_service, test_user):
        """取消不存在的订单"""
        result = order_service.cancel_order(99999, test_user.id)
        assert result["success"] is False

    def test_cancel_filled_order(self, order_service, test_user, cn_account, sample_market_data):
        """取消已成交订单 - 应该失败"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)
        order_service.execute_order(order.id, sample_market_data)

        result = order_service.cancel_order(order.id, test_user.id)
        assert result["success"] is False
        assert "只能取消待执行的订单" in result["message"]


class TestStopLossExecution:
    """止损单执行测试"""

    def test_execute_stop_loss_triggered(self, order_service, test_user, cn_account):
        """执行触发的止损单"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.STOP_LOSS,
            direction=OrderDirection.SELL,
            stop_price=9.5,
            quantity=100
        )
        order = order_service.create_order(test_user.id, order_data)

        # 先买入建仓
        buy_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        buy_order = order_service.create_order(test_user.id, buy_data)
        order_service.execute_order(buy_order.id, MarketData(
            stock_code="600000", current_price=10.0,
            bid_price=9.98, ask_price=10.02, volume=1000000
        ))

        # 价格下跌触发止损
        market_data = MarketData(
            stock_code="600000",
            current_price=9.4,
            bid_price=9.38,
            ask_price=9.42,
            volume=1000000
        )
        result = order_service.execute_order(order.id, market_data)
        assert result["success"] is True


class TestTradeCreation:
    """成交记录测试"""

    def test_trade_created_on_fill(self, order_service, test_user, cn_account, sample_market_data):
        """成交后创建交易记录"""
        order_data = OrderCreate(
            market="CN",
            stock_code="600000",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            strategy_tag="test_strategy"
        )
        order = order_service.create_order(test_user.id, order_data)
        result = order_service.execute_order(order.id, sample_market_data)

        from app.models.trade import Trade
        trade = order_service.db.query(Trade).filter(Trade.user_id == test_user.id).first()
        assert trade is not None
        assert trade.stock_code == "600000"
        assert trade.trade_type == "BUY"
        assert trade.quantity == 100
        assert trade.strategy_tag == "test_strategy"
