from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.circuit_breaker import CircuitBreaker
from app.services.alert_service import AlertService

router = APIRouter(prefix="/api/risk-control", tags=["风控"])


@router.get("/circuit-breaker/status")
def get_circuit_breaker_status(user_id: int, db: Session = Depends(get_db)):
    """获取熔断状态"""
    cb = CircuitBreaker(db)
    return cb.get_status(user_id)


@router.post("/circuit-breaker/check")
def check_circuit_breaker(user_id: int, db: Session = Depends(get_db)):
    """检查熔断"""
    cb = CircuitBreaker(db)
    triggered, reason = cb.check(user_id)
    return {"triggered": triggered, "reason": reason}


@router.post("/circuit-breaker/reset")
def reset_circuit_breaker(user_id: int, db: Session = Depends(get_db)):
    """重置熔断器"""
    cb = CircuitBreaker(db)
    cb.reset()
    return {"message": "熔断器已重置"}


@router.get("/circuit-breaker/events")
def get_circuit_breaker_events(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """获取熔断事件"""
    cb = CircuitBreaker(db)
    return cb.get_events(user_id, limit)


@router.get("/alerts/records")
def get_alert_records(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """获取告警记录"""
    service = AlertService(db)
    return service.get_records(user_id, limit)


@router.post("/alerts/test")
def test_alert(user_id: int, channel: str = "dingtalk", db: Session = Depends(get_db)):
    """测试告警"""
    service = AlertService(db)
    success = service.test_alert(user_id, channel)
    if not success:
        raise HTTPException(status_code=400, detail="测试失败")
    return {"message": "测试成功"}
