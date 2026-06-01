from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.models.risk_config import RiskConfig
from app.strategies.base import Signal


class RiskControl:
    """风控系统"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_config(self, user_id: int) -> RiskConfig:
        config = self.db.query(RiskConfig).filter(RiskConfig.user_id == user_id).first()
        if not config:
            config = RiskConfig(user_id=user_id)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config

    def check(self, signal: Signal, user_id: int) -> Tuple[bool, str]:
        config = self.get_or_create_config(user_id)

        checks = [
            self._check_position_limit,
            self._check_trade_frequency,
            self._check_single_trade,
        ]

        for check in checks:
            passed, reason = check(signal, user_id, config)
            if not passed:
                return False, reason

        return True, "通过"

    def _check_position_limit(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == signal.stock_code
        ).first()

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"

        positions = self.db.query(Position).filter(Position.user_id == user_id).all()
        market_value = sum(p.quantity * (p.current_price or p.avg_cost) for p in positions)
        total_assets = user.current_capital + market_value

        if position:
            position_value = position.quantity * signal.price
            position_pct = position_value / total_assets if total_assets > 0 else 0
            if position_pct > config.max_position_pct:
                return False, f"仓位超限: {position_pct:.1%} > {config.max_position_pct:.1%}"

        return True, "通过"

    def _check_trade_frequency(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= today
        ).count()

        if daily_trades >= config.max_daily_trades:
            return False, f"今日交易次数已达上限: {daily_trades}/{config.max_daily_trades}"

        return True, "通过"

    def _check_single_trade(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        trade_amount = signal.price * signal.quantity
        if trade_amount > config.max_single_trade:
            return False, f"单笔交易金额超限: {trade_amount:.2f} > {config.max_single_trade:.2f}"
        return True, "通过"
