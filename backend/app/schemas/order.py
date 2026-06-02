from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    OCO = "OCO"
    CONDITIONAL = "CONDITIONAL"


class OrderDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    DAY = "DAY"


class OrderCreate(BaseModel):
    market: str
    stock_code: str
    stock_name: Optional[str] = None
    order_type: OrderType
    direction: OrderDirection
    price: Optional[float] = None
    quantity: int
    time_in_force: Optional[TimeInForce] = TimeInForce.GTC
    stop_price: Optional[float] = None
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None
    strategy_tag: Optional[str] = None


class OrderUpdate(BaseModel):
    price: Optional[float] = None
    quantity: Optional[int] = None
    stop_price: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    market: str
    stock_code: str
    stock_name: Optional[str]
    order_type: str
    direction: str
    price: Optional[float]
    quantity: int
    filled_quantity: int
    avg_fill_price: Optional[float]
    status: str
    time_in_force: str
    stop_price: Optional[float]
    strategy_tag: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    filled_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderList(BaseModel):
    orders: list[OrderResponse]
    total: int
