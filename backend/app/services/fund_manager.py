from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session

from app.models.trade import Trade
from app.models.auto_trade_log import AutoTradeLog
from app.strategies.base import Signal
from app.services.trading_engine import TradingEngine, TradeResult


class FundMode(Enum):
    SIMULATED = "simulated"
    REAL = "real"


class FundManager:
    """资金管理器"""

    def __init__(self, db: Session, mode: FundMode = FundMode.SIMULATED):
        self.db = db
        self.mode = mode
        self.trading_engine = TradingEngine(db)

    async def execute_trade(self, signal: Signal, user_id: int, task_id: Optional[int] = None) -> TradeResult:
        log = AutoTradeLog(
            user_id=user_id,
            task_id=task_id,
            signal_source=signal.strategy_name,
            stock_code=signal.stock_code,
            stock_name=signal.stock_name,
            direction=signal.direction,
            price=signal.price,
            quantity=signal.quantity,
            confidence=signal.confidence,
            risk_check_passed=True,
            risk_check_reason="通过"
        )

        try:
            if signal.direction == "BUY":
                result = self.trading_engine.buy(
                    user_id=user_id,
                    stock_code=signal.stock_code,
                    stock_name=signal.stock_name,
                    price=signal.price,
                    quantity=signal.quantity,
                    strategy_tag=signal.strategy_name
                )
            else:
                result = self.trading_engine.sell(
                    user_id=user_id,
                    stock_code=signal.stock_code,
                    stock_name=signal.stock_name,
                    price=signal.price,
                    quantity=signal.quantity,
                    strategy_tag=signal.strategy_name
                )

            log.execution_result = "SUCCESS" if result.success else "FAILED"
            log.error_message = result.message if not result.success else None

        except Exception as e:
            log.execution_result = "FAILED"
            log.error_message = str(e)
            result = TradeResult(success=False, message=str(e))

        self.db.add(log)
        self.db.commit()

        return result
