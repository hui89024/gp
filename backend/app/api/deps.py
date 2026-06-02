from typing import Generator
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.trading_engine import TradingEngine
from app.services.account_service import AccountService
from app.services.data_service import DataService
from app.services.broker_service import BrokerService
from app.services.fundamental_service import FundamentalService
from app.services.live_risk_control import LiveTradingRiskControl


def get_trading_engine(db: Session = Depends(get_db)) -> TradingEngine:
    return TradingEngine(db)


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


def get_data_service() -> DataService:
    return DataService()


def get_broker_service(db: Session = Depends(get_db)) -> BrokerService:
    return BrokerService(db)


def get_fundamental_service(db: Session = Depends(get_db)) -> FundamentalService:
    return FundamentalService(db)


def get_live_risk_control(db: Session = Depends(get_db)) -> LiveTradingRiskControl:
    return LiveTradingRiskControl(db)


def get_current_user_token(request: Request) -> str:
    """从请求头中提取 Bearer token"""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证令牌"
        )
    return authorization.replace("Bearer ", "")


def get_current_user(
    token: str = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    """解码 token 并返回当前用户"""
    from app.utils.auth import decode_token
    from app.models.user import User

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    user_id = payload.get("sub")
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌数据"
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    return user