from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class CircuitBreakerEvent(Base):
    __tablename__ = "circuit_breaker_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trigger_reason = Column(String(200))
    trigger_value = Column(Float)
    threshold = Column(Float)
    action_taken = Column(String(50))
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())