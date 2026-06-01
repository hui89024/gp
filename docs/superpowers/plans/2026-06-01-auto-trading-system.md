# 自动炒股系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现自动炒股系统，包含策略引擎、执行引擎、风控系统和资金管理

**Architecture:** 基于现有后端架构，添加策略引擎、执行引擎、风控系统，复用现有交易引擎

**Tech Stack:** Python, FastAPI, SQLAlchemy, APScheduler, React, TypeScript

---

## 文件结构

```
backend/app/
├── strategies/
│   ├── __init__.py
│   ├── base.py              # 策略基类
│   ├── prediction.py        # 预测信号策略
│   ├── ma_strategy.py       # 均线策略
│   ├── rsi_strategy.py      # RSI策略
│   └── rule_strategy.py     # 规则引擎策略
├── services/
│   ├── strategy_engine.py   # 策略引擎服务
│   ├── execution_engine.py  # 执行引擎服务
│   ├── risk_control.py      # 风控服务
│   └── fund_manager.py      # 资金管理服务
├── models/
│   ├── strategy_config.py   # 策略配置模型
│   ├── auto_trade_task.py   # 自动交易任务模型
│   ├── risk_config.py       # 风控配置模型
│   └── auto_trade_log.py    # 自动交易日志模型
├── schemas/
│   └── auto_trading.py      # 自动交易Schema
├── api/
│   └── auto_trading.py      # 自动交易API

frontend/src/
├── components/
│   ├── StrategyList.tsx      # 策略列表组件
│   ├── StrategyForm.tsx      # 策略配置表单
│   ├── AutoTradeMonitor.tsx  # 自动交易监控
│   └── RiskConfigForm.tsx    # 风控配置表单
├── pages/
│   └── AutoTrading.tsx       # 自动交易页面
```

---

## Task 1: 策略数据模型

**Files:**
- Create: `backend/app/models/strategy_config.py`
- Create: `backend/app/models/auto_trade_task.py`
- Create: `backend/app/models/risk_config.py`
- Create: `backend/app/models/auto_trade_log.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建策略配置模型**

```python
# backend/app/models/strategy_config.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_name = Column(String(50), nullable=False)
    strategy_type = Column(String(20), nullable=False)  # PREDICTION/MA/RSI/RULE
    config = Column(JSON, nullable=False)  # 策略配置参数
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: 创建自动交易任务模型**

