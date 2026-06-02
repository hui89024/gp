from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.fundamental_service import FundamentalService

router = APIRouter(prefix="/api/fundamental", tags=["基本面数据"])


@router.get("/{stock_code}/report")
def get_financial_report(stock_code: str, db: Session = Depends(get_db)):
    """获取财务报表"""
    service = FundamentalService(db)
    return service.get_financial_report(stock_code)


@router.get("/{stock_code}/indicators")
def get_financial_indicators(stock_code: str, db: Session = Depends(get_db)):
    """获取财务指标"""
    service = FundamentalService(db)
    return service.get_financial_indicators(stock_code)


@router.get("/{stock_code}/company")
def get_company_info(stock_code: str, db: Session = Depends(get_db)):
    """获取公司信息"""
    service = FundamentalService(db)
    return service.get_company_info(stock_code)
