from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.utils.commission import calculate_commission


@dataclass
class TradeResult:
    success: bool
    message: str
    trade: Optional[Trade] = None
    position: Optional[Position] = None


class TradingEngine:
    """交易引擎"""

    def __init__(self, db: Session):
        self.db = db

    def buy(
        self,
        user_id: int,
        stock_code: str,
        stock_name: str,
        price: float,
        quantity: int,
        strategy_tag: Optional[str] = None
    ) -> TradeResult:
        """
        买入股票

        Args:
            user_id: 用户ID
            stock_code: 股票代码
            stock_name: 股票名称
            price: 买入价格
            quantity: 买入数量
            strategy_tag: 策略标签

        Returns:
            交易结果
        """
        # 验证数量必须是100的整数倍
        if quantity % 100 != 0:
            return TradeResult(success=False, message="买入数量必须是100的整数倍")

        # 获取用户
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return TradeResult(success=False, message="用户不存在")

        # 计算手续费
        commission = calculate_commission("BUY", price, quantity)
        total_cost = price * quantity + commission["total"]

        # 检查资金是否充足
        if user.current_capital < total_cost:
            return TradeResult(success=False, message="资金不足")

        # 创建交易记录
        trade = Trade(
            user_id=user_id,
            stock_code=stock_code,
            trade_type="BUY",
            price=price,
            quantity=quantity,
            commission=commission["total"],
            total_amount=price * quantity,
            strategy_tag=strategy_tag
        )
        self.db.add(trade)

        # 更新用户资金
        user.current_capital -= total_cost

        # 更新持仓
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == stock_code
        ).first()

        if position:
            # 计算新的平均成本
            total_quantity = position.quantity + quantity
            position.avg_cost = (
                (position.avg_cost * position.quantity + price * quantity)
                / total_quantity
            )
            position.quantity = total_quantity
        else:
            # 创建新持仓
            position = Position(
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                avg_cost=price,
                current_price=price,
                unrealized_pnl=0.0
            )
            self.db.add(position)

        self.db.commit()
        self.db.refresh(trade)
        self.db.refresh(position)

        return TradeResult(
            success=True,
            message="买入成功",
            trade=trade,
            position=position
        )

    def sell(
        self,
        user_id: int,
        stock_code: str,
        stock_name: str,
        price: float,
        quantity: int,
        strategy_tag: Optional[str] = None
    ) -> TradeResult:
        """
        卖出股票

        Args:
            user_id: 用户ID
            stock_code: 股票代码
            stock_name: 股票名称
            price: 卖出价格
            quantity: 卖出数量
            strategy_tag: 策略标签

        Returns:
            交易结果
        """
        # 验证数量必须是100的整数倍
        if quantity % 100 != 0:
            return TradeResult(success=False, message="卖出数量必须是100的整数倍")

        # 获取用户
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return TradeResult(success=False, message="用户不存在")

        # 获取持仓
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == stock_code
        ).first()

        if not position or position.quantity < quantity:
            return TradeResult(success=False, message="持仓不足")

        # 检查T+1限制（假设当天买入的不能卖出）
        today_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.stock_code == stock_code,
            Trade.trade_type == "BUY",
            Trade.trade_time >= datetime.now().replace(hour=0, minute=0, second=0)
        ).all()

        today_bought = sum(t.quantity for t in today_trades)
        if position.quantity - today_bought < quantity:
            return TradeResult(success=False, message="受T+1限制，当日买入的股票不能卖出")

        # 计算手续费
        commission = calculate_commission("SELL", price, quantity)
        total_income = price * quantity - commission["total"]

        # 创建交易记录
        trade = Trade(
            user_id=user_id,
            stock_code=stock_code,
            trade_type="SELL",
            price=price,
            quantity=quantity,
            commission=commission["total"],
            total_amount=price * quantity,
            strategy_tag=strategy_tag
        )
        self.db.add(trade)

        # 更新用户资金
        user.current_capital += total_income

        # 更新持仓
        position.quantity -= quantity
        if position.quantity == 0:
            self.db.delete(position)
            position = None

        self.db.commit()
        self.db.refresh(trade)
        if position:
            self.db.refresh(position)

        return TradeResult(
            success=True,
            message="卖出成功",
            trade=trade,
            position=position
        )

    def get_positions(self, user_id: int) -> list:
        """获取用户持仓"""
        return self.db.query(Position).filter(
            Position.user_id == user_id
        ).all()

    def get_trades(
        self,
        user_id: int,
        stock_code: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """获取交易记录"""
        query = self.db.query(Trade).filter(Trade.user_id == user_id)

        if stock_code:
            query = query.filter(Trade.stock_code == stock_code)

        return query.order_by(Trade.trade_time.desc()).limit(limit).all()
