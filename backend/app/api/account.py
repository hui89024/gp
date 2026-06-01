from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, AccountOverview
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/account", tags=["账户"])


@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """创建用户"""
    service = AccountService(db)

    # 检查用户名是否已存在
    existing = service.get_user_by_username(user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    return service.create_user(user_in.username, user_in.initial_capital)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户信息"""
    service = AccountService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/users/{user_id}/overview", response_model=AccountOverview)
def get_account_overview(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取账户概览"""
    service = AccountService(db)
    try:
        return service.get_account_overview(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))