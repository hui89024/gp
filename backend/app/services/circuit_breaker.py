from datetime import datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass

from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.models.circuit_breaker_event import CircuitBreakerEvent
from app.models.auto_trade_task import AutoTradeTask


@dataclass
class CircuitBreakerConfig:
    max_drawdown_pct: float = -0.10
    max_daily_loss_pct: float = -0.05
    max_consecutive_losses: int = 5
    max_trades_per_minute: int = 10
    max_position_pct: float = 0.90


class CircuitBreaker:
    """独立风控熔断器"""

    def __init__(self, db: Session, config: Optional[CircuitBreakerConfig] = None):
        self.db = db
        self.config = config or CircuitBreakerConfig()
        self.is_triggered = False
        self.trigger_reason = None

    def check(self, user_id: int) -> Tuple[bool, str]:
        """检查是否需要熔断"""
        if self.is_triggered:
            return True, self.trigger_reason

        checks = [
            self._check_daily_loss,
            self._check_consecutive_losses,
            self._check_trade_frequency,
            self._check_position,
        ]

        for check in checks:
            triggered, reason = check(user_id)
            if triggered:
                self._trigger_breaker(user_id, reason)
                return True, reason

        return False, "正常"

    def _trigger_breaker(self, user_id: int, reason: str):
        """触发熔断"""
        self.is_triggered = True
        self.trigger_reason = reason
        self._stop_all_tasks(user_id)

        event = CircuitBreakerEvent(
            user_id=user_id,
            trigger_reason=reason,
            action_taken="STOP_TASKS"
        )
        self.db.add(event)
        self.db.commit()

    def _stop_all_tasks(self, user_id: int):
        """停止所有自动交易任务"""
        tasks = self.db.query(AutoTradeTask).filter(
            AutoTradeTask.user_id == user_id,
            AutoTradeTask.enabled == True
        ).all()
        for task in tasks:
            task.enabled = False
        self.db.commit()

    def _check_daily_loss(self, user_id: int) -> Tuple[bool, str]:
        """检查单日亏损"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sell_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_type == "SELL",
            Trade.trade_time >= today
        ).all()

        daily_pnl = sum(t.total_amount * 0.02 for t in sell_trades)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, ""

        daily_loss_pct = daily_pnl / user.initial_capital
        if daily_loss_pct < self.config.max_daily_loss_pct:
            return True, f"单日亏损超限: {daily_loss_pct:.1%}"
        return False, ""

    def _check_consecutive_losses(self, user_id: int) -> Tuple[bool, str]:
        """检查连续亏损"""
        recent_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_type == "SELL"
        ).order_by(Trade.trade_time.desc()).limit(self.config.max_consecutive_losses).all()

        if len(recent_trades) < self.config.max_consecutive_losses:
            return False, ""

        consecutive_losses = sum(1 for t in recent_trades if t.total_amount * 0.02 < 0)
        if consecutive_losses >= self.config.max_consecutive_losses:
            return True, f"连续亏损{consecutive_losses}次"
        return False, ""

    def _check_trade_frequency(self, user_id: int) -> Tuple[bool, str]:
        """检查交易频率"""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= one_minute_ago
        ).count()

        if recent_trades > self.config.max_trades_per_minute:
            return True, f"交易频率超限: {recent_trades}次/分钟"
        return False, ""

    def _check_position(self, user_id: int) -> Tuple[bool, str]:
        """检查仓位"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, ""

        positions = self.db.query(Position).filter(Position.user_id == user_id).all()
        market_value = sum(p.quantity * (p.current_price or p.avg_cost) for p in positions)
        total_assets = user.current_capital + market_value

        if total_assets > 0:
            position_pct = market_value / total_assets
            if position_pct > self.config.max_position_pct:
                return True, f"仓位超限: {position_pct:.1%}"
        return False, ""

    def reset(self):
        """重置熔断器"""
        self.is_triggered = False
        self.trigger_reason = None

    def get_status(self, user_id: int) -> dict:
        """获取熔断状态"""
        return {
            "is_triggered": self.is_triggered,
            "trigger_reason": self.trigger_reason
        }

    def get_events(self, user_id: int, limit: int = 20) -> list:
        """获取熔断事件"""
        return self.db.query(CircuitBreakerEvent).filter(
            CircuitBreakerEvent.user_id == user_id
        ).order_by(CircuitBreakerEvent.created_at.desc()).limit(limit).all()