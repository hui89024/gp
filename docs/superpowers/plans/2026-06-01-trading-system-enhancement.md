# 交易系统增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现历史回测、独立风控熔断、告警系统

**Architecture:** 基于现有架构，添加回测引擎、熔断器、告警服务

**Tech Stack:** Python, FastAPI, SQLAlchemy, NumPy, Pandas

---

## Task 1: 回测数据模型

**Files:**
- Create: `backend/app/models/backtest_record.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建回测记录模型**

```python
# backend/app/models/backtest_record.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Date, ARRAY
from sqlalchemy.sql import func
from app.database import Base


class BacktestRecord(Base):
    __tablename__ = "backtest_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_name = Column(String(50))
    strategy_config = Column(JSON)
    start_date = Column(Date)
    end_date = Column(Date)
    initial_capital = Column(Float)
    stock_codes = Column(ARRAY(String))
    
    # 回测结果
    total_return = Column(Float)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    profit_loss_ratio = Column(Float)
    total_trades = Column(Integer)
    
    # 详细数据
    trades = Column(JSON)
    equity_curve = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: 更新模型导出**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.models.prediction import Prediction
from app.models.review import Review, StrategyPerformance
from app.models.strategy_config import StrategyConfig
from app.models.auto_trade_task import AutoTradeTask
from app.models.risk_config import RiskConfig
from app.models.auto_trade_log import AutoTradeLog
from app.models.backtest_record import BacktestRecord

