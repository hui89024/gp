from typing import Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.models.live_trade import LiveTrade
from app.models.risk_control_record import RiskControlRecord


class LiveTradingRiskControl:
    """实盘交易风控系统"""

    def __init__(self, db: Session):
        self.db = db
        self.max_single_trade = settings.LIVE_MAX_SINGLE_TRADE
        self.max_daily_trades = settings.LIVE_MAX_DAILY_TRADES
        self.max_daily_loss = settings.LIVE_MAX_DAILY_LOSS
        self.max_position_ratio = settings.LIVE_MAX_POSITION_RATIO
        self.stop_loss_ratio = settings.LIVE_STOP_LOSS_RATIO

    def validate_trade(
        self, user_id: int, amount: float, stock_code: str, trade_type: str
    ) -> Tuple[bool, str]:
        """交易前验证"""
        # 1. 检查单笔交易金额
        if amount > self.max_single_trade:
            self._record_event(user_id, "trade_rejected", {
                "reason": f"单笔交易金额{amount}超过限制{self.max_single_trade}",
                "stock_code": stock_code
            })
            return False, f"单笔交易金额不能超过{self.max_single_trade}元"

        # 2. 检查每日交易次数
        today_count = self._get_today_trade_count(user_id)
        if today_count >= self.max_daily_trades:
            self._record_event(user_id, "trade_rejected", {
                "reason": f"今日交易{today_count}次已达上限",
                "stock_code": stock_code
            })
            return False, f"每日交易次数不能超过{self.max_daily_trades}次"

        # 3. 检查每日亏损
        today_loss = self._get_today_loss(user_id)
        if today_loss >= self.max_daily_loss:
            self._record_event(user_id, "trade_rejected", {
                "reason": f"今日亏损{today_loss}已达上限",
                "stock_code": stock_code
            })
            return False, f"每日亏损已达上限{self.max_daily_loss}元"

        return True, "验证通过"

    def check_stop_loss(self, user_id: int, positions: list) -> list:
        """检查止损，返回需要平仓的持仓"""
        stop_loss_list = []
        for pos in positions:
            if pos.get("profit_loss_ratio", 0) <= self.stop_loss_ratio:
                stop_loss_list.append(pos)
                self._record_event(user_id, "stop_loss", {
                    "stock_code": pos.get("stock_code"),
                    "profit_loss_ratio": pos.get("profit_loss_ratio"),
                })
        return stop_loss_list

    def _get_today_trade_count(self, user_id: int) -> int:
        """获取今日交易次数"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id,
            LiveTrade.trade_time >= today_start,
            LiveTrade.status == "filled"
        ).count()

    def _get_today_loss(self, user_id: int) -> float:
        """获取今日亏损金额"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        trades = self.db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id,
            LiveTrade.trade_time >= today_start,
            LiveTrade.status == "filled"
        ).all()
        total_loss = 0.0
        for trade in trades:
            if trade.trade_type == "SELL":
                total_loss += float(trade.total_amount) - float(trade.commission)
            else:
                total_loss -= float(trade.total_amount) + float(trade.commission)
        return abs(min(total_loss, 0))

    def _record_event(self, user_id: int, event_type: str, detail: dict):
        """记录风控事件"""
        record = RiskControlRecord(
            user_id=user_id,
            event_type=event_type,
            event_detail=detail
        )
        self.db.add(record)
        self.db.commit()
