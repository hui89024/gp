from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.trading_engine import TradingEngine
from app.services.account_service import AccountService
from app.services.data_service import DataService


def get_trading_engine(db: Session = Depends(get_db)) -> TradingEngine:
    return TradingEngine(db)


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


def get_data_service() -> DataService:
    return DataService()