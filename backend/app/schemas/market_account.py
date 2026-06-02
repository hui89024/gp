from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MarketAccountCreate(BaseModel):
    market: str  # CN/HK/US
    currency: str  # CNY/HKD/USD
    initial_capital: float
    exchange_rate: Optional[float] = 1.0


class MarketAccountUpdate(BaseModel):
    current_capital: Optional[float] = None
    exchange_rate: Optional[float] = None


class MarketAccountResponse(BaseModel):
    id: int
    user_id: int
    market: str
    currency: str
    initial_capital: float
    current_capital: float
    exchange_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class MarketAccountList(BaseModel):
    accounts: list[MarketAccountResponse]
    total_assets_cny: float  # 总资产（人民币）
