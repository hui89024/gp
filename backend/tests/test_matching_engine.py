import pytest
from app.services.matching_engine import MatchingEngine, MarketData, MatchResult
from app.services.market_rules import CNRules, HKRules, USRules
from app.models.order import Order


@pytest.fixture
def cn_rules():
    return CNRules()


@pytest.fixture
def hk_rules():
    return HKRules()


@pytest.fixture
def us_rules():
    return USRules()


@pytest.fixture
def cn_engine(cn_rules):
    return MatchingEngine(cn_rules)


@pytest.fixture
def hk_engine(hk_rules):
    return MatchingEngine(hk_rules)


@pytest.fixture
def us_engine(us_rules):
    return MatchingEngine(us_rules)


def make_order(order_type="MARKET", direction="BUY", price=None, quantity=100, stop_price=None, status="PENDING"):
    """Helper to create order-like object"""
    order = Order.__new__(Order)
    order.order_type = order_type
    order.direction = direction
    order.price = price
    order.quantity = quantity
    order.stop_price = stop_price
    order.status = status
    return order


def make_market_data(current_price=10.0, bid_price=9.98, ask_price=10.02, volume=1000000):
    return MarketData(
        stock_code="600000",
        current_price=current_price,
        bid_price=bid_price,
        ask_price=ask_price,
        volume=volume
    )


class TestMarketOrder:
    """市价单撮合测试"""

    def test_buy_market_order(self, cn_engine):
        order = make_order(order_type="MARKET", direction="BUY")
        market_data = make_market_data(ask_price=10.0)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == pytest.approx(10.05, rel=1e-3)
        assert result.quantity == 100

    def test_sell_market_order(self, cn_engine):
        order = make_order(order_type="MARKET", direction="SELL")
        market_data = make_market_data(bid_price=10.0)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == pytest.approx(9.95, rel=1e-3)
        assert result.quantity == 100

    def test_market_order_slippage(self, cn_engine):
        """测试市价单滑点"""
        order = make_order(order_type="MARKET", direction="BUY")
        market_data = make_market_data(ask_price=100.0)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == pytest.approx(100.5, rel=1e-3)  # 0.5% slippage


class TestLimitOrder:
    """限价单撮合测试"""

    def test_buy_limit_order_filled(self, cn_engine):
        """买入限价单 - 卖一价低于限价"""
        order = make_order(order_type="LIMIT", direction="BUY", price=10.05)
        market_data = make_market_data(ask_price=10.0)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == 10.0

    def test_buy_limit_order_not_filled(self, cn_engine):
        """买入限价单 - 卖一价高于限价"""
        order = make_order(order_type="LIMIT", direction="BUY", price=9.95)
        market_data = make_market_data(ask_price=10.0)
        result = cn_engine.match(order, market_data)
        assert result.success is False
        assert result.price is None

    def test_sell_limit_order_filled(self, cn_engine):
        """卖出限价单 - 买一价高于限价"""
        order = make_order(order_type="LIMIT", direction="SELL", price=9.95)
        market_data = make_market_data(bid_price=10.0)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == 10.0

    def test_sell_limit_order_not_filled(self, cn_engine):
        """卖出限价单 - 买一价低于限价"""
        order = make_order(order_type="LIMIT", direction="SELL", price=10.05)
        market_data = make_market_data(bid_price=10.0)
        result = cn_engine.match(order, market_data)
        assert result.success is False
        assert result.price is None


class TestStopLossOrder:
    """止损单撮合测试"""

    def test_sell_stop_loss_triggered(self, cn_engine):
        """卖出止损单触发 - 当前价跌破止损价"""
        order = make_order(order_type="STOP_LOSS", direction="SELL", stop_price=9.5)
        market_data = make_market_data(current_price=9.4, bid_price=9.38)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == 9.38

    def test_sell_stop_loss_not_triggered(self, cn_engine):
        """卖出止损单未触发 - 当前价高于止损价"""
        order = make_order(order_type="STOP_LOSS", direction="SELL", stop_price=9.5)
        market_data = make_market_data(current_price=9.6)
        result = cn_engine.match(order, market_data)
        assert result.success is False

    def test_buy_stop_loss_triggered(self, cn_engine):
        """买入止损单触发 - 当前价涨破止损价"""
        order = make_order(order_type="STOP_LOSS", direction="BUY", stop_price=10.5)
        market_data = make_market_data(current_price=10.6, ask_price=10.62)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == 10.62

    def test_buy_stop_loss_not_triggered(self, cn_engine):
        """买入止损单未触发 - 当前价低于止损价"""
        order = make_order(order_type="STOP_LOSS", direction="BUY", stop_price=10.5)
        market_data = make_market_data(current_price=10.4)
        result = cn_engine.match(order, market_data)
        assert result.success is False