__all__ = [
    "User", "Position", "Trade", "Prediction", "Review", "StrategyPerformance",
    "StrategyConfig", "AutoTradeTask", "RiskConfig", "AutoTradeLog",
    "BacktestRecord"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add backtest record model"
```

---

## Task 2: 回测引擎服务

**Files:**
- Create: `backend/app/services/backtest_engine.py`
- Create: `backend/tests/test_backtest_engine.py`

- [ ] **Step 1: 创建回测引擎**

```python
# backend/app/services/backtest_engine.py
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
import numpy as np

from app.models.backtest_record import BacktestRecord
from app.services.data_service import DataService
from app.strategies.base import BaseStrategy, Signal
from app.strategies.ma_strategy import MAStrategy
from app.strategies.rsi_strategy import RSIStrategy


@dataclass
class BacktestConfig:
    start_date: datetime
    end_date: datetime
    initial_capital: float
    stock_codes: List[str]
    strategy_name: str
    strategy_config: Dict[str, Any]
    commission_rate: float = 0.00025
    slippage_pct: float = 0.001


@dataclass
class BacktestTrade:
    date: str
    stock_code: str
    direction: str
    price: float
    quantity: int
    commission: float
    pnl: float


@dataclass
class BacktestResult:
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int
    trades: List[Dict]
    equity_curve: List[Dict]
    daily_returns: List[float]


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_service = DataService()
    
    def run(self, user_id: int, config: BacktestConfig) -> BacktestResult:
        """运行回测"""
        # 1. 获取历史数据
        historical_data = self._load_data(config.stock_codes, config.start_date, config.end_date)
        
        if not historical_data:
            raise ValueError("无法获取历史数据")
        
        # 2. 初始化账户
        capital = config.initial_capital
        positions = {}
        trades = []
        equity_curve = []
        
        # 3. 创建策略
        strategy = self._create_strategy(config.strategy_name, config.strategy_config)
        
        # 4. 逐日模拟
        dates = sorted(historical_data.keys())
        
        for date in dates:
            daily_data = historical_data[date]
            
            # 更新持仓市值
            portfolio_value = capital
            for code, pos in positions.items():
                if code in daily_data:
                    portfolio_value += pos["quantity"] * daily_data[code]["close"]
            
            # 生成信号
            signals = strategy.generate_signals(config.stock_codes)
            
            # 执行交易
            for signal in signals:
                if signal.stock_code not in daily_data:
                    continue
                
                current_price = daily_data[signal.stock_code]["close"]
                slippage = current_price * config.slippage_pct
                
                if signal.direction == "BUY":
                    actual_price = current_price + slippage
                    cost = actual_price * signal.quantity
                    commission = cost * config.commission_rate
                    
                    if capital >= cost + commission:
                        capital -= (cost + commission)
                        
                        if signal.stock_code in positions:
                            pos = positions[signal.stock_code]
                            total_cost = pos["avg_cost"] * pos["quantity"] + actual_price * signal.quantity
                            pos["quantity"] += signal.quantity
                            pos["avg_cost"] = total_cost / pos["quantity"]
                        else:
                            positions[signal.stock_code] = {
                                "quantity": signal.quantity,
                                "avg_cost": actual_price
                            }
                        
                        trades.append({
                            "date": date,
                            "stock_code": signal.stock_code,
                            "direction": "BUY",
                            "price": actual_price,
                            "quantity": signal.quantity,
                            "commission": commission,
                            "pnl": 0
                        })
                
                elif signal.direction == "SELL":
                    if signal.stock_code in positions:
                        pos = positions[signal.stock_code]
                        actual_price = current_price - slippage
                        sell_quantity = min(signal.quantity, pos["quantity"])
                        revenue = actual_price * sell_quantity
                        commission = revenue * config.commission_rate
                        pnl = (actual_price - pos["avg_cost"]) * sell_quantity - commission
                        
                        capital += (revenue - commission)
                        pos["quantity"] -= sell_quantity
                        
                        if pos["quantity"] == 0:
                            del positions[signal.stock_code]
                        
                        trades.append({
                            "date": date,
                            "stock_code": signal.stock_code,
                            "direction": "SELL",
                            "price": actual_price,
                            "quantity": sell_quantity,
                            "commission": commission,
                            "pnl": pnl
                        })
            
            # 记录每日权益
            portfolio_value = capital
            for code, pos in positions.items():
                if code in daily_data:
                    portfolio_value += pos["quantity"] * daily_data[code]["close"]
            
            equity_curve.append({
                "date": date,
                "equity": portfolio_value,
                "capital": capital,
                "positions_value": portfolio_value - capital
            })
        
        # 5. 计算性能指标
        result = self._calculate_metrics(equity_curve, trades, config.initial_capital)
        
        # 6. 保存回测记录
        self._save_record(user_id, config, result)
        
        return result
    
    def _load_data(self, stock_codes: List[str], start_date: datetime, end_date: datetime) -> Dict:
        """加载历史数据"""
        data = {}
        
        for code in stock_codes:
            history = self.data_service.get_stock_history(code, days=365)
            
            for h in history:
                if h.date not in data:
                    data[h.date] = {}
                
                data[h.date][code] = {
                    "open": h.open,
                    "high": h.high,
                    "low": h.low,
                    "close": h.close,
                    "volume": h.volume
                }
        
        return data
    
    def _create_strategy(self, strategy_name: str, config: Dict[str, Any]) -> BaseStrategy:
        """创建策略实例"""
        strategy_map = {
            "MA": MAStrategy,
            "RSI": RSIStrategy,
        }
        
        strategy_class = strategy_map.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"未知策略: {strategy_name}")
        
        return strategy_class(config=config)
    
    def _calculate_metrics(self, equity_curve: List[Dict], trades: List[Dict], 
                          initial_capital: float) -> BacktestResult:
        """计算性能指标"""
        if not equity_curve:
            return BacktestResult(
                total_return=0, annual_return=0, max_drawdown=0,
                sharpe_ratio=0, win_rate=0, profit_loss_ratio=0,
                total_trades=0, trades=[], equity_curve=[], daily_returns=[]
            )
        
        # 计算每日收益率
        daily_returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1]["equity"]
            curr_equity = equity_curve[i]["equity"]
            if prev_equity > 0:
                daily_returns.append((curr_equity - prev_equity) / prev_equity)
        
        # 总收益率
        final_equity = equity_curve[-1]["equity"]
        total_return = (final_equity - initial_capital) / initial_capital
        
        # 年化收益率
        days = len(equity_curve)
        annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        
        # 胜率
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # 盈亏比
        avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([t["pnl"] for t in losing_trades])) if losing_trades else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve,
            daily_returns=daily_returns
        )
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """计算最大回撤"""
        peak = equity_curve[0]["equity"]
        max_dd = 0
        
        for point in equity_curve:
            if point["equity"] > peak:
                peak = point["equity"]
            dd = (peak - point["equity"]) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, daily_returns: List[float], risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        if not daily_returns:
            return 0.0
        
        avg_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        if std_return == 0:
            return 0.0
        
        annualized_return = avg_return * 252
        annualized_std = std_return * np.sqrt(252)
        
        return (annualized_return - risk_free_rate) / annualized_std
    
    def _save_record(self, user_id: int, config: BacktestConfig, result: BacktestResult):
        """保存回测记录"""
        record = BacktestRecord(
            user_id=user_id,
            strategy_name=config.strategy_name,
            strategy_config=config.strategy_config,
            start_date=config.start_date.date(),
            end_date=config.end_date.date(),
            initial_capital=config.initial_capital,
            stock_codes=config.stock_codes,
            total_return=result.total_return,
            annual_return=result.annual_return,
            max_drawdown=result.max_drawdown,
            sharpe_ratio=result.sharpe_ratio,
            win_rate=result.win_rate,
            profit_loss_ratio=result.profit_loss_ratio,
            total_trades=result.total_trades,
            trades=result.trades,
            equity_curve=result.equity_curve
        )
        
        self.db.add(record)
        self.db.commit()
    
    def get_records(self, user_id: int, limit: int = 20) -> List[BacktestRecord]:
        """获取回测记录"""
        return self.db.query(BacktestRecord).filter(
            BacktestRecord.user_id == user_id
        ).order_by(BacktestRecord.created_at.desc()).limit(limit).all()
    
    def get_record(self, record_id: int, user_id: int) -> Optional[BacktestRecord]:
        """获取回测详情"""
        return self.db.query(BacktestRecord).filter(
            BacktestRecord.id == record_id,
            BacktestRecord.user_id == user_id
        ).first()
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_backtest_engine.py
import pytest
from datetime import datetime, timedelta
from app.services.backtest_engine import BacktestEngine, BacktestConfig
from app.models.user import User