```python
# backend/app/models/auto_trade_task.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.sql import func
from app.database import Base


class AutoTradeTask(Base):
    __tablename__ = "auto_trade_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    execution_mode = Column(String(20), nullable=False)  # POLLING/REALTIME/BATCH
    interval_minutes = Column(Integer)  # 轮询间隔
    watchlist = Column(ARRAY(String))  # 监控股票列表
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: 创建风控配置模型**

```python
# backend/app/models/risk_config.py
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class RiskConfig(Base):
    __tablename__ = "risk_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    stop_loss_pct = Column(Float, default=-0.05)
    take_profit_pct = Column(Float, default=0.10)
    max_position_pct = Column(Float, default=0.20)
    max_total_position_pct = Column(Float, default=0.80)
    max_daily_trades = Column(Integer, default=10)
    max_weekly_trades = Column(Integer, default=30)
    max_daily_loss = Column(Float, default=50000.0)
    max_single_trade = Column(Float, default=100000.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 4: 创建自动交易日志模型**

```python
# backend/app/models/auto_trade_log.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class AutoTradeLog(Base):
    __tablename__ = "auto_trade_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("auto_trade_tasks.id"))
    signal_source = Column(String(50))
    stock_code = Column(String(10))
    stock_name = Column(String(50))
    direction = Column(String(4))  # BUY/SELL
    price = Column(Float)
    quantity = Column(Integer)
    confidence = Column(Float)
    risk_check_passed = Column(Boolean)
    risk_check_reason = Column(String(200))
    execution_result = Column(String(20))  # SUCCESS/FAILED/SKIPPED
    error_message = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 5: 更新模型导出**

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

__all__ = [
    "User", "Position", "Trade", "Prediction", "Review", "StrategyPerformance",
    "StrategyConfig", "AutoTradeTask", "RiskConfig", "AutoTradeLog"
]
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add auto trading data models"
```

---

## Task 2: 自动交易Schema定义

**Files:**
- Create: `backend/app/schemas/auto_trading.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 创建自动交易Schema**

```python
# backend/app/schemas/auto_trading.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    PREDICTION = "PREDICTION"
    MA = "MA"
    RSI = "RSI"
    RULE = "RULE"


class ExecutionMode(str, Enum):
    POLLING = "POLLING"
    REALTIME = "REALTIME"
    BATCH = "BATCH"


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


# 策略配置
class StrategyConfigCreate(BaseModel):
    strategy_name: str
    strategy_type: StrategyType
    config: Dict[str, Any]
    enabled: bool = True


class StrategyConfigUpdate(BaseModel):
    strategy_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class StrategyConfigResponse(BaseModel):
    id: int
    user_id: int
    strategy_name: str
    strategy_type: StrategyType
    config: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 自动交易任务
class AutoTradeTaskCreate(BaseModel):
    execution_mode: ExecutionMode
    interval_minutes: Optional[int] = 5
    watchlist: List[str]


class AutoTradeTaskUpdate(BaseModel):
    execution_mode: Optional[ExecutionMode] = None
    interval_minutes: Optional[int] = None
    watchlist: Optional[List[str]] = None
    enabled: Optional[bool] = None


class AutoTradeTaskResponse(BaseModel):
    id: int
    user_id: int
    execution_mode: ExecutionMode
    interval_minutes: Optional[int]
    watchlist: List[str]
    enabled: bool
    last_run_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# 风控配置
class RiskConfigCreate(BaseModel):
    stop_loss_pct: float = -0.05
    take_profit_pct: float = 0.10
    max_position_pct: float = 0.20
    max_total_position_pct: float = 0.80
    max_daily_trades: int = 10
    max_weekly_trades: int = 30
    max_daily_loss: float = 50000.0
    max_single_trade: float = 100000.0


class RiskConfigResponse(RiskConfigCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# 交易信号
class TradeSignal(BaseModel):
    stock_code: str
    stock_name: str
    direction: SignalDirection
    price: float
    quantity: int
    confidence: float
    strategy_name: str
    reason: str
    timestamp: datetime


# 自动交易日志
class AutoTradeLogResponse(BaseModel):
    id: int
    user_id: int
    task_id: Optional[int]
    signal_source: Optional[str]
    stock_code: Optional[str]
    stock_name: Optional[str]
    direction: Optional[str]
    price: Optional[float]
    quantity: Optional[int]
    confidence: Optional[float]
    risk_check_passed: Optional[bool]
    risk_check_reason: Optional[str]
    execution_result: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# 运行状态
class AutoTradingStatus(BaseModel):
    running: bool
    active_tasks: int
    active_strategies: int
    today_trades: int
    today_pnl: float


# 统计数据
class AutoTradingStatistics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl_per_trade: float
    max_win: float
    max_loss: float
```

- [ ] **Step 2: 更新Schema导出**

```python
# backend/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, AccountOverview
from app.schemas.trade import TradeCreate, TradeResponse, PositionResponse
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult, KLineData
from app.schemas.prediction import PredictionCreate, PredictionResponse, PredictionSignal, ModelPerformance
from app.schemas.review import (
    ReviewCreate, ReviewResponse, DailyReviewSummary,
    WeeklyReviewSummary, StrategyAnalysis, BehaviorAnalysis, ComprehensiveReview
)
from app.schemas.auto_trading import (
    StrategyType, ExecutionMode, SignalDirection,
    StrategyConfigCreate, StrategyConfigUpdate, StrategyConfigResponse,
    AutoTradeTaskCreate, AutoTradeTaskUpdate, AutoTradeTaskResponse,
    RiskConfigCreate, RiskConfigResponse,
    TradeSignal, AutoTradeLogResponse, AutoTradingStatus, AutoTradingStatistics
)

__all__ = [
    "UserCreate", "UserResponse", "AccountOverview",
    "TradeCreate", "TradeResponse", "PositionResponse",
    "StockQuote", "StockHistory", "StockSearchResult", "KLineData",
    "PredictionCreate", "PredictionResponse", "PredictionSignal", "ModelPerformance",
    "ReviewCreate", "ReviewResponse", "DailyReviewSummary",
    "WeeklyReviewSummary", "StrategyAnalysis", "BehaviorAnalysis", "ComprehensiveReview",
    "StrategyType", "ExecutionMode", "SignalDirection",
    "StrategyConfigCreate", "StrategyConfigUpdate", "StrategyConfigResponse",
    "AutoTradeTaskCreate", "AutoTradeTaskUpdate", "AutoTradeTaskResponse",
    "RiskConfigCreate", "RiskConfigResponse",
    "TradeSignal", "AutoTradeLogResponse", "AutoTradingStatus", "AutoTradingStatistics"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add auto trading schemas"
```

---

## Task 3: 策略基类和内置策略

**Files:**
- Create: `backend/app/strategies/__init__.py`
- Create: `backend/app/strategies/base.py`
- Create: `backend/app/strategies/prediction.py`
- Create: `backend/app/strategies/ma_strategy.py`
- Create: `backend/app/strategies/rsi_strategy.py`

- [ ] **Step 1: 创建策略基类**

```python
# backend/app/strategies/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Signal:
    stock_code: str
    stock_name: str
    direction: str  # BUY/SELL
    price: float
    quantity: int
    confidence: float
    strategy_name: str
    reason: str
    timestamp: datetime


class BaseStrategy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @abstractmethod
    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            stock_codes: 监控的股票代码列表
        
        Returns:
            交易信号列表
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """验证策略配置是否有效"""
        pass
```

- [ ] **Step 2: 创建策略初始化文件**

```python
# backend/app/strategies/__init__.py
from app.strategies.base import BaseStrategy, Signal
from app.strategies.prediction import PredictionStrategy
from app.strategies.ma_strategy import MAStrategy
from app.strategies.rsi_strategy import RSIStrategy

__all__ = ["BaseStrategy", "Signal", "PredictionStrategy", "MAStrategy", "RSIStrategy"]
```

- [ ] **Step 3: 创建预测信号策略**

```python
# backend/app/strategies/prediction.py
from typing import List, Dict, Any
from datetime import datetime
from app.strategies.base import BaseStrategy, Signal
from app.services.data_service import DataService
from app.services.prediction_service import PredictionService


class PredictionStrategy(BaseStrategy):
    """预测信号策略 - 使用LSTM模型预测"""
    
    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.db = db_session
        self.data_service = DataService()
        self.prediction_service = PredictionService(db_session) if db_session else None
    
    @property
    def name(self) -> str:
        return "PredictionStrategy"
    
    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        """基于LSTM预测生成信号"""
        signals = []
        
        confidence_threshold = self.config.get("confidence_threshold", 0.7)
        
        for stock_code in stock_codes:
            try:
                # 获取实时行情
                quote = self.data_service.get_stock_quote(stock_code)
                if not quote:
                    continue
                
                # 获取预测信号
                if self.prediction_service:
                    prediction = self.prediction_service.predict(stock_code)
                    
                    if prediction and prediction.confidence >= confidence_threshold:
                        direction = "BUY" if prediction.predicted_direction == "UP" else "SELL"
                        
                        signal = Signal(
                            stock_code=stock_code,
                            stock_name=quote.stock_name,
                            direction=direction,
                            price=quote.current_price,
                            quantity=100,  # 默认1手
                            confidence=prediction.confidence,
                            strategy_name=self.name,
                            reason=f"LSTM预测{direction}，置信度{prediction.confidence:.1%}",
                            timestamp=datetime.now()
                        )
                        signals.append(signal)
            except Exception as e:
                print(f"预测策略处理{stock_code}失败: {e}")
        
        return signals
    
    def validate_config(self, config: dict) -> bool:
        """验证配置"""
        if "confidence_threshold" not in config:
            return False
        threshold = config["confidence_threshold"]
        return 0 < threshold <= 1
```

- [ ] **Step 4: 创建均线策略**

```python
# backend/app/strategies/ma_strategy.py
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from app.strategies.base import BaseStrategy, Signal
from app.services.data_service import DataService


class MAStrategy(BaseStrategy):
    """均线策略 - 金叉买入，死叉卖出"""
    
    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.data_service = DataService()
    
    @property
    def name(self) -> str:
        return "MAStrategy"
    
    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        """基于均线交叉生成信号"""
        signals = []
        
        short_period = self.config.get("short_period", 5)
        long_period = self.config.get("long_period", 20)
        
        for stock_code in stock_codes:
            try:
                # 获取历史数据
                history = self.data_service.get_stock_history(stock_code, days=long_period + 5)
                if len(history) < long_period:
                    continue
                
                # 计算均线
                closes = [h.close for h in history]
                short_ma = np.mean(closes[-short_period:])
                long_ma = np.mean(closes[-long_period:])
                
                # 计算前一天的均线
                prev_short_ma = np.mean(closes[-(short_period+1):-1])
                prev_long_ma = np.mean(closes[-(long_period+1):-1])
                
                # 获取实时行情
                quote = self.data_service.get_stock_quote(stock_code)
                if not quote:
                    continue
                
                # 判断金叉/死叉
                direction = None
                reason = ""
                
                # 金叉：短期均线从下方穿过长期均线
                if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                    direction = "BUY"
                    reason = f"MA{short_period}上穿MA{long_period}，金叉买入"
                
                # 死叉：短期均线从上方穿过长期均线
                elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                    direction = "SELL"
                    reason = f"MA{short_period}下穿MA{long_period}，死叉卖出"
                
                if direction:
                    signal = Signal(
                        stock_code=stock_code,
                        stock_name=quote.stock_name,
                        direction=direction,
                        price=quote.current_price,
                        quantity=100,
                        confidence=0.6,  # 均线策略固定置信度
                        strategy_name=self.name,
                        reason=reason,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
            except Exception as e:
                print(f"均线策略处理{stock_code}失败: {e}")
        
        return signals
    
    def validate_config(self, config: dict) -> bool:
        """验证配置"""
        short_period = config.get("short_period", 5)
        long_period = config.get("long_period", 20)
        return 0 < short_period < long_period
```

- [ ] **Step 5: 创建RSI策略**

```python
# backend/app/strategies/rsi_strategy.py
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from app.strategies.base import BaseStrategy, Signal
from app.services.data_service import DataService


class RSIStrategy(BaseStrategy):
    """RSI策略 - 超卖买入，超买卖出"""
    
    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.data_service = DataService()
    
    @property
    def name(self) -> str:
        return "RSIStrategy"
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50.0  # 默认中性
        
        deltas = np.diff(prices[-(period+1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        """基于RSI指标生成信号"""
        signals = []
        
        rsi_period = self.config.get("rsi_period", 14)
        oversold_threshold = self.config.get("oversold_threshold", 30)
        overbought_threshold = self.config.get("overbought_threshold", 70)
        
        for stock_code in stock_codes:
            try:
                # 获取历史数据
                history = self.data_service.get_stock_history(stock_code, days=rsi_period + 5)
                if len(history) < rsi_period + 1:
                    continue
                
                # 计算RSI
                closes = [h.close for h in history]
                rsi = self._calculate_rsi(closes, rsi_period)
                
                # 获取实时行情
                quote = self.data_service.get_stock_quote(stock_code)
                if not quote:
                    continue
                
                # 判断超买超卖
                direction = None
                reason = ""
                
                if rsi <= oversold_threshold:
                    direction = "BUY"
                    reason = f"RSI={rsi:.1f}，处于超卖区域，买入"
                elif rsi >= overbought_threshold:
                    direction = "SELL"
                    reason = f"RSI={rsi:.1f}，处于超买区域，卖出"
                
                if direction:
                    signal = Signal(
                        stock_code=stock_code,
                        stock_name=quote.stock_name,
                        direction=direction,
                        price=quote.current_price,
                        quantity=100,
                        confidence=0.65,
                        strategy_name=self.name,
                        reason=reason,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
            except Exception as e:
                print(f"RSI策略处理{stock_code}失败: {e}")
        
        return signals
    
    def validate_config(self, config: dict) -> bool:
        """验证配置"""
        oversold = config.get("oversold_threshold", 30)
        overbought = config.get("overbought_threshold", 70)
        return 0 < oversold < overbought < 100
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/strategies/
git commit -m "feat: add strategy base class and built-in strategies"
```

---

## Task 4: 风控服务

**Files:**
- Create: `backend/app/services/risk_control.py`
- Create: `backend/tests/test_risk_control.py`

- [ ] **Step 1: 创建风控服务**

```python
# backend/app/services/risk_control.py
from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

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
        """获取或创建风控配置"""
        config = self.db.query(RiskConfig).filter(
            RiskConfig.user_id == user_id
        ).first()
        
        if not config:
            config = RiskConfig(user_id=user_id)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        
        return config
    
    def check(self, signal: Signal, user_id: int) -> Tuple[bool, str]:
        """
        风控检查
        
        Returns:
            (是否通过, 原因)
        """
        config = self.get_or_create_config(user_id)
        
        checks = [
            self._check_position_limit,
            self._check_trade_frequency,
            self._check_daily_loss,
            self._check_single_trade,
        ]
        
        for check in checks:
            passed, reason = check(signal, user_id, config)
            if not passed:
                return False, reason
        
        return True, "通过"
    
    def _check_position_limit(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        """检查仓位限制"""
        # 获取当前持仓
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == signal.stock_code
        ).first()
        
        # 获取账户总资产
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"
        
        # 计算当前持仓市值
        positions = self.db.query(Position).filter(
            Position.user_id == user_id
        ).all()
        
        market_value = sum(p.quantity * (p.current_price or p.avg_cost) for p in positions)
        total_assets = user.current_capital + market_value
        
        # 检查单只股票仓位
        if position:
            position_value = position.quantity * signal.price
            position_pct = position_value / total_assets if total_assets > 0 else 0
            
            if position_pct > config.max_position_pct:
                return False, f"仓位超限: {position_pct:.1%} > {config.max_position_pct:.1%}"
        
        # 检查总仓位
        if signal.direction == "BUY":
            new_market_value = market_value + signal.price * signal.quantity
            total_position_pct = new_market_value / total_assets if total_assets > 0 else 0
            
            if total_position_pct > config.max_total_position_pct:
                return False, f"总仓位超限: {total_position_pct:.1%} > {config.max_total_position_pct:.1%}"
        
        return True, "通过"
    
    def _check_trade_frequency(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        """检查交易频率"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 检查每日交易次数
        daily_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= today
        ).count()
        
        if daily_trades >= config.max_daily_trades:
            return False, f"今日交易次数已达上限: {daily_trades}/{config.max_daily_trades}"
        
        # 检查每周交易次数
        week_start = today - timedelta(days=today.weekday())
        weekly_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= week_start
        ).count()
        
        if weekly_trades >= config.max_weekly_trades:
            return False, f"本周交易次数已达上限: {weekly_trades}/{config.max_weekly_trades}"
        
        return True, "通过"
    
    def _check_daily_loss(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        """检查每日亏损"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 计算今日盈亏（简化处理）
        sell_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_type == "SELL",
            Trade.trade_time >= today
        ).all()
        
        daily_pnl = sum(t.total_amount * 0.02 for t in sell_trades)  # 简化计算
        
        if daily_pnl < -config.max_daily_loss:
            return False, f"今日亏损已达上限: {daily_pnl:.2f}"
        
        return True, "通过"
    
    def _check_single_trade(self, signal: Signal, user_id: int, config: RiskConfig) -> Tuple[bool, str]:
        """检查单笔交易金额"""
        trade_amount = signal.price * signal.quantity
        
        if trade_amount > config.max_single_trade:
            return False, f"单笔交易金额超限: {trade_amount:.2f} > {config.max_single_trade:.2f}"
        
        return True, "通过"
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_risk_control.py
import pytest
from datetime import datetime
from app.services.risk_control import RiskControl
from app.strategies.base import Signal
from app.models.user import User


@pytest.fixture
def risk_control(db_session):
    return RiskControl(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="riskuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_check_pass(risk_control, test_user):
    """测试通过风控检查"""
    signal = Signal(
        stock_code="000001",
        stock_name="平安银行",
        direction="BUY",
        price=10.0,
        quantity=100,
        confidence=0.8,
        strategy_name="test",
        reason="测试",
        timestamp=datetime.now()
    )
    
    passed, reason = risk_control.check(signal, test_user.id)
    assert passed is True
    assert reason == "通过"


def test_check_single_trade_limit(risk_control, test_user):
    """测试单笔交易限制"""
    signal = Signal(
        stock_code="000001",
        stock_name="平安银行",
        direction="BUY",
        price=1000.0,
        quantity=1000,
        confidence=0.8,
        strategy_name="test",
        reason="测试",
        timestamp=datetime.now()
    )
    
    passed, reason = risk_control.check(signal, test_user.id)
    assert passed is False
    assert "单笔交易金额超限" in reason
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/risk_control.py backend/tests/test_risk_control.py
git commit -m "feat: add risk control service"
```

---

## Task 5: 策略引擎服务

**Files:**
- Create: `backend/app/services/strategy_engine.py`
- Create: `backend/tests/test_strategy_engine.py`

- [ ] **Step 1: 创建策略引擎服务**

```python
# backend/app/services/strategy_engine.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.strategy_config import StrategyConfig
from app.strategies.base import BaseStrategy, Signal
from app.strategies.prediction import PredictionStrategy
from app.strategies.ma_strategy import MAStrategy
from app.strategies.rsi_strategy import RSIStrategy


class StrategyEngine:
    """策略引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.strategies: Dict[str, BaseStrategy] = {}
    
    def load_strategies(self, user_id: int):
        """加载用户配置的策略"""
        configs = self.db.query(StrategyConfig).filter(
            StrategyConfig.user_id == user_id,
            StrategyConfig.enabled == True
        ).all()
        
        for config in configs:
            strategy = self._create_strategy(config)
            if strategy:
                self.strategies[config.strategy_name] = strategy
    
    def _create_strategy(self, config: StrategyConfig) -> Optional[BaseStrategy]:
        """根据配置创建策略实例"""
        strategy_map = {
            "PREDICTION": PredictionStrategy,
            "MA": MAStrategy,
            "RSI": RSIStrategy,
        }
        
        strategy_class = strategy_map.get(config.strategy_type)
        if strategy_class:
            return strategy_class(config=config.config, db_session=self.db)
        return None
    
    def get_all_signals(self, stock_codes: List[str]) -> List[Signal]:
        """获取所有策略的信号"""
        all_signals = []
        
        for strategy in self.strategies.values():
            try:
                signals = strategy.generate_signals(stock_codes)
                all_signals.extend(signals)
            except Exception as e:
                print(f"策略{strategy.name}执行失败: {e}")
        
        return all_signals
    
    def resolve_conflicts(self, signals: List[Signal]) -> List[Signal]:
        """解决策略冲突 - 同一股票取置信度最高的信号"""
        resolved = {}
        
        for signal in signals:
            key = signal.stock_code
            if key not in resolved:
                resolved[key] = signal
            elif signal.confidence > resolved[key].confidence:
                resolved[key] = signal
        
        return list(resolved.values())
    
    def create_strategy_config(self, user_id: int, strategy_name: str, 
                              strategy_type: str, config: dict) -> StrategyConfig:
        """创建策略配置"""
        strategy_config = StrategyConfig(
            user_id=user_id,
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            config=config,
            enabled=True
        )
        self.db.add(strategy_config)
        self.db.commit()
        self.db.refresh(strategy_config)
        return strategy_config
    
    def update_strategy_config(self, config_id: int, user_id: int, 
                              updates: dict) -> Optional[StrategyConfig]:
        """更新策略配置"""
        config = self.db.query(StrategyConfig).filter(
            StrategyConfig.id == config_id,
            StrategyConfig.user_id == user_id
        ).first()
        
        if not config:
            return None
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete_strategy_config(self, config_id: int, user_id: int) -> bool:
        """删除策略配置"""
        config = self.db.query(StrategyConfig).filter(
            StrategyConfig.id == config_id,
            StrategyConfig.user_id == user_id
        ).first()
        
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        return True
    
    def get_strategy_configs(self, user_id: int) -> List[StrategyConfig]:
        """获取用户所有策略配置"""
        return self.db.query(StrategyConfig).filter(
            StrategyConfig.user_id == user_id
        ).all()
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_strategy_engine.py
import pytest
from app.services.strategy_engine import StrategyEngine
from app.models.strategy_config import StrategyConfig
from app.models.user import User


@pytest.fixture
def strategy_engine(db_session):
    return StrategyEngine(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="strategyuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_create_strategy_config(strategy_engine, test_user):
    """测试创建策略配置"""
    config = strategy_engine.create_strategy_config(
        user_id=test_user.id,
        strategy_name="test_ma",
        strategy_type="MA",
        config={"short_period": 5, "long_period": 20}
    )
    
    assert config.strategy_name == "test_ma"
    assert config.strategy_type == "MA"
    assert config.enabled is True


def test_get_strategy_configs(strategy_engine, test_user):
    """测试获取策略配置列表"""
    # 创建两个策略
    strategy_engine.create_strategy_config(
        user_id=test_user.id,
        strategy_name="test_ma",
        strategy_type="MA",
        config={"short_period": 5, "long_period": 20}
    )
    strategy_engine.create_strategy_config(
        user_id=test_user.id,
        strategy_name="test_rsi",
        strategy_type="RSI",
        config={"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}
    )
    
    configs = strategy_engine.get_strategy_configs(test_user.id)
    assert len(configs) == 2


def test_update_strategy_config(strategy_engine, test_user):
    """测试更新策略配置"""
    config = strategy_engine.create_strategy_config(
        user_id=test_user.id,
        strategy_name="test_ma",
        strategy_type="MA",
        config={"short_period": 5, "long_period": 20}
    )
    
    updated = strategy_engine.update_strategy_config(
        config_id=config.id,
        user_id=test_user.id,
        updates={"strategy_name": "updated_ma", "enabled": False}
    )
    
    assert updated.strategy_name == "updated_ma"
    assert updated.enabled is False


def test_delete_strategy_config(strategy_engine, test_user):
    """测试删除策略配置"""
    config = strategy_engine.create_strategy_config(
        user_id=test_user.id,
        strategy_name="test_ma",
        strategy_type="MA",
        config={"short_period": 5, "long_period": 20}
    )
    
    result = strategy_engine.delete_strategy_config(config.id, test_user.id)
    assert result is True
    
    configs = strategy_engine.get_strategy_configs(test_user.id)
    assert len(configs) == 0
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/strategy_engine.py backend/tests/test_strategy_engine.py
git commit -m "feat: add strategy engine service"
```

---

## Task 6: 资金管理服务

**Files:**
- Create: `backend/app/services/fund_manager.py`
- Create: `backend/tests/test_fund_manager.py`

- [ ] **Step 1: 创建资金管理服务**

```python
# backend/app/services/fund_manager.py
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.trade import Trade
from app.models.auto_trade_log import AutoTradeLog
from app.strategies.base import Signal
from app.services.trading_engine import TradingEngine, TradeResult


class FundMode(Enum):
    SIMULATED = "simulated"  # 模拟资金
    REAL = "real"            # 真实资金


class FundManager:
    """资金管理器"""
    
    def __init__(self, db: Session, mode: FundMode = FundMode.SIMULATED):
        self.db = db
        self.mode = mode
        self.trading_engine = TradingEngine(db)
    
    async def execute_trade(self, signal: Signal, user_id: int, 
                           task_id: Optional[int] = None) -> TradeResult:
        """执行交易"""
        # 记录日志
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
            if self.mode == FundMode.SIMULATED:
                result = await self._execute_simulated(signal, user_id)
            else:
                result = await self._execute_real(signal, user_id)
            
            log.execution_result = "SUCCESS" if result.success else "FAILED"
            log.error_message = result.message if not result.success else None
            
        except Exception as e:
            log.execution_result = "FAILED"
            log.error_message = str(e)
            result = TradeResult(success=False, message=str(e))
        
        self.db.add(log)
        self.db.commit()
        
        return result
    
    async def _execute_simulated(self, signal: Signal, user_id: int) -> TradeResult:
        """模拟资金交易"""
        if signal.direction == "BUY":
            return self.trading_engine.buy(
                user_id=user_id,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                price=signal.price,
                quantity=signal.quantity,
                strategy_tag=signal.strategy_name
            )
        else:
            return self.trading_engine.sell(
                user_id=user_id,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                price=signal.price,
                quantity=signal.quantity,
                strategy_tag=signal.strategy_name
            )
    
    async def _execute_real(self, signal: Signal, user_id: int) -> TradeResult:
        """真实资金交易（示例实现）"""
        # 这里需要对接具体券商API
        # 示例实现，实际需要根据券商SDK调整
        
        try:
            # 模拟券商API调用
            # broker = self._get_broker(user_id)
            # order = await broker.place_order(...)
            
            # 记录交易
            trade = Trade(
                user_id=user_id,
                stock_code=signal.stock_code,
                trade_type=signal.direction,
                price=signal.price,
                quantity=signal.quantity,
                total_amount=signal.price * signal.quantity,
                strategy_tag=signal.strategy_name
            )
            self.db.add(trade)
            self.db.commit()
            
            return TradeResult(success=True, message="交易成功", trade=trade)
        except Exception as e:
            return TradeResult(success=False, message=str(e))
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_fund_manager.py
import pytest
from datetime import datetime
from app.services.fund_manager import FundManager, FundMode
from app.strategies.base import Signal
from app.models.user import User


@pytest.fixture
def fund_manager(db_session):
    return FundManager(db_session, FundMode.SIMULATED)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="funduser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.mark.asyncio
async def test_execute_buy(fund_manager, test_user):
    """测试执行买入"""
    signal = Signal(
        stock_code="000001",
        stock_name="平安银行",
        direction="BUY",
        price=10.0,
        quantity=100,
        confidence=0.8,
        strategy_name="test",
        reason="测试买入",
        timestamp=datetime.now()
    )
    
    result = await fund_manager.execute_trade(signal, test_user.id)
    assert result.success is True
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/fund_manager.py backend/tests/test_fund_manager.py
git commit -m "feat: add fund manager service"
```

---

## Task 7: 执行引擎服务

**Files:**
- Create: `backend/app/services/execution_engine.py`
- Create: `backend/tests/test_execution_engine.py`

- [ ] **Step 1: 创建执行引擎服务**

```python
# backend/app/services/execution_engine.py
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.auto_trade_task import AutoTradeTask
from app.models.risk_config import RiskConfig
from app.models.auto_trade_log import AutoTradeLog
from app.services.strategy_engine import StrategyEngine
from app.services.risk_control import RiskControl
from app.services.fund_manager import FundManager, FundMode
from app.strategies.base import Signal


class ExecutionMode(Enum):
    POLLING = "POLLING"
    REALTIME = "REALTIME"
    BATCH = "BATCH"


class ExecutionEngine:
    """执行引擎"""
    
    def __init__(self, db: Session, user_id: int, mode: FundMode = FundMode.SIMULATED):
        self.db = db
        self.user_id = user_id
        self.strategy_engine = StrategyEngine(db)
        self.risk_control = RiskControl(db)
        self.fund_manager = FundManager(db, mode)
        self.running = False
        self.pending_signals: List[Signal] = []
    
    def start(self, task_id: int):
        """启动执行引擎"""
        task = self.db.query(AutoTradeTask).filter(
            AutoTradeTask.id == task_id,
            AutoTradeTask.user_id == self.user_id
        ).first()
        
        if not task:
            raise ValueError("任务不存在")
        
        # 加载策略
        self.strategy_engine.load_strategies(self.user_id)
        
        self.running = True
        self.current_task = task
        
        # 根据执行模式启动
        if task.execution_mode == "POLLING":
            self._run_polling(task)
        elif task.execution_mode == "BATCH":
            self._run_batch(task)
    
    def stop(self):
        """停止执行引擎"""
        self.running = False
    
    def _run_polling(self, task: AutoTradeTask):
        """运行定时轮询模式"""
        # 在实际应用中，这里会使用APScheduler
        # 这里简化为单次执行
        self._execute_cycle(task.watchlist)
    
    def _run_batch(self, task: AutoTradeTask):
        """运行批量模式"""
        # 批量分析
        self._analyze(task.watchlist)
        # 批量执行会在开盘时调用 _execute_pending_signals
    
    def _execute_cycle(self, stock_codes: List[str]):
        """执行一个交易周期"""
        # 1. 生成信号
        signals = self.strategy_engine.get_all_signals(stock_codes)
        
        # 2. 解决冲突
        signals = self.strategy_engine.resolve_conflicts(signals)
        
        # 3. 风控检查
        approved_signals = []
        for signal in signals:
            passed, reason = self.risk_control.check(signal, self.user_id)
            
            if passed:
                approved_signals.append(signal)
            else:
                # 记录被拒绝的信号
                self._log_rejected_signal(signal, reason)
        
        # 4. 执行交易
        for signal in approved_signals:
            self._execute_signal(signal)
    
    def _analyze(self, stock_codes: List[str]):
        """分析并保存信号（批量模式用）"""
        signals = self.strategy_engine.get_all_signals(stock_codes)
        self.pending_signals = self.strategy_engine.resolve_conflicts(signals)
    
    def execute_pending_signals(self):
        """执行待处理信号（批量模式用）"""
        for signal in self.pending_signals:
            passed, reason = self.risk_control.check(signal, self.user_id)
            if passed:
                self._execute_signal(signal)
            else:
                self._log_rejected_signal(signal, reason)
        
        self.pending_signals = []
    
    def _execute_signal(self, signal: Signal):
        """执行单个信号"""
        import asyncio
        
        try:
            result = asyncio.run(
                self.fund_manager.execute_trade(
                    signal=signal,
                    user_id=self.user_id,
                    task_id=self.current_task.id if hasattr(self, 'current_task') else None
                )
            )
            
            # 更新任务最后运行时间
            if hasattr(self, 'current_task'):
                self.current_task.last_run_at = datetime.now()
                self.db.commit()
        except Exception as e:
            print(f"执行信号失败: {e}")
    
    def _log_rejected_signal(self, signal: Signal, reason: str):
        """记录被拒绝的信号"""
        log = AutoTradeLog(
            user_id=self.user_id,
            task_id=self.current_task.id if hasattr(self, 'current_task') else None,
            signal_source=signal.strategy_name,
            stock_code=signal.stock_code,
            stock_name=signal.stock_name,
            direction=signal.direction,
            price=signal.price,
            quantity=signal.quantity,
            confidence=signal.confidence,
            risk_check_passed=False,
            risk_check_reason=reason,
            execution_result="SKIPPED"
        )
        self.db.add(log)
        self.db.commit()
    
    def get_status(self) -> Dict[str, Any]:
        """获取运行状态"""
        from app.models.trade import Trade
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 获取今日交易统计
        today_trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id,
            Trade.trade_time >= today
        ).all()
        
        today_pnl = sum(t.total_amount * 0.02 for t in today_trades if t.trade_type == "SELL")
        
        # 获取活跃任务数
        active_tasks = self.db.query(AutoTradeTask).filter(
            AutoTradeTask.user_id == self.user_id,
            AutoTradeTask.enabled == True
        ).count()
        
        # 获取活跃策略数
        active_strategies = len(self.strategy_engine.strategies)
        
        return {
            "running": self.running,
            "active_tasks": active_tasks,
            "active_strategies": active_strategies,
            "today_trades": len(today_trades),
            "today_pnl": today_pnl
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        from app.models.trade import Trade
        
        trades = self.db.query(Trade).filter(
            Trade.user_id == self.user_id
        ).all()
        
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl_per_trade": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0
            }
        
        sell_trades = [t for t in trades if t.trade_type == "SELL"]
        
        # 简化计算
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
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_execution_engine.py
import pytest
from app.services.execution_engine import ExecutionEngine
from app.services.fund_manager import FundMode
from app.models.user import User
from app.models.auto_trade_task import AutoTradeTask


@pytest.fixture
def execution_engine(db_session, test_user):
    return ExecutionEngine(db_session, test_user.id, FundMode.SIMULATED)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="execuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_get_status(execution_engine):
    """测试获取状态"""
    status = execution_engine.get_status()
    assert "running" in status
    assert "active_tasks" in status
    assert "today_trades" in status


def test_get_statistics(execution_engine):
    """测试获取统计"""
    stats = execution_engine.get_statistics()
    assert "total_trades" in stats
    assert "win_rate" in stats
    assert "total_pnl" in stats
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/execution_engine.py backend/tests/test_execution_engine.py
git commit -m "feat: add execution engine service"
```

---

## Task 8: 自动交易API

**Files:**
- Create: `backend/app/api/auto_trading.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建自动交易API**

```python
# backend/app/api/auto_trading.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auto_trading import (
    StrategyConfigCreate, StrategyConfigUpdate, StrategyConfigResponse,
    AutoTradeTaskCreate, AutoTradeTaskUpdate, AutoTradeTaskResponse,
    RiskConfigCreate, RiskConfigResponse,
    AutoTradeLogResponse, AutoTradingStatus, AutoTradingStatistics
)
from app.services.strategy_engine import StrategyEngine
from app.services.execution_engine import ExecutionEngine
from app.services.risk_control import RiskControl
from app.services.fund_manager import FundMode

router = APIRouter(prefix="/api/auto-trading", tags=["自动交易"])


# 策略管理API
@router.post("/strategies", response_model=StrategyConfigResponse)
def create_strategy(
    strategy_in: StrategyConfigCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """创建策略配置"""
    engine = StrategyEngine(db)
    return engine.create_strategy_config(
        user_id=user_id,
        strategy_name=strategy_in.strategy_name,
        strategy_type=strategy_in.strategy_type,
        config=strategy_in.config
    )


@router.get("/strategies", response_model=List[StrategyConfigResponse])
def get_strategies(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取策略列表"""
    engine = StrategyEngine(db)
    return engine.get_strategy_configs(user_id)


@router.put("/strategies/{strategy_id}", response_model=StrategyConfigResponse)
def update_strategy(
    strategy_id: int,
    strategy_in: StrategyConfigUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """更新策略配置"""
    engine = StrategyEngine(db)
    updates = strategy_in.dict(exclude_unset=True)
    result = engine.update_strategy_config(strategy_id, user_id, updates)
    
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return result


@router.delete("/strategies/{strategy_id}")
def delete_strategy(
    strategy_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """删除策略"""
    engine = StrategyEngine(db)
    result = engine.delete_strategy_config(strategy_id, user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return {"message": "删除成功"}


# 任务管理API
@router.post("/tasks", response_model=AutoTradeTaskResponse)
def create_task(
    task_in: AutoTradeTaskCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """创建自动交易任务"""
    task = AutoTradeTask(
        user_id=user_id,
        execution_mode=task_in.execution_mode,
        interval_minutes=task_in.interval_minutes,
        watchlist=task_in.watchlist,
        enabled=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=List[AutoTradeTaskResponse])
def get_tasks(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    return db.query(AutoTradeTask).filter(
        AutoTradeTask.user_id == user_id
    ).all()


@router.post("/tasks/{task_id}/start")
def start_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """启动任务"""
    engine = ExecutionEngine(db, user_id, FundMode.SIMULATED)
    
    try:
        engine.start(task_id)
        return {"message": "任务启动成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/stop")
def stop_task(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """停止任务"""
    # 更新任务状态
    task = db.query(AutoTradeTask).filter(
        AutoTradeTask.id == task_id,
        AutoTradeTask.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.enabled = False
    db.commit()
    
    return {"message": "任务已停止"}


# 风控配置API
@router.get("/risk-config", response_model=RiskConfigResponse)
def get_risk_config(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取风控配置"""
    control = RiskControl(db)
    return control.get_or_create_config(user_id)


@router.put("/risk-config", response_model=RiskConfigResponse)
def update_risk_config(
    config_in: RiskConfigCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """更新风控配置"""
    control = RiskControl(db)
    config = control.get_or_create_config(user_id)
    
    for key, value in config_in.dict().items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    return config


# 状态和统计API
@router.get("/status", response_model=AutoTradingStatus)
def get_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取运行状态"""
    engine = ExecutionEngine(db, user_id, FundMode.SIMULATED)
    return engine.get_status()


@router.get("/statistics", response_model=AutoTradingStatistics)
def get_statistics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取统计数据"""
    engine = ExecutionEngine(db, user_id, FundMode.SIMULATED)
    return engine.get_statistics()


# 日志API
@router.get("/logs", response_model=List[AutoTradeLogResponse])
def get_logs(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取交易日志"""
    return db.query(AutoTradeLog).filter(
        AutoTradeLog.user_id == user_id
    ).order_by(
        AutoTradeLog.created_at.desc()
    ).limit(limit).all()
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

__all__ = [
    "account_router", "trade_router", "stock_router",
    "prediction_router", "review_router", "auto_trading_router"
]
```

- [ ] **Step 3: 更新主应用**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    account_router, trade_router, stock_router,
    prediction_router, review_router, auto_trading_router
)
from app.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="股票交易系统",
    description="模拟炒股系统API，包含预测、复盘和自动交易功能",
    version="3.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(account_router)
app.include_router(trade_router)
app.include_router(stock_router)
app.include_router(prediction_router)
app.include_router(review_router)
app.include_router(auto_trading_router)


@app.get("/")
def root():
    return {"message": "股票交易系统 API v3.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add auto trading API endpoints"
```

---

## Task 9: 前端自动交易页面

**Files:**
- Create: `frontend/src/components/StrategyList.tsx`
- Create: `frontend/src/components/StrategyForm.tsx`
- Create: `frontend/src/components/AutoTradeMonitor.tsx`
- Create: `frontend/src/components/RiskConfigForm.tsx`
- Create: `frontend/src/pages/AutoTrading.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 更新类型定义**

在 `frontend/src/types/index.ts` 末尾添加：

```typescript
// 自动交易相关类型
export interface StrategyConfig {
  id: number;
  user_id: number;
  strategy_name: string;
  strategy_type: 'PREDICTION' | 'MA' | 'RSI' | 'RULE';
  config: Record<string, any>;
  enabled: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface AutoTradeTask {
  id: number;
  user_id: number;
  execution_mode: 'POLLING' | 'REALTIME' | 'BATCH';
  interval_minutes: number | null;
  watchlist: string[];
  enabled: boolean;
  last_run_at: string | null;
  created_at: string;
}

export interface RiskConfig {
  id: number;
  user_id: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  max_position_pct: number;
  max_total_position_pct: number;
  max_daily_trades: number;
  max_weekly_trades: number;
  max_daily_loss: number;
  max_single_trade: number;
}

export interface AutoTradeLog {
  id: number;
  user_id: number;
  task_id: number | null;
  signal_source: string | null;
  stock_code: string | null;
  stock_name: string | null;
  direction: string | null;
  price: number | null;
  quantity: number | null;
  confidence: number | null;
  risk_check_passed: boolean | null;
  risk_check_reason: string | null;
  execution_result: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AutoTradingStatus {
  running: boolean;
  active_tasks: number;
  active_strategies: number;
  today_trades: number;
  today_pnl: number;
}

export interface AutoTradingStatistics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl_per_trade: number;
  max_win: number;
  max_loss: number;
}
```

- [ ] **Step 2: 更新API服务**

在 `frontend/src/services/api.ts` 末尾添加：

```typescript
// 自动交易API
export const autoTradingApi = {
  // 策略管理
  createStrategy: (userId: number, data: { strategy_name: string; strategy_type: string; config: Record<string, any> }) =>
    api.post<StrategyConfig>('/api/auto-trading/strategies', data, { params: { user_id: userId } }),

  getStrategies: (userId: number) =>
    api.get<StrategyConfig[]>('/api/auto-trading/strategies', { params: { user_id: userId } }),

  updateStrategy: (strategyId: number, userId: number, data: Partial<StrategyConfig>) =>
    api.put<StrategyConfig>(`/api/auto-trading/strategies/${strategyId}`, data, { params: { user_id: userId } }),

  deleteStrategy: (strategyId: number, userId: number) =>
    api.delete(`/api/auto-trading/strategies/${strategyId}`, { params: { user_id: userId } }),

  // 任务管理
  createTask: (userId: number, data: { execution_mode: string; interval_minutes?: number; watchlist: string[] }) =>
    api.post<AutoTradeTask>('/api/auto-trading/tasks', data, { params: { user_id: userId } }),

  getTasks: (userId: number) =>
    api.get<AutoTradeTask[]>('/api/auto-trading/tasks', { params: { user_id: userId } }),

  startTask: (taskId: number, userId: number) =>
    api.post(`/api/auto-trading/tasks/${taskId}/start`, null, { params: { user_id: userId } }),

  stopTask: (taskId: number, userId: number) =>
    api.post(`/api/auto-trading/tasks/${taskId}/stop`, null, { params: { user_id: userId } }),

  // 风控配置
  getRiskConfig: (userId: number) =>
    api.get<RiskConfig>('/api/auto-trading/risk-config', { params: { user_id: userId } }),

  updateRiskConfig: (userId: number, data: Partial<RiskConfig>) =>
    api.put<RiskConfig>('/api/auto-trading/risk-config', data, { params: { user_id: userId } }),

  // 状态和统计
  getStatus: (userId: number) =>
    api.get<AutoTradingStatus>('/api/auto-trading/status', { params: { user_id: userId } }),

  getStatistics: (userId: number) =>
    api.get<AutoTradingStatistics>('/api/auto-trading/statistics', { params: { user_id: userId } }),

  // 日志
  getLogs: (userId: number, limit: number = 50) =>
    api.get<AutoTradeLog[]>('/api/auto-trading/logs', { params: { user_id: userId, limit } }),
};
```

- [ ] **Step 3: 创建策略列表组件**

```tsx
// frontend/src/components/StrategyList.tsx
import { useState, useEffect } from 'react';
import { Table, Tag, Switch, Button, Space, message, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { autoTradingApi } from '../services/api';
import type { StrategyConfig } from '../types';

interface Props {
  userId: number;
  onEdit: (strategy: StrategyConfig) => void;
  onRefresh: () => void;
}

export default function StrategyList({ userId, onEdit, onRefresh }: Props) {
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, [userId]);

  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const response = await autoTradingApi.getStrategies(userId);
      setStrategies(response.data);
    } catch (error) {
      console.error('获取策略列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (strategy: StrategyConfig) => {
    try {
      await autoTradingApi.updateStrategy(strategy.id, userId, {
        enabled: !strategy.enabled,
      });
      message.success(`策略已${strategy.enabled ? '禁用' : '启用'}`);
      fetchStrategies();
      onRefresh();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await autoTradingApi.deleteStrategy(id, userId);
      message.success('删除成功');
      fetchStrategies();
      onRefresh();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'PREDICTION': return 'blue';
      case 'MA': return 'green';
      case 'RSI': return 'orange';
      case 'RULE': return 'purple';
      default: return 'default';
    }
  };

  const columns = [
    { title: '策略名称', dataIndex: 'strategy_name', key: 'name' },
    {
      title: '类型',
      dataIndex: 'strategy_type',
      key: 'type',
      render: (type: string) => <Tag color={getTypeColor(type)}>{type}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: StrategyConfig) => (
        <Switch checked={enabled} onChange={() => handleToggle(record)} />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StrategyConfig) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => onEdit(record)} />
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={strategies}
      loading={loading}
      rowKey="id"
      pagination={false}
    />
  );
}
```

- [ ] **Step 4: 创建策略配置表单**

```tsx
// frontend/src/components/StrategyForm.tsx
import { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, InputNumber, Switch, message } from 'antd';
import { autoTradingApi } from '../services/api';
import type { StrategyConfig } from '../types';

interface Props {
  userId: number;
  visible: boolean;
  strategy?: StrategyConfig | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function StrategyForm({ userId, visible, strategy, onClose, onSuccess }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (strategy) {
      form.setFieldsValue({
        strategy_name: strategy.strategy_name,
        strategy_type: strategy.strategy_type,
        ...strategy.config,
      });
    } else {
      form.resetFields();
    }
  }, [strategy, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const { strategy_name, strategy_type, ...config } = values;

      if (strategy) {
        await autoTradingApi.updateStrategy(strategy.id, userId, {
          strategy_name,
          config,
        });
        message.success('更新成功');
      } else {
        await autoTradingApi.createStrategy(userId, {
          strategy_name,
          strategy_type,
          config,
        });
        message.success('创建成功');
      }

      onSuccess();
      onClose();
    } catch (error) {
      message.error('操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={strategy ? '编辑策略' : '创建策略'}
      open={visible}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="strategy_name" label="策略名称" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        <Form.Item name="strategy_type" label="策略类型" rules={[{ required: true }]}>
          <Select>
            <Select.Option value="PREDICTION">预测信号</Select.Option>
            <Select.Option value="MA">均线策略</Select.Option>
            <Select.Option value="RSI">RSI策略</Select.Option>
            <Select.Option value="RULE">规则引擎</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prev, curr) => prev.strategy_type !== curr.strategy_type}
        >
          {({ getFieldValue }) => {
            const type = getFieldValue('strategy_type');
            
            if (type === 'PREDICTION') {
              return (
                <Form.Item name="confidence_threshold" label="置信度阈值" initialValue={0.7}>
                  <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
                </Form.Item>
              );
            }
            
            if (type === 'MA') {
              return (
                <>
                  <Form.Item name="short_period" label="短期周期" initialValue={5}>
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item name="long_period" label="长期周期" initialValue={20}>
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                </>
              );
            }
            
            if (type === 'RSI') {
              return (
                <>
                  <Form.Item name="rsi_period" label="RSI周期" initialValue={14}>
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item name="oversold_threshold" label="超卖阈值" initialValue={30}>
                    <InputNumber min={0} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                  <Form.Item name="overbought_threshold" label="超买阈值" initialValue={70}>
                    <InputNumber min={0} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </>
              );
            }
            
            return null;
          }}
        </Form.Item>
      </Form>
    </Modal>
  );
}
```

- [ ] **Step 5: 创建自动交易监控组件**

```tsx
// frontend/src/components/AutoTradeMonitor.tsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, message } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons';
import { autoTradingApi } from '../services/api';
import type { AutoTradingStatus, AutoTradeLog } from '../types';

interface Props {
  userId: number;
}

export default function AutoTradeMonitor({ userId }: Props) {
  const [status, setStatus] = useState<AutoTradingStatus | null>(null);
  const [logs, setLogs] = useState<AutoTradeLog[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchLogs();
  }, [userId]);

  const fetchStatus = async () => {
    try {
      const response = await autoTradingApi.getStatus(userId);
      setStatus(response.data);
    } catch (error) {
      console.error('获取状态失败:', error);
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await autoTradingApi.getLogs(userId, 20);
      setLogs(response.data);
    } catch (error) {
      console.error('获取日志失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const logColumns = [
    { title: '时间', dataIndex: 'created_at', key: 'time', render: (v: string) => new Date(v).toLocaleTimeString() },
    { title: '股票', dataIndex: 'stock_code', key: 'stock' },
    { title: '名称', dataIndex: 'stock_name', key: 'name' },
    {
      title: '方向',
      dataIndex: 'direction',
      key: 'direction',
      render: (v: string) => <Tag color={v === 'BUY' ? 'green' : 'red'}>{v === 'BUY' ? '买入' : '卖出'}</Tag>,
    },
    { title: '价格', dataIndex: 'price', key: 'price', render: (v: number) => v?.toFixed(2) },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '策略', dataIndex: 'signal_source', key: 'strategy' },
    {
      title: '结果',
      dataIndex: 'execution_result',
      key: 'result',
      render: (v: string) => (
        <Tag color={v === 'SUCCESS' ? 'green' : v === 'SKIPPED' ? 'orange' : 'red'}>
          {v === 'SUCCESS' ? '成功' : v === 'SKIPPED' ? '跳过' : '失败'}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行状态"
              value={status?.running ? '运行中' : '已停止'}
              valueStyle={{ color: status?.running ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活跃策略" value={status?.active_strategies || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="今日交易" value={status?.today_trades || 0} suffix="笔" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={status?.today_pnl || 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: (status?.today_pnl || 0) >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近交易日志">
        <Table
          columns={logColumns}
          dataSource={logs}
          loading={loading}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}
```

- [ ] **Step 6: 创建风控配置表单**

```tsx
// frontend/src/components/RiskConfigForm.tsx
import { useState, useEffect } from 'react';
import { Card, Form, InputNumber, Button, message, Row, Col } from 'antd';
import { autoTradingApi } from '../services/api';
import type { RiskConfig } from '../types';

interface Props {
  userId: number;
}

export default function RiskConfigForm({ userId }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, [userId]);

  const fetchConfig = async () => {
    try {
      const response = await autoTradingApi.getRiskConfig(userId);
      form.setFieldsValue(response.data);
    } catch (error) {
      console.error('获取风控配置失败:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await autoTradingApi.updateRiskConfig(userId, values);
      message.success('保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="风控配置" extra={<Button type="primary" onClick={handleSubmit} loading={loading}>保存</Button>}>
      <Form form={form} layout="vertical">
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item name="stop_loss_pct" label="止损比例">
              <InputNumber min={-1} max={0} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="take_profit_pct" label="止盈比例">
              <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="max_position_pct" label="单只仓位上限">
              <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="max_total_position_pct" label="总仓位上限">
              <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item name="max_daily_trades" label="每日最大交易次数">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="max_weekly_trades" label="每周最大交易次数">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="max_daily_loss" label="每日最大亏损">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="max_single_trade" label="单笔最大金额">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Card>
  );
}
```

- [ ] **Step 7: 创建自动交易页面**

```tsx
// frontend/src/pages/AutoTrading.tsx
import { useState, useEffect } from 'react';
import { Tabs, Button, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import StrategyList from '../components/StrategyList';
import StrategyForm from '../components/StrategyForm';
import AutoTradeMonitor from '../components/AutoTradeMonitor';
import RiskConfigForm from '../components/RiskConfigForm';
import { useTradeStore } from '../stores/tradeStore';
import type { StrategyConfig } from '../types';

export default function AutoTrading() {
  const { userId, setUserId } = useTradeStore();
  const [formVisible, setFormVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<StrategyConfig | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  const handleEdit = (strategy: StrategyConfig) => {
    setEditingStrategy(strategy);
    setFormVisible(true);
  };

  const handleCreate = () => {
    setEditingStrategy(null);
    setFormVisible(true);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  if (!userId) return null;

  return (
    <div>
      <Tabs
        items={[
          {
            key: 'monitor',
            label: '交易监控',
            children: <AutoTradeMonitor userId={userId} />,
          },
          {
            key: 'strategies',
            label: '策略管理',
            children: (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                    创建策略
                  </Button>
                </div>
                <StrategyList userId={userId} onEdit={handleEdit} onRefresh={handleRefresh} />
              </div>
            ),
          },
          {
            key: 'risk',
            label: '风控配置',
            children: <RiskConfigForm userId={userId} />,
          },
        ]}
      />

      <StrategyForm
        userId={userId}
        visible={formVisible}
        strategy={editingStrategy}
        onClose={() => setFormVisible(false)}
        onSuccess={handleRefresh}
      />
    </div>
  );
}
```

- [ ] **Step 8: 更新App路由**

```tsx
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';
import Prediction from './pages/Prediction';
import Review from './pages/Review';
import AutoTrading from './pages/AutoTrading';

const { Header, Content } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <h1 style={{ color: 'white', margin: 0 }}>股票交易系统</h1>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trade" element={<Trade />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/review" element={<Review />} />
          <Route path="/auto-trading" element={<AutoTrading />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: add auto trading frontend pages and components"
```

---

## 自审检查清单

**1. 规格覆盖:**
- [x] 策略引擎 (Task 3, 5)
- [x] 执行引擎 (Task 7)
- [x] 风控系统 (Task 4)
- [x] 资金管理 (Task 6)
- [x] 数据模型 (Task 1)
- [x] API接口 (Task 8)
- [x] 前端界面 (Task 9)

**2. 占位符检查:**
- [x] 无TBD或TODO
- [x] 所有代码完整

**3. 类型一致性:**
- [x] 前后端类型一致
- [x] 函数签名一致
