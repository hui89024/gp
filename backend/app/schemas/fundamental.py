from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, datetime


class FinancialReport(BaseModel):
    stock_code: str
    balance_sheet: Optional[dict] = None
    income_statement: Optional[dict] = None
    cash_flow: Optional[dict] = None
    report_date: date


class FinancialIndicators(BaseModel):
    stock_code: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_ratio: Optional[float] = None


class CompanyInfo(BaseModel):
    stock_code: str
    company_name: str
    main_business: Optional[str] = None
    industry: Optional[str] = None
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None


class IndustryData(BaseModel):
    industry: str
    stock_count: int
    avg_pe: Optional[float] = None
    avg_pb: Optional[float] = None
    avg_roe: Optional[float] = None
