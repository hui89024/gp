from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StockQuote(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    amount: float
    change_percent: float
    change_amount: float
    timestamp: datetime


class StockHistory(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float


class StockSearchResult(BaseModel):
    stock_code: str
    stock_name: str
    market: str


class KLineData(BaseModel):
    dates: List[str]
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[int]
