from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from app.database import Base


class LiveTrade(Base):
    """实盘交易记录模型"""
    __tablename__ = "live_trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    broker_account_id = Column(Integer, ForeignKey("broker_accounts.id"), nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50))
    trade_type = Column(String(10), nullable=False)  # BUY / SELL
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    commission = Column(Numeric(10, 2), default=0)
    broker_order_id = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")  # pending / filled / cancelled / failed
    strategy_tag = Column(String(50), nullable=True)
    trade_time = Column(DateTime, default=datetime.utcnow)
