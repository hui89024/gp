from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PredictionCreate(BaseModel):
    stock_code: str
    model_type: str = "LSTM"


class PredictionResponse(BaseModel):
    id: int
    stock_code: str
    model_type: str
    predicted_direction: Optional[str]
    predicted_price: Optional[float]
    confidence: Optional[float]
    actual_result: Optional[str]
    actual_price: Optional[float]
    prediction_date: datetime
    target_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionSignal(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    predicted_direction: str
    predicted_price: float
    confidence: float
    signal_strength: str
    model_type: str
    prediction_date: datetime


class ModelPerformance(BaseModel):
    model_type: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    avg_confidence: float