class TestTakeProfitOrder:
    """止盈单撮合测试"""

    def test_sell_take_profit_triggered(self, cn_engine):
        """卖出止盈单触发 - 当前价达到止盈价"""
        order = make_order(order_type="TAKE_PROFIT", direction="SELL", stop_price=11.0)
        market_data = make_market_data(current_price=11.2, bid_price=11.18)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == 11.18

    def test_sell_take_profit_not_triggered(self, cn_engine):
        """卖出止盈单未触发 - 当前价低于止盈价"""
        order = make_order(order_type="TAKE_PROFIT", direction="SELL", stop_price=11.0)
        market_data = make_market_data(current_price=10.8)
        result = cn_engine.match(order, market_data)
        assert result.success is False

    def test_buy_take_profit_triggered(self, cn_engine):
        """买入止盈单触发 - 当前价跌破止盈价"""
        order = make_order(order_type="TAKE_PROFIT", direction="BUY", stop_price=9.0)
        market_data = make_market_data(current_price=8.9, ask_price=8.92)
        result = cn_engine.match(order, market_data)
        assert result.success is True
        assert result.price == 8.92

    def test_buy_take_profit_not_triggered(self, cn_engine):
        """买入止盈单未触发 - 当前价高于止盈价"""
        order = make_order(order_type="TAKE_PROFIT", direction="BUY", stop_price=9.0)
        market_data = make_market_data(current_price=9.1)
        result = cn_engine.match(order, market_data)
        assert result.success is False


class TestOrderStatus:
    """订单状态测试"""

    def test_non_pending_order_rejected(self, cn_engine):
        """非PENDING状态订单被拒绝"""
        order = make_order(status="FILLED")
        market_data = make_market_data()
        result = cn_engine.match(order, market_data)
        assert result.success is False
        assert result.message == "订单状态错误"


class TestUnsupportedOrderType:
    """不支持的订单类型测试"""

    def test_unsupported_order_type(self, cn_engine):
        """不支持的订单类型"""
        order = make_order(order_type="OCO")
        market_data = make_market_data()
        result = cn_engine.match(order, market_data)
        assert result.success is False
        assert "不支持的订单类型" in result.message


class TestPriceLimit:
    """涨跌停限制测试"""

    def test_cn_price_limit_exceeded(self, cn_engine):
        """A股价格超出涨跌停限制"""
        order = make_order(order_type="LIMIT", direction="BUY", price=12.0)
        market_data = make_market_data()
        result = cn_engine.match(order, market_data, base_price=10.0)
        assert result.success is False
        assert "涨跌停" in result.message

    def test_cn_price_within_limit(self, cn_engine):
        """A股价格在涨跌停范围内"""
        order = make_order(order_type="LIMIT", direction="BUY", price=10.5)
        market_data = make_market_data(ask_price=10.5)
        result = cn_engine.match(order, market_data, base_price=10.0)
        assert result.success is True

    def test_hk_no_price_limit(self, hk_engine):
        """港股无涨跌停限制"""
        order = make_order(order_type="LIMIT", direction="BUY", price=15.0)
        market_data = make_market_data(ask_price=15.0)
        result = hk_engine.match(order, market_data, base_price=10.0)
        assert result.success is True


class TestDifferentMarkets:
    """不同市场撮合测试"""

    def test_hk_market_order(self, hk_engine):
        """港股市价单"""
        order = make_order(order_type="MARKET", direction="BUY")
        market_data = make_market_data(ask_price=100.0)
        result = hk_engine.match(order, market_data)
        assert result.success is True
        assert result.price == pytest.approx(100.5, rel=1e-3)

    def test_us_market_order(self, us_engine):
        """美股市价单"""
        order = make_order(order_type="MARKET", direction="SELL")
        market_data = make_market_data(bid_price=50.0)
        result = us_engine.match(order, market_data)
        assert result.success is True
        assert result.price == pytest.approx(49.75, rel=1e-3)
