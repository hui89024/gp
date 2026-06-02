from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.market_account import MarketAccount
from app.schemas.market_account import (
    MarketAccountCreate, MarketAccountUpdate, MarketAccountResponse, MarketAccountList
)

router = APIRouter(prefix="/api/v1/accounts", tags=["市场账户"])


@router.post("", response_model=MarketAccountResponse)
async def create_market_account(
    account_data: MarketAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id,
        MarketAccount.market == account_data.market
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{account_data.market}市场账户已存在"
        )
    account = MarketAccount(
        user_id=current_user.id,
        market=account_data.market,
        currency=account_data.currency,
        initial_capital=account_data.initial_capital,
        current_capital=account_data.initial_capital,
        exchange_rate=account_data.exchange_rate
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=MarketAccountList)
async def get_market_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id
    ).all()
    total_assets_cny = sum(
        account.current_capital * account.exchange_rate for account in accounts
    )
    return MarketAccountList(
        accounts=accounts,
        total_assets_cny=round(total_assets_cny, 2)
    )


@router.get("/{market}", response_model=MarketAccountResponse)
async def get_market_account(
    market: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id,
        MarketAccount.market == market
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{market}市场账户不存在"
        )
    return account


@router.put("/{market}", response_model=MarketAccountResponse)
async def update_market_account(
    market: str,
    update_data: MarketAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id,
        MarketAccount.market == market
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{market}市场账户不存在"
        )
    if update_data.current_capital is not None:
        account.current_capital = update_data.current_capital
    if update_data.exchange_rate is not None:
        account.exchange_rate = update_data.exchange_rate
    db.commit()
    db.refresh(account)
    return account
