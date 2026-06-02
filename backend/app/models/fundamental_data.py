from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class FundamentalData(Base):
    """基本面数据模型"""
    __tablename__ = "fundamental_data"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False)
    data_type = Column(String(50), nullable=False)  # balance_sheet / income / cash_flow / indicators
    data = Column(JSONB, nullable=False)
    report_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "data_type", "report_date", name="uq_fundamental"),
    )
