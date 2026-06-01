from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.trade import TradeCreate, TradeResponse, PositionResponse
from app.services.trading_engine import TradingEngine

router = APIRouter(prefix="/api/trades", tags=["交易"])


@router.post("/buy", response_model=TradeResponse)
def buy_stock(
    trade_in: TradeCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """买入股票"""
    engine = TradingEngine(db)
    result = engine.buy(
        user_id=user_id,
        stock_code=trade_in.stock_code,
        stock_name=trade_in.stock_name,
        price=trade_in.price,
        quantity=trade_in.quantity,
        strategy_tag=trade_in.strategy_tag
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.trade


@router.post("/sell", response_model=TradeResponse)
def sell_stock(
    trade_in: TradeCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """卖出股票"""
    engine = TradingEngine(db)
    result = engine.sell(
        user_id=user_id,
        stock_code=trade_in.stock_code,
        stock_name=trade_in.stock_name,
        price=trade_in.price,
        quantity=trade_in.quantity,
        strategy_tag=trade_in.strategy_tag
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.trade


@router.get("/history", response_model=List[TradeResponse])
def get_trade_history(
    user_id: int,
    stock_code: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取交易历史"""
    engine = TradingEngine(db)
    return engine.get_trades(user_id, stock_code, limit)


@router.get("/positions", response_model=List[PositionResponse])
def get_positions(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取持仓"""
    engine = TradingEngine(db)
    return engine.get_positions(user_id)