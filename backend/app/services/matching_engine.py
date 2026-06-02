from dataclasses import dataclass
from typing import Optional
from app.services.market_rules import MarketRules, PriceLimitType
from app.models.order import Order


@dataclass
class MarketData:
    stock_code: str
    current_price: float
    bid_price: float  # 买一价
    ask_price: float  # 卖一价
    volume: int


@dataclass
class MatchResult:
    success: bool
    message: str
    price: Optional[float] = None
    quantity: Optional[int] = None


class MatchingEngine:
    def __init__(self, market_rules: MarketRules):
        self.market_rules = market_rules
        self.default_slippage = 0.005  # 0.5%

    def match(self, order: Order, market_data: MarketData, base_price: Optional[float] = None) -> MatchResult:
        if order.status and order.status != "PENDING":
            return MatchResult(success=False, message="订单状态错误")
        if base_price and order.price:
            if not self.market_rules.check_price_limit(base_price, order.price):
                return MatchResult(success=False, message="价格超出涨跌停限制")
        if order.order_type == "MARKET":
            return self._match_market_order(order, market_data)
        elif order.order_type == "LIMIT":
            return self._match_limit_order(order, market_data)
        elif order.order_type == "STOP_LOSS":
            return self._match_stop_loss_order(order, market_data)
        elif order.order_type == "TAKE_PROFIT":
            return self._match_take_profit_order(order, market_data)
        else:
            return MatchResult(success=False, message=f"不支持的订单类型: {order.order_type}")

    def _match_market_order(self, order: Order, market_data: MarketData) -> MatchResult:
        slippage = self.default_slippage
        if order.direction == "BUY":
            price = market_data.ask_price * (1 + slippage)
        else:
            price = market_data.bid_price * (1 - slippage)
        return MatchResult(success=True, message="市价单撮合成功", price=round(price, 4), quantity=order.quantity)

    def _match_limit_order(self, order: Order, market_data: MarketData) -> MatchResult:
        if order.direction == "BUY":
            if market_data.ask_price <= order.price:
                return MatchResult(success=True, message="限价买入单撮合成功", price=market_data.ask_price, quantity=order.quantity)
        else:
            if market_data.bid_price >= order.price:
                return MatchResult(success=True, message="限价卖出单撮合成功", price=market_data.bid_price, quantity=order.quantity)
        return MatchResult(success=False, message="限价单未达到成交条件")

    def _match_stop_loss_order(self, order: Order, market_data: MarketData) -> MatchResult:
        if order.direction == "SELL":
            if market_data.current_price <= order.stop_price:
                return MatchResult(success=True, message="止损单触发", price=market_data.bid_price, quantity=order.quantity)
        else:
            if market_data.current_price >= order.stop_price:
                return MatchResult(success=True, message="止损单触发", price=market_data.ask_price, quantity=order.quantity)
        return MatchResult(success=False, message="止损单未触发")

    def _match_take_profit_order(self, order: Order, market_data: MarketData) -> MatchResult:
        if order.direction == "SELL":
            if market_data.current_price >= order.stop_price:
                return MatchResult(success=True, message="止盈单触发", price=market_data.bid_price, quantity=order.quantity)
        else:
            if market_data.current_price <= order.stop_price:
                return MatchResult(success=True, message="止盈单触发", price=market_data.ask_price, quantity=order.quantity)
        return MatchResult(success=False, message="止盈单未触发")
