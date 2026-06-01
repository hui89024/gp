from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    initial_capital: Optional[float] = 1000000.0


class UserResponse(UserBase):
    id: int
    initial_capital: float
    current_capital: float
    created_at: datetime

    class Config:
        from_attributes = True


class AccountOverview(BaseModel):
    total_assets: float
    available_capital: float
    market_value: float
    total_pnl: float
    today_pnl: float
