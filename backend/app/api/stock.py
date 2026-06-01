from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas.stock import StockQuote, StockHistory, StockSearchResult, KLineData
from app.services.data_service import DataService

router = APIRouter(prefix="/api/stocks", tags=["股票数据"])


@router.get("/{stock_code}/quote", response_model=StockQuote)
def get_stock_quote(
    stock_code: str,
    data_service: DataService = Depends()
):
    """获取实时行情"""
    quote = data_service.get_stock_quote(stock_code)
    if not quote:
        raise HTTPException(status_code=404, detail="股票不存在")
    return quote


@router.get("/{stock_code}/history", response_model=List[StockHistory])
def get_stock_history(
    stock_code: str,
    days: int = 30,
    data_service: DataService = Depends()
):
    """获取历史数据"""
    return data_service.get_stock_history(stock_code, days)


@router.get("/{stock_code}/kline", response_model=KLineData)
def get_kline_data(
    stock_code: str,
    days: int = 60,
    data_service: DataService = Depends()
):
    """获取K线数据"""
    return data_service.get_kline_data(stock_code, days)


@router.get("/search", response_model=List[StockSearchResult])
def search_stocks(
    keyword: str,
    data_service: DataService = Depends()
):
    """搜索股票"""
    return data_service.search_stocks(keyword)