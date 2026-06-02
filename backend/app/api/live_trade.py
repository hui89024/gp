from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.live_trade import LiveTrade
from app.schemas.live_trade import (
    LiveTradeRequest, LiveTradeResponse, BrokerPosition, BrokerBalance
)
from app.services.broker_service import BrokerService
from app.services.live_risk_control import LiveTradingRiskControl

router = APIRouter(prefix="/api/live-trades", tags=["实盘交易"])


@router.post("/buy", response_model=LiveTradeResponse)
def live_buy(
    data: LiveTradeRequest,
    db: Session = Depends(get_db)
):
    """实盘买入"""
    risk_control = LiveTradingRiskControl(db)
    amount = data.price * data.quantity
    ok, msg = risk_control.validate_trade(user_id=1, amount=amount, stock_code=data.stock_code, trade_type="BUY")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    service = BrokerService(db)
    try:
        result = service.buy(data.stock_code, data.price, data.quantity)
        trade = LiveTrade(
            user_id=1,
            broker_account_id=service._account_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            trade_type="BUY",
            price=data.price,
            quantity=data.quantity,
            total_amount=amount,
            commission=0,
            broker_order_id=result.get("entrust_no", ""),
            status="filled",
            strategy_tag=data.strategy_tag
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"买入失败: {str(e)}")


@router.post("/sell", response_model=LiveTradeResponse)
def live_sell(
    data: LiveTradeRequest,
    db: Session = Depends(get_db)
):
    """实盘卖出"""
    risk_control = LiveTradingRiskControl(db)
    amount = data.price * data.quantity
    ok, msg = risk_control.validate_trade(user_id=1, amount=amount, stock_code=data.stock_code, trade_type="SELL")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    service = BrokerService(db)
    try:
        result = service.sell(data.stock_code, data.price, data.quantity)
        trade = LiveTrade(
            user_id=1,
            broker_account_id=service._account_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            trade_type="SELL",
            price=data.price,
            quantity=data.quantity,
            total_amount=amount,
            commission=0,
            broker_order_id=result.get("entrust_no", ""),
            status="filled",
            strategy_tag=data.strategy_tag
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"卖出失败: {str(e)}")


@router.get("/positions")
def get_live_positions(db: Session = Depends(get_db)):
    """查询实盘持仓"""
    service = BrokerService(db)
    try:
        return service.get_positions()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"查询持仓失败: {str(e)}")


@router.get("/balance")
def get_live_balance(db: Session = Depends(get_db)):
    """查询资金"""
    service = BrokerService(db)
    try:
        return service.get_balance()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"查询资金失败: {str(e)}")


@router.get("/history", response_model=List[LiveTradeResponse])
def get_live_trades(
    stock_code: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """实盘交易历史"""
    query = db.query(LiveTrade).filter(LiveTrade.user_id == 1)
    if stock_code:
        query = query.filter(LiveTrade.stock_code == stock_code)
    return query.order_by(LiveTrade.trade_time.desc()).limit(limit).all()


@router.post("/cancel/{order_id}")
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """撤单"""
    service = BrokerService(db)
    try:
        result = service.cancel_order(order_id)
        return {"message": "撤单成功" if result else "撤单失败"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"撤单失败: {str(e)}")