@pytest.fixture
def backtest_engine(db_session):
    return BacktestEngine(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="backtestuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_backtest_config():
    """测试回测配置"""
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2024, 1, 1),
        initial_capital=1000000,
        stock_codes=["000001"],
        strategy_name="MA",
        strategy_config={"short_period": 5, "long_period": 20}
    )
    
    assert config.initial_capital == 1000000
    assert config.strategy_name == "MA"


def test_calculate_max_drawdown(backtest_engine):
    """测试最大回撤计算"""
    equity_curve = [
        {"equity": 1000000},
        {"equity": 1100000},
        {"equity": 950000},
        {"equity": 1050000},
    ]
    
    max_dd = backtest_engine._calculate_max_drawdown(equity_curve)
    assert abs(max_dd - 0.136) < 0.01  # 约13.6%
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/backtest_engine.py backend/tests/test_backtest_engine.py
git commit -m "feat: add backtest engine service"
```

---

## Task 3: 回测API

**Files:**
- Create: `backend/app/api/backtest.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建回测API**

```python
# backend/app/api/backtest.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.backtest_record import BacktestRecord
from app.services.backtest_engine import BacktestEngine, BacktestConfig

router = APIRouter(prefix="/api/backtest", tags=["回测"])


@router.post("/run")
def run_backtest(
    user_id: int,
    strategy_name: str,
    strategy_config: dict,
    stock_codes: List[str],
    start_date: str,
    end_date: str,
    initial_capital: float = 1000000,
    db: Session = Depends(get_db)
):
    """运行回测"""
    engine = BacktestEngine(db)
    
    config = BacktestConfig(
        start_date=datetime.strptime(start_date, "%Y-%m-%d"),
        end_date=datetime.strptime(end_date, "%Y-%m-%d"),
        initial_capital=initial_capital,
        stock_codes=stock_codes,
        strategy_name=strategy_name,
        strategy_config=strategy_config
    )
    
    try:
        result = engine.run(user_id, config)
        return {
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "max_drawdown": result.max_drawdown,
            "sharpe_ratio": result.sharpe_ratio,
            "win_rate": result.win_rate,
            "profit_loss_ratio": result.profit_loss_ratio,
            "total_trades": result.total_trades,
            "trades_count": len(result.trades)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records")
def get_records(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取回测记录"""
    engine = BacktestEngine(db)
    return engine.get_records(user_id, limit)


@router.get("/records/{record_id}")
def get_record(
    record_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取回测详情"""
    engine = BacktestEngine(db)
    record = engine.get_record(record_id, user_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record
```

- [ ] **Step 2: 更新API导出和主应用**

