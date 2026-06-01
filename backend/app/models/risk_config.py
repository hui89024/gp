from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class RiskConfig(Base):
    __tablename__ = "risk_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    stop_loss_pct = Column(Float, default=-0.05)
    take_profit_pct = Column(Float, default=0.10)
    max_position_pct = Column(Float, default=0.20)
    max_total_position_pct = Column(Float, default=0.80)
    max_daily_trades = Column(Integer, default=10)
    max_weekly_trades = Column(Integer, default=30)
    max_daily_loss = Column(Float, default=50000.0)
    max_single_trade = Column(Float, default=100000.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
