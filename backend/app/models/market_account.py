from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class MarketAccount(Base):
    """多市场账户模型"""
    __tablename__ = "market_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market = Column(String(10), nullable=False)  # CN/HK/US
    currency = Column(String(3), nullable=False)  # CNY/HKD/USD
    initial_capital = Column(Float, nullable=False)
    current_capital = Column(Float, nullable=False)
    exchange_rate = Column(Float, default=1.0)  # 汇率（相对人民币）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'market', name='uq_user_market'),
    )
