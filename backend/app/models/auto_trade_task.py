from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.sql import func
from app.database import Base


class AutoTradeTask(Base):
    __tablename__ = "auto_trade_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    execution_mode = Column(String(20), nullable=False)  # POLLING/REALTIME/BATCH
    interval_minutes = Column(Integer)
    watchlist = Column(ARRAY(String))
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
