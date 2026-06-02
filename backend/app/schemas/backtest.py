from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class BacktestRequest(BaseModel):
    """回测请求"""
    strategy_name: str = Field(..., min_length=1, max_length=50)
    strategy_type: str = Field("MA", description="策略类型: MA/RSI/MACD")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    start_date: str = Field(..., description="回测开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="回测结束日期 YYYY-MM-DD")
    initial_capital: float = Field(100000.0, gt=0)
    stock_codes: List[str] = Field(..., min_length=1, description="股票代码列表")
    commission_rate: float = Field(0.0003, ge=0)
    stamp_tax_rate: float = Field(0.001, ge=0)
    slippage: float = Field(0.001, ge=0)


class TradeRecordResponse(BaseModel):
    stock_code: str
    direction: str
    price: float
    quantity: int
    amount: float
    commission: float
    tax: float
    trade_date: str
    reason: str = ""


class EquityPoint(BaseModel):
    date: str
    equity: float


class BacktestResponse(BaseModel):
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]


class BacktestRecordResponse(BaseModel):
    id: int
    user_id: int
    strategy_name: Optional[str] = None
    strategy_config: Optional[Dict[str, Any]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    initial_capital: Optional[float] = None
    stock_codes: Optional[List[str]] = None
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    total_trades: Optional[int] = None
    trades: Optional[List[Dict[str, Any]]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