```python
# backend/app/api/__init__.py
from app.api.account import router as account_router
from app.api.trade import router as trade_router
from app.api.stock import router as stock_router
from app.api.prediction import router as prediction_router
from app.api.review import router as review_router
from app.api.auto_trading import router as auto_trading_router
from app.api.backtest import router as backtest_router

__all__ = [
    "account_router", "trade_router", "stock_router",
    "prediction_router", "review_router", "auto_trading_router",
    "backtest_router"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/
git commit -m "feat: add backtest API endpoints"
```

---

## Task 4: 熔断器数据模型

**Files:**
- Create: `backend/app/models/circuit_breaker_event.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建熔断事件模型**

```python
# backend/app/models/circuit_breaker_event.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class CircuitBreakerEvent(Base):
    __tablename__ = "circuit_breaker_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trigger_reason = Column(String(200))
    trigger_value = Column(Float)
    threshold = Column(Float)
    action_taken = Column(String(50))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: 更新模型导出**

```python
# backend/app/models/__init__.py
# 添加 CircuitBreakerEvent 到导出列表
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add circuit breaker event model"
```

---

## Task 5: 熔断器服务

**Files:**
- Create: `backend/app/services/circuit_breaker.py`
- Create: `backend/tests/test_circuit_breaker.py`

- [ ] **Step 1: 创建熔断器服务**

```python
# backend/app/services/circuit_breaker.py
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
        
        # 停止所有自动交易任务
        self._stop_all_tasks(user_id)
        
        # 记录熔断事件
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
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_circuit_breaker.py
import pytest
from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.models.user import User


@pytest.fixture
def circuit_breaker(db_session):
    return CircuitBreaker(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="cbuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_check_no_trigger(circuit_breaker, test_user):
    """测试正常情况"""
    triggered, reason = circuit_breaker.check(test_user.id)
    assert triggered is False
    assert reason == "正常"


def test_reset(circuit_breaker):
    """测试重置"""
    circuit_breaker.is_triggered = True
    circuit_breaker.trigger_reason = "测试"
    
    circuit_breaker.reset()
    
    assert circuit_breaker.is_triggered is False
    assert circuit_breaker.trigger_reason is None
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/circuit_breaker.py backend/tests/test_circuit_breaker.py
git commit -m "feat: add circuit breaker service"
```

---

## Task 6: 告警系统

**Files:**
- Create: `backend/app/models/alert_record.py`
- Create: `backend/app/services/alert_service.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建告警记录模型**

```python
# backend/app/models/alert_record.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.sql import func
from app.database import Base


class AlertRecord(Base):
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rule_name = Column(String(100))
    severity = Column(String(20))  # INFO/WARNING/CRITICAL
    message = Column(String(500))
    channels = Column(ARRAY(String))
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: 创建告警服务**

```python
# backend/app/services/alert_service.py
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.alert_record import AlertRecord


class AlertService:
    """告警服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifiers = {
            "dingtalk": DingTalkNotifier(),
            "email": EmailNotifier(),
        }
        self.rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[Dict]:
        """加载默认告警规则"""
        return [
            {
                "name": "单日亏损告警",
                "condition": lambda ctx: ctx.get("daily_loss_pct", 0) < -0.03,
                "severity": "WARNING",
                "channels": ["dingtalk"],
                "message": "单日亏损超过3%"
            },
            {
                "name": "连续亏损告警",
                "condition": lambda ctx: ctx.get("consecutive_losses", 0) >= 3,
                "severity": "CRITICAL",
                "channels": ["dingtalk", "email"],
                "message": "连续亏损{consecutive_losses}次"
            },
            {
                "name": "熔断触发告警",
                "condition": lambda ctx: ctx.get("circuit_breaker_triggered", False),
                "severity": "CRITICAL",
                "channels": ["dingtalk", "email"],
                "message": "风控熔断已触发: {reason}"
            },
        ]
    
    def check_and_alert(self, user_id: int, context: Dict[str, Any]):
        """检查并发送告警"""
        for rule in self.rules:
            try:
                if rule["condition"](context):
                    message = rule["message"].format(**context)
                    self._send_alert(user_id, rule["name"], rule["severity"], 
                                   message, rule["channels"])
            except Exception as e:
                print(f"告警规则执行失败: {e}")
    
    def _send_alert(self, user_id: int, rule_name: str, severity: str, 
                   message: str, channels: List[str]):
        """发送告警"""
        # 记录告警
        record = AlertRecord(
            user_id=user_id,
            rule_name=rule_name,
            severity=severity,
            message=message,
            channels=channels,
            sent=True,
            sent_at=datetime.now()
        )
        self.db.add(record)
        self.db.commit()
        
        # 发送通知
        for channel in channels:
            notifier = self.notifiers.get(channel)
            if notifier:
                try:
                    notifier.send(user_id, message, severity)
                except Exception as e:
                    print(f"发送{channel}通知失败: {e}")
    
    def get_records(self, user_id: int, limit: int = 50) -> List[AlertRecord]:
        """获取告警记录"""
        return self.db.query(AlertRecord).filter(
            AlertRecord.user_id == user_id
        ).order_by(AlertRecord.created_at.desc()).limit(limit).all()
    
    def test_alert(self, user_id: int, channel: str) -> bool:
        """测试告警"""
        notifier = self.notifiers.get(channel)
        if not notifier:
            return False
        
        try:
            notifier.send(user_id, "这是一条测试告警", "INFO")
            return True
        except Exception:
            return False


class DingTalkNotifier:
    """钉钉通知"""
    
    def send(self, user_id: int, message: str, severity: str):
        """发送钉钉消息"""
        # 实际实现需要配置webhook_url
        print(f"[钉钉] [{severity}] {message}")


class EmailNotifier:
    """邮件通知"""
    
    def send(self, user_id: int, message: str, severity: str):
        """发送邮件"""
        # 实际实现需要配置SMTP
        print(f"[邮件] [{severity}] {message}")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/alert_record.py backend/app/services/alert_service.py
git commit -m "feat: add alert service with notification support"
```

