from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.auto_trade_task import AutoTradeTask
from app.models.trade import Trade
from app.services.strategy_engine import StrategyEngine
from app.services.risk_control import RiskControl
from app.services.fund_manager import FundManager, FundMode


class ExecutionEngine:
    """执行引擎"""

    def __init__(self, db: Session, user_id: int, mode: FundMode = FundMode.SIMULATED):
        self.db = db
        self.user_id = user_id
        self.strategy_engine = StrategyEngine(db)
        self.risk_control = RiskControl(db)
        self.fund_manager = FundManager(db, mode)
        self.running = False

    def start(self, task_id: int):
        task = self.db.query(AutoTradeTask).filter(
            AutoTradeTask.id == task_id,
            AutoTradeTask.user_id == self.user_id
        ).first()
        if not task:
            raise ValueError("任务不存在")

        self.strategy_engine.load_strategies(self.user_id)
        self.running = True
        self._execute_cycle(task.watchlist)
        task.last_run_at = datetime.now()
        self.db.commit()

    def stop(self):
        self.running = False

    def _execute_cycle(self, stock_codes: List[str]):
        signals = self.strategy_engine.get_all_signals(stock_codes)
        signals = self.strategy_engine.resolve_conflicts(signals)

        for signal in signals:
            passed, reason = self.risk_control.check(signal, self.user_id)
            if passed:
                import asyncio
                asyncio.run(self.fund_manager.execute_trade(signal, self.user_id))

    def get_status(self) -> Dict[str, Any]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id,
            Trade.trade_time >= today
        ).all()

        today_pnl = sum(t.total_amount * 0.02 for t in today_trades if t.trade_type == "SELL")

        active_tasks = self.db.query(AutoTradeTask).filter(
            AutoTradeTask.user_id == self.user_id,
            AutoTradeTask.enabled == True
        ).count()

        active_strategies = len(self.strategy_engine.strategies)

        return {
            "running": self.running,
            "active_tasks": active_tasks,
            "active_strategies": active_strategies,
            "today_trades": len(today_trades),
            "today_pnl": today_pnl
        }

    def get_statistics(self) -> Dict[str, Any]:
        trades = self.db.query(Trade).filter(Trade.user_id == self.user_id).all()

        if not trades:
            return {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate": 0.0, "total_pnl": 0.0, "avg_pnl_per_trade": 0.0,
                "max_win": 0.0, "max_loss": 0.0
            }

        sell_trades = [t for t in trades if t.trade_type == "SELL"]
        pnls = [t.total_amount * 0.02 for t in sell_trades]
        winning = sum(1 for p in pnls if p > 0)
        losing = sum(1 for p in pnls if p < 0)

        return {
            "total_trades": len(trades),
            "winning_trades": winning,
            "losing_trades": losing,
            "win_rate": winning / len(sell_trades) if sell_trades else 0.0,
            "total_pnl": sum(pnls),
            "avg_pnl_per_trade": sum(pnls) / len(pnls) if pnls else 0.0,
            "max_win": max(pnls) if pnls else 0.0,
            "max_loss": min(pnls) if pnls else 0.0
        }
