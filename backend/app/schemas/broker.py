from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BrokerAccountCreate(BaseModel):
    broker_type: str = "eastmoney"
    account: str
    password: str


class BrokerAccountUpdate(BaseModel):
    broker_type: Optional[str] = None
    account: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class BrokerAccountResponse(BaseModel):
    id: int
    user_id: int
    broker_type: str
    account: str
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BrokerLoginRequest(BaseModel):
    account: str
    password: str
