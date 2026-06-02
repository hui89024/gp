from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.order import Order
from app.models.market_account import MarketAccount
from app.models.position import Position
from app.models.trade import Trade
from app.schemas.order import OrderCreate
from app.services.market_rules import MarketRulesFactory
from app.services.matching_engine import MatchingEngine, MarketData


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, user_id: int, order_data: OrderCreate) -> Order:
        rules = MarketRulesFactory.get_rules(order_data.market)
        if not rules.validate_quantity(order_data.quantity, order_data.stock_code):
            raise ValueError(f"无效的交易数量: {order_data.quantity}")
        account = self.db.query(MarketAccount).filter(
            MarketAccount.user_id == user_id,
            MarketAccount.market == order_data.market
        ).first()
        if not account:
            raise ValueError(f"未找到{order_data.market}市场账户")
        order = Order(
            user_id=user_id,
            market=order_data.market,
            stock_code=order_data.stock_code,
            stock_name=order_data.stock_name,
            order_type=order_data.order_type.value,
            direction=order_data.direction.value,
            price=order_data.price,
            quantity=order_data.quantity,
            time_in_force=order_data.time_in_force.value if order_data.time_in_force else "GTC",
            stop_price=order_data.stop_price,
            condition_type=order_data.condition_type,
            condition_value=order_data.condition_value,
            strategy_tag=order_data.strategy_tag,
            status="PENDING"
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def execute_order(self, order_id: int, market_data: MarketData, base_price: Optional[float] = None) -> dict:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "message": "订单不存在"}
        if order.status != "PENDING":
            return {"success": False, "message": "订单状态错误"}
        rules = MarketRulesFactory.get_rules(order.market)
        engine = MatchingEngine(rules)
        result = engine.match(order, market_data, base_price)
        if result.success:
            order.status = "FILLED"
            order.filled_quantity = result.quantity
            order.avg_fill_price = result.price
            order.filled_at = datetime.utcnow()
            commission = rules.calculate_commission(order.direction, result.price, result.quantity)
            trade = Trade(
                user_id=order.user_id,
                order_id=order.id,
                market=order.market,
                stock_code=order.stock_code,
                trade_type=order.direction,
                price=result.price,
                quantity=result.quantity,
                commission=commission.get("commission", 0),
                tax=commission.get("stamp_tax", 0) + commission.get("transfer_fee", 0),
                total_amount=result.price * result.quantity,
                strategy_tag=order.strategy_tag,
                trade_time=datetime.utcnow()
            )
            self.db.add(trade)
            self._update_position(order, result.price, result.quantity)
            self._update_account(order, result.price, result.quantity, commission["total"])
            self.db.commit()
            return {
                "success": True, "message": result.message,
                "trade_id": trade.id, "price": result.price,
                "quantity": result.quantity, "commission": commission["total"]
            }
        else:
            return {"success": False, "message": result.message}

    def _update_position(self, order: Order, price: float, quantity: int):
        position = self.db.query(Position).filter(
            Position.user_id == order.user_id,
            Position.market == order.market,
            Position.stock_code == order.stock_code
        ).first()
        if order.direction == "BUY":
            if position:
                total_quantity = position.quantity + quantity
                position.avg_cost = (
                    (position.avg_cost * position.quantity + price * quantity) / total_quantity
                )
                position.quantity = total_quantity
            else:
                position = Position(
                    user_id=order.user_id,
                    market=order.market,
                    stock_code=order.stock_code,
                    stock_name=order.stock_name,
                    quantity=quantity,
                    avg_cost=price,
                    current_price=price,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0
                )
                self.db.add(position)
        else:
            if position:
                position.quantity -= quantity
                if position.quantity == 0:
                    self.db.delete(position)

    def _update_account(self, order: Order, price: float, quantity: int, commission: float):
        account = self.db.query(MarketAccount).filter(
            MarketAccount.user_id == order.user_id,
            MarketAccount.market == order.market
        ).first()
        if order.direction == "BUY":
            account.current_capital -= (price * quantity + commission)
        else:
            account.current_capital += (price * quantity - commission)

    def get_orders(self, user_id: int, market: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Order]:
        query = self.db.query(Order).filter(Order.user_id == user_id)
        if market:
            query = query.filter(Order.market == market)
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(Order.created_at.desc()).limit(limit).all()

    def cancel_order(self, order_id: int, user_id: int) -> dict:
        order = self.db.query(Order).filter(
            Order.id == order_id, Order.user_id == user_id
        ).first()
        if not order:
            return {"success": False, "message": "订单不存在"}
        if order.status != "PENDING":
            return {"success": False, "message": "只能取消待执行的订单"}
        order.status = "CANCELLED"
        self.db.commit()
        return {"success": True, "message": "订单已取消"}
