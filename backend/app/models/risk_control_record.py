from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class RiskControlRecord(Base):
    """风控记录模型"""
    __tablename__ = "risk_control_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # trade_rejected / stop_loss / circuit_breaker
    event_detail = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
