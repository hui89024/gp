from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.backtest import (
    BacktestRequest, BacktestResponse, BacktestRecordResponse
)
from app.models.backtest_record import BacktestRecord
from app.services.backtest_engine import BacktestEngine, BacktestConfig

router = APIRouter(prefix="/api/backtest", tags=["回测"])


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest, user_id: int, db: Session = Depends(get_db)):
    """执行回测"""
    config = BacktestConfig(
        strategy_name=req.strategy_name,
        strategy_type=req.strategy_type,
        strategy_params=req.strategy_params,
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        stock_codes=req.stock_codes,
        commission_rate=req.commission_rate,
        stamp_tax_rate=req.stamp_tax_rate,
        slippage=req.slippage,
    )

    engine = BacktestEngine(config)
    result = engine.run()

    if result.total_trades == 0:
        raise HTTPException(status_code=400, detail="回测期间无交易产生，请检查策略参数和日期范围")

    # 保存回测记录
    record = BacktestRecord(
        user_id=user_id,
        strategy_name=req.strategy_name,
        strategy_config={
            "strategy_type": req.strategy_type,
            "strategy_params": req.strategy_params,
            "commission_rate": req.commission_rate,
            "stamp_tax_rate": req.stamp_tax_rate,
            "slippage": req.slippage,
        },
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        stock_codes=req.stock_codes,
        total_return=result.total_return,
        annual_return=result.annual_return,
        max_drawdown=result.max_drawdown,
        sharpe_ratio=result.sharpe_ratio,
        win_rate=result.win_rate,
        profit_loss_ratio=result.profit_loss_ratio,
        total_trades=result.total_trades,
        trades=result.trades,
        equity_curve=result.equity_curve,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return BacktestResponse(
        total_return=result.total_return,
        annual_return=result.annual_return,
        max_drawdown=result.max_drawdown,
        sharpe_ratio=result.sharpe_ratio,
        win_rate=result.win_rate,
        profit_loss_ratio=result.profit_loss_ratio,
        total_trades=result.total_trades,
        trades=result.trades,
        equity_curve=result.equity_curve,
    )


@router.get("/records", response_model=List[BacktestRecordResponse])
def get_records(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """获取回测历史记录"""
    records = (
        db.query(BacktestRecord)
        .filter(BacktestRecord.user_id == user_id)
        .order_by(BacktestRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/records/{record_id}", response_model=BacktestRecordResponse)
def get_record(record_id: int, user_id: int, db: Session = Depends(get_db)):
    """获取单条回测记录详情"""
    record = (
        db.query(BacktestRecord)
        .filter(BacktestRecord.id == record_id, BacktestRecord.user_id == user_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="回测记录不存在")
    return record


@router.delete("/records/{record_id}")
def delete_record(record_id: int, user_id: int, db: Session = Depends(get_db)):
    """删除回测记录"""
    record = (
        db.query(BacktestRecord)
        .filter(BacktestRecord.id == record_id, BacktestRecord.user_id == user_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="回测记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}
