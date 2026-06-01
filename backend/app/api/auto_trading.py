from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auto_trading import (
    StrategyConfigCreate, StrategyConfigUpdate, StrategyConfigResponse,
    AutoTradeTaskCreate, AutoTradeTaskResponse,
    RiskConfigCreate, RiskConfigResponse,
    AutoTradeLogResponse, AutoTradingStatus, AutoTradingStatistics
)
from app.models.strategy_config import StrategyConfig
from app.models.auto_trade_task import AutoTradeTask
from app.models.auto_trade_log import AutoTradeLog
from app.services.strategy_engine import StrategyEngine
from app.services.execution_engine import ExecutionEngine
from app.services.risk_control import RiskControl
from app.services.fund_manager import FundMode

router = APIRouter(prefix="/api/auto-trading", tags=["自动交易"])


@router.post("/strategies", response_model=StrategyConfigResponse)
def create_strategy(strategy_in: StrategyConfigCreate, user_id: int, db: Session = Depends(get_db)):
    engine = StrategyEngine(db)
    return engine.create_strategy_config(
        user_id=user_id,
        strategy_name=strategy_in.strategy_name,
        strategy_type=strategy_in.strategy_type,
        config=strategy_in.config
    )


@router.get("/strategies", response_model=List[StrategyConfigResponse])
def get_strategies(user_id: int, db: Session = Depends(get_db)):
    engine = StrategyEngine(db)
    return engine.get_strategy_configs(user_id)


@router.put("/strategies/{strategy_id}", response_model=StrategyConfigResponse)
def update_strategy(strategy_id: int, strategy_in: StrategyConfigUpdate, user_id: int, db: Session = Depends(get_db)):
    engine = StrategyEngine(db)
    updates = strategy_in.dict(exclude_unset=True)
    result = engine.update_strategy_config(strategy_id, user_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return result


@router.delete("/strategies/{strategy_id}")
def delete_strategy(strategy_id: int, user_id: int, db: Session = Depends(get_db)):
    engine = StrategyEngine(db)
    result = engine.delete_strategy_config(strategy_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"message": "删除成功"}


@router.post("/tasks", response_model=AutoTradeTaskResponse)
def create_task(task_in: AutoTradeTaskCreate, user_id: int, db: Session = Depends(get_db)):
    task = AutoTradeTask(
        user_id=user_id,
        execution_mode=task_in.execution_mode,
        interval_minutes=task_in.interval_minutes,
        watchlist=task_in.watchlist,
        enabled=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=List[AutoTradeTaskResponse])
def get_tasks(user_id: int, db: Session = Depends(get_db)):
    return db.query(AutoTradeTask).filter(AutoTradeTask.user_id == user_id).all()


@router.post("/tasks/{task_id}/start")
def start_task(task_id: int, user_id: int, db: Session = Depends(get_db)):
    engine = ExecutionEngine(db, user_id, FundMode.SIMULATED)
    try:
        engine.start(task_id)
        return {"message": "任务启动成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/stop")
def stop_task(task_id: int, user_id: int, db: Session = Depends(get_db)):
    task = db.query(AutoTradeTask).filter(
        AutoTradeTask.id == task_id,
        AutoTradeTask.user_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.enabled = False
    db.commit()
    return {"message": "任务已停止"}


@router.get("/risk-config", response_model=RiskConfigResponse)
def get_risk_config(user_id: int, db: Session = Depends(get_db)):
    control = RiskControl(db)
    return control.get_or_create_config(user_id)


@router.put("/risk-config", response_model=RiskConfigResponse)
def update_risk_config(config_in: RiskConfigCreate, user_id: int, db: Session = Depends(get_db)):
    control = RiskControl(db)
    config = control.get_or_create_config(user_id)
    for key, value in config_in.dict().items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


@router.get("/status", response_model=AutoTradingStatus)
def get_status(user_id: int, db: Session = Depends(get_db)):
    engine = ExecutionEngine(db, user_id, FundMode.SIMULATED)
    return engine.get_status()


@router.get("/statistics", response_model=AutoTradingStatistics)
def get_statistics(user_id: int, db: Session = Depends(get_db)):
    engine = ExecutionEngine(db, user_id, FundMode.SIMULATED)
    return engine.get_statistics()


@router.get("/logs", response_model=List[AutoTradeLogResponse])
def get_logs(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(AutoTradeLog).filter(
        AutoTradeLog.user_id == user_id
    ).order_by(AutoTradeLog.created_at.desc()).limit(limit).all()
