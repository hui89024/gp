from pydantic import BaseModel, Field
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


class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExecutionResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    PARTIAL = "PARTIAL"


# StrategyConfig Schemas
class StrategyConfigBase(BaseModel):
    strategy_name: str = Field(..., min_length=1, max_length=50)
    strategy_type: StrategyType
    config: Dict[str, Any]
    enabled: bool = True


class StrategyConfigCreate(StrategyConfigBase):
    pass


class StrategyConfigUpdate(BaseModel):
    strategy_name: Optional[str] = Field(None, min_length=1, max_length=50)
    strategy_type: Optional[StrategyType] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class StrategyConfigResponse(StrategyConfigBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AutoTradeTask Schemas
class AutoTradeTaskBase(BaseModel):
    execution_mode: ExecutionMode
    interval_minutes: Optional[int] = Field(None, ge=1)
    watchlist: List[str] = []
    enabled: bool = True


class AutoTradeTaskCreate(AutoTradeTaskBase):
    pass


class AutoTradeTaskUpdate(BaseModel):
    execution_mode: Optional[ExecutionMode] = None
    interval_minutes: Optional[int] = Field(None, ge=1)
    watchlist: Optional[List[str]] = None
    enabled: Optional[bool] = None


class AutoTradeTaskResponse(AutoTradeTaskBase):
    id: int
    user_id: int
    last_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# RiskConfig Schemas
class RiskConfigBase(BaseModel):
    stop_loss_pct: float = Field(-0.05, le=0)
    take_profit_pct: float = Field(0.10, ge=0)
    max_position_pct: float = Field(0.20, gt=0, le=1)
    max_total_position_pct: float = Field(0.80, gt=0, le=1)
    max_daily_trades: int = Field(10, gt=0)
    max_weekly_trades: int = Field(30, gt=0)
    max_daily_loss: float = Field(50000.0, gt=0)
    max_single_trade: float = Field(100000.0, gt=0)


class RiskConfigCreate(RiskConfigBase):
    pass


class RiskConfigUpdate(BaseModel):
    stop_loss_pct: Optional[float] = Field(None, le=0)
    take_profit_pct: Optional[float] = Field(None, ge=0)
    max_position_pct: Optional[float] = Field(None, gt=0, le=1)
    max_total_position_pct: Optional[float] = Field(None, gt=0, le=1)
    max_daily_trades: Optional[int] = Field(None, gt=0)
    max_weekly_trades: Optional[int] = Field(None, gt=0)
    max_daily_loss: Optional[float] = Field(None, gt=0)
    max_single_trade: Optional[float] = Field(None, gt=0)


class RiskConfigResponse(RiskConfigBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AutoTradeLog Schemas
class AutoTradeLogBase(BaseModel):
    signal_source: Optional[str] = None
    stock_code: str = Field(..., max_length=10)
    stock_name: Optional[str] = Field(None, max_length=50)
    direction: TradeDirection
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    risk_check_passed: bool = False
    risk_check_reason: Optional[str] = Field(None, max_length=200)
    execution_result: ExecutionResult
    error_message: Optional[str] = Field(None, max_length=500)


class AutoTradeLogCreate(AutoTradeLogBase):
    task_id: Optional[int] = None


class AutoTradeLogResponse(AutoTradeLogBase):
    id: int
    user_id: int
    task_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Signal Schema (用于策略信号)
class TradeSignal(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None
    direction: TradeDirection
    price: float
    quantity: int
    confidence: float = Field(0.0, ge=0, le=1)
    reason: str = ""
    strategy_name: str


# Risk Check Result
class RiskCheckResult(BaseModel):
    passed: bool
    reason: str = ""
    details: Dict[str, Any] = {}