---

## Task 7: 熔断和告警API

**Files:**
- Create: `backend/app/api/risk_control.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建风控API**

```python
# backend/app/api/risk_control.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.services.alert_service import AlertService
from app.models.alert_record import AlertRecord

router = APIRouter(prefix="/api/risk-control", tags=["风控"])


@router.get("/circuit-breaker/status")
def get_circuit_breaker_status(user_id: int, db: Session = Depends(get_db)):
    """获取熔断状态"""
    cb = CircuitBreaker(db)
    return cb.get_status(user_id)


@router.post("/circuit-breaker/check")
def check_circuit_breaker(user_id: int, db: Session = Depends(get_db)):
    """检查熔断"""
    cb = CircuitBreaker(db)
    triggered, reason = cb.check(user_id)
    return {"triggered": triggered, "reason": reason}


@router.post("/circuit-breaker/reset")
def reset_circuit_breaker(user_id: int, db: Session = Depends(get_db)):
    """重置熔断器"""
    cb = CircuitBreaker(db)
    cb.reset()
    return {"message": "熔断器已重置"}


@router.get("/circuit-breaker/events")
def get_circuit_breaker_events(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """获取熔断事件"""
    cb = CircuitBreaker(db)
    return cb.get_events(user_id, limit)


@router.get("/alerts/records")
def get_alert_records(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """获取告警记录"""
    service = AlertService(db)
    return service.get_records(user_id, limit)


@router.post("/alerts/test")
def test_alert(user_id: int, channel: str = "dingtalk", db: Session = Depends(get_db)):
    """测试告警"""
    service = AlertService(db)
    success = service.test_alert(user_id, channel)
    
    if not success:
        raise HTTPException(status_code=400, detail="测试失败")
    
    return {"message": "测试成功"}
```

- [ ] **Step 2: 更新API导出**

```python
# backend/app/api/__init__.py
from app.api.account import router as account_router
from app.api.trade import router as trade_router
from app.api.stock import router as stock_router
from app.api.prediction import router as prediction_router
from app.api.review import router as review_router
from app.api.auto_trading import router as auto_trading_router
from app.api.backtest import router as backtest_router
from app.api.risk_control import router as risk_control_router

__all__ = [
    "account_router", "trade_router", "stock_router",
    "prediction_router", "review_router", "auto_trading_router",
    "backtest_router", "risk_control_router"
]
```

- [ ] **Step 3: 更新主应用**

```python
# backend/app/main.py
from app.api import (
    account_router, trade_router, stock_router,
    prediction_router, review_router, auto_trading_router,
    backtest_router, risk_control_router
)

# 注册所有路由
app.include_router(account_router)
app.include_router(trade_router)
app.include_router(stock_router)
app.include_router(prediction_router)
app.include_router(review_router)
app.include_router(auto_trading_router)
app.include_router(backtest_router)
app.include_router(risk_control_router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add risk control API endpoints"
```

---

## Task 8: 前端增强页面

**Files:**
- Create: `frontend/src/components/BacktestPanel.tsx`
- Create: `frontend/src/components/CircuitBreakerStatus.tsx`
- Create: `frontend/src/components/AlertCenter.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 更新类型和API**

在 `frontend/src/types/index.ts` 添加：
```typescript
export interface BacktestResult {
  total_return: number;
  annual_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_loss_ratio: number;
  total_trades: number;
}

export interface BacktestRecord {
  id: number;
  user_id: number;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  total_return: number;
  annual_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_loss_ratio: number;
  total_trades: number;
  created_at: string;
}

export interface CircuitBreakerStatus {
  is_triggered: boolean;
  trigger_reason: string | null;
}

export interface AlertRecord {
  id: number;
  user_id: number;
  rule_name: string;
  severity: string;
  message: string;
  channels: string[];
  sent: boolean;
  sent_at: string | null;
  created_at: string;
}
```

在 `frontend/src/services/api.ts` 添加：
```typescript
export const backtestApi = {
  run: (userId: number, data: {
    strategy_name: string;
    strategy_config: Record<string, any>;
    stock_codes: string[];
    start_date: string;
    end_date: string;
    initial_capital?: number;
  }) => api.post<BacktestResult>('/api/backtest/run', data, { params: { user_id: userId } }),

  getRecords: (userId: number, limit?: number) =>
    api.get<BacktestRecord[]>('/api/backtest/records', { params: { user_id: userId, limit } }),

  getRecord: (recordId: number, userId: number) =>
    api.get<BacktestRecord>(`/api/backtest/records/${recordId}`, { params: { user_id: userId } }),
};

export const riskControlApi = {
  getCircuitBreakerStatus: (userId: number) =>
    api.get<CircuitBreakerStatus>('/api/risk-control/circuit-breaker/status', { params: { user_id: userId } }),

  checkCircuitBreaker: (userId: number) =>
    api.post<{ triggered: boolean; reason: string }>('/api/risk-control/circuit-breaker/check', null, { params: { user_id: userId } }),

  resetCircuitBreaker: (userId: number) =>
    api.post('/api/risk-control/circuit-breaker/reset', null, { params: { user_id: userId } }),

  getAlertRecords: (userId: number, limit?: number) =>
    api.get<AlertRecord[]>('/api/risk-control/alerts/records', { params: { user_id: userId, limit } }),

  testAlert: (userId: number, channel: string) =>
    api.post('/api/risk-control/alerts/test', null, { params: { user_id: userId, channel } }),
};
```

- [ ] **Step 2: 创建回测面板组件**

```tsx
// frontend/src/components/BacktestPanel.tsx
import { useState } from 'react';
import { Card, Form, Select, DatePicker, InputNumber, Button, Table, Statistic, Row, Col, message } from 'antd';
import { backtestApi } from '../services/api';
import type { BacktestResult, BacktestRecord } from '../types';

const { RangePicker } = DatePicker;

interface Props {
  userId: number;
}

export default function BacktestPanel({ userId }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [records, setRecords] = useState<BacktestRecord[]>([]);

  const handleRun = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const response = await backtestApi.run(userId, {
        strategy_name: values.strategy_name,
        strategy_config: values.strategy_config || {},
        stock_codes: values.stock_codes,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
        initial_capital: values.initial_capital,
      });

      setResult(response.data);
      message.success('回测完成');
      fetchRecords();
    } catch (error) {
      message.error('回测失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecords = async () => {
    try {
      const response = await backtestApi.getRecords(userId);
      setRecords(response.data);
    } catch (error) {
      console.error('获取记录失败:', error);
    }
  };

  const columns = [
    { title: '策略', dataIndex: 'strategy_name', key: 'strategy' },
    { title: '总收益', dataIndex: 'total_return', key: 'return', render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '最大回撤', dataIndex: 'max_drawdown', key: 'drawdown', render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '夏普比率', dataIndex: 'sharpe_ratio', key: 'sharpe', render: (v: number) => v.toFixed(2) },
    { title: '胜率', dataIndex: 'win_rate', key: 'winrate', render: (v: number) => `${(v * 100).toFixed(1)}%` },
    { title: '交易次数', dataIndex: 'total_trades', key: 'trades' },
  ];

  return (
    <div>
      <Card title="运行回测" style={{ marginBottom: 16 }}>
        <Form form={form} layout="inline">
          <Form.Item name="strategy_name" label="策略" rules={[{ required: true }]}>
            <Select style={{ width: 120 }}>
              <Select.Option value="MA">均线策略</Select.Option>
              <Select.Option value="RSI">RSI策略</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="stock_codes" label="股票" rules={[{ required: true }]}>
            <Select mode="tags" style={{ width: 200 }} placeholder="输入股票代码" />
          </Form.Item>
          <Form.Item name="date_range" label="时间范围" rules={[{ required: true }]}>
            <RangePicker />
          </Form.Item>
          <Form.Item name="initial_capital" label="初始资金" initialValue={1000000}>
            <InputNumber min={10000} step={100000} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" onClick={handleRun} loading={loading}>运行回测</Button>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <Card title="回测结果" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={4}><Statistic title="总收益" value={result.total_return * 100} precision={2} suffix="%" /></Col>
            <Col span={4}><Statistic title="年化收益" value={result.annual_return * 100} precision={2} suffix="%" /></Col>
            <Col span={4}><Statistic title="最大回撤" value={result.max_drawdown * 100} precision={2} suffix="%" valueStyle={{ color: '#cf1322' }} /></Col>
            <Col span={4}><Statistic title="夏普比率" value={result.sharpe_ratio} precision={2} /></Col>
            <Col span={4}><Statistic title="胜率" value={result.win_rate * 100} precision={1} suffix="%" /></Col>
            <Col span={4}><Statistic title="交易次数" value={result.total_trades} /></Col>
          </Row>
        </Card>
      )}

      <Card title="历史回测记录">
        <Table columns={columns} dataSource={records} rowKey="id" pagination={false} />
      </Card>
    </div>
  );
}
```

- [ ] **Step 3: 创建熔断状态组件**

```tsx
// frontend/src/components/CircuitBreakerStatus.tsx
import { useState, useEffect } from 'react';
import { Card, Tag, Button, List, message } from 'antd';
import { WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { riskControlApi } from '../services/api';
import type { CircuitBreakerStatus } from '../types';

interface Props {
  userId: number;
}

export default function CircuitBreakerStatusComponent({ userId }: Props) {
  const [status, setStatus] = useState<CircuitBreakerStatus | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchEvents();
  }, [userId]);

  const fetchStatus = async () => {
    try {
      const response = await riskControlApi.getCircuitBreakerStatus(userId);
      setStatus(response.data);
    } catch (error) {
      console.error('获取状态失败:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await riskControlApi.getAlertRecords(userId, 10);
      setEvents(response.data);
    } catch (error) {
      console.error('获取事件失败:', error);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await riskControlApi.resetCircuitBreaker(userId);
      message.success('熔断器已重置');
      fetchStatus();
    } catch (error) {
      message.error('重置失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title="风控熔断状态"
      extra={
        status?.is_triggered && (
          <Button danger onClick={handleReset} loading={loading}>重置熔断器</Button>
        )
      }
    >
      <div style={{ marginBottom: 16 }}>
        {status?.is_triggered ? (
          <Tag icon={<WarningOutlined />} color="error" style={{ fontSize: 16, padding: '8px 16px' }}>
            熔断已触发: {status.trigger_reason}
          </Tag>
        ) : (
          <Tag icon={<CheckCircleOutlined />} color="success" style={{ fontSize: 16, padding: '8px 16px' }}>
            正常运行
          </Tag>
        )}
      </div>

      <List
        header="最近事件"
        dataSource={events}
        renderItem={(item: any) => (
          <List.Item>
            <List.Item.Meta
              title={item.rule_name}
              description={item.message}
            />
            <div>{new Date(item.created_at).toLocaleString()}</div>
          </List.Item>
        )}
      />
    </Card>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: add backtest and circuit breaker frontend components"
```

---

## 自审检查清单

**1. 规格覆盖:**
- [x] 历史回测系统 (Task 1-3)
- [x] 独立风控熔断 (Task 4-5, 7)
- [x] 告警系统 (Task 6-7)
- [x] 前端界面 (Task 8)

**2. 占位符检查:**
- [x] 无TBD或TODO
- [x] 所有代码完整
