from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    model_type = Column(String(20), nullable=False)  # LSTM/Transformer/Ensemble
    predicted_direction = Column(String(4))  # UP/DOWN
    predicted_price = Column(Float)
    confidence = Column(Float)
    actual_result = Column(String(4))  # UP/DOWN/NA
    actual_price = Column(Float)
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())