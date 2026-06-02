from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.broker_account import BrokerAccount
from app.schemas.broker import (
    BrokerAccountCreate, BrokerAccountUpdate, BrokerAccountResponse
)
from app.services.encryption import encryption_service
from app.services.broker_service import BrokerService

router = APIRouter(prefix="/api/broker", tags=["券商账户"])


@router.post("/accounts", response_model=BrokerAccountResponse)
def create_broker_account(
    data: BrokerAccountCreate,
    db: Session = Depends(get_db)
):
    """添加券商账户"""
    encrypted_pwd = encryption_service.encrypt(data.password)
    account = BrokerAccount(
        user_id=1,  # TODO: 从认证上下文获取
        broker_type=data.broker_type,
        account=data.account,
        password_encrypted=encrypted_pwd
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts", response_model=List[BrokerAccountResponse])
def list_broker_accounts(db: Session = Depends(get_db)):
    """获取券商账户列表"""
    return db.query(BrokerAccount).filter(BrokerAccount.is_active == True).all()


@router.put("/accounts/{account_id}", response_model=BrokerAccountResponse)
def update_broker_account(
    account_id: int,
    data: BrokerAccountUpdate,
    db: Session = Depends(get_db)
):
    """更新券商账户"""
    account = db.query(BrokerAccount).filter(BrokerAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="券商账户不存在")
    if data.broker_type is not None:
        account.broker_type = data.broker_type
    if data.account is not None:
        account.account = data.account
    if data.password is not None:
        account.password_encrypted = encryption_service.encrypt(data.password)
    if data.is_active is not None:
        account.is_active = data.is_active
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}")
def delete_broker_account(account_id: int, db: Session = Depends(get_db)):
    """删除券商账户（软删除）"""
    account = db.query(BrokerAccount).filter(BrokerAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="券商账户不存在")
    account.is_active = False
    db.commit()
    return {"message": "已禁用"}


@router.post("/accounts/{account_id}/login")
def login_broker(account_id: int, db: Session = Depends(get_db)):
    """登录券商账户"""
    service = BrokerService(db)
    try:
        service.login(account_id)
        return {"message": "登录成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"登录失败: {str(e)}")
