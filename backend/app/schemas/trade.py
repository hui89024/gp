from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TradeCreate(BaseModel):
    stock_code: str = Field(..., min_length=6, max_length=6)
    stock_name: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    strategy_tag: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: Optional[str]
    trade_type: str
    price: float
    quantity: int
    commission: float
    total_amount: float
    strategy_tag: Optional[str]
    trade_time: datetime

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_cost: float
    current_price: Optional[float]
    unrealized_pnl: Optional[float]
    market_value: Optional[float]

    class Config:
        from_attributes = True
