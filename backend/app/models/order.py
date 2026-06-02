from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market = Column(String(10), nullable=False)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    order_type = Column(String(20), nullable=False)
    direction = Column(String(4), nullable=False)
    price = Column(Float)
    quantity = Column(Integer, nullable=False)
    filled_quantity = Column(Integer, default=0)
    avg_fill_price = Column(Float)
    status = Column(String(20), default="PENDING")
    time_in_force = Column(String(10), default="GTC")
    stop_price = Column(Float)
    condition_type = Column(String(20))
    condition_value = Column(String(100))
    strategy_tag = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))
