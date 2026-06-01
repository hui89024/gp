from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class AutoTradeLog(Base):
    __tablename__ = "auto_trade_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("auto_trade_tasks.id"))
    signal_source = Column(String(50))
    stock_code = Column(String(10))
    stock_name = Column(String(50))
    direction = Column(String(4))
    price = Column(Float)
    quantity = Column(Integer)
    confidence = Column(Float)
    risk_check_passed = Column(Boolean)
    risk_check_reason = Column(String(200))
    execution_result = Column(String(20))
    error_message = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
