from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LiveTradeRequest(BaseModel):
    stock_code: str
    stock_name: str
    price: float
    quantity: int
    strategy_tag: Optional[str] = None


class LiveTradeResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: Optional[str]
    trade_type: str
    price: float
    quantity: int
    total_amount: float
    commission: float
    broker_order_id: Optional[str]
    status: str
    strategy_tag: Optional[str]
    trade_time: datetime

    class Config:
        from_attributes = True


class BrokerPosition(BaseModel):
    stock_code: str
    stock_name: str
    quantity: int
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_ratio: float


class BrokerBalance(BaseModel):
    total_assets: float
    available_cash: float
    market_value: float
    frozen_amount: float
