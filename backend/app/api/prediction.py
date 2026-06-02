from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.prediction import PredictionResponse, PredictionSignal, ModelPerformance
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predictions", tags=["预测"])


@router.post("/train/{stock_code}")
def train_model(
    stock_code: str,
    days: int = 180,
    db: Session = Depends(get_db)
):
    """训练预测模型"""
    service = PredictionService(db)
    result = service.train_model(stock_code, days)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/signal/{stock_code}", response_model=PredictionSignal)
def get_prediction_signal(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取预测信号"""
    service = PredictionService(db)

    # 前置检查：实时行情
    quote = service.data_service.get_stock_quote(stock_code)
    if not quote:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取{stock_code}的实时行情，请检查股票代码是否正确或数据源是否可用"
        )

    signal = service.predict(stock_code)

    if not signal:
        raise HTTPException(
            status_code=404,
            detail=f"无法生成{stock_code}的预测信号，历史数据可能不足，请先训练模型"
        )

    return signal


@router.get("/signals", response_model=List[PredictionSignal])
def get_multiple_signals(
    stock_codes: str,
    db: Session = Depends(get_db)
):
    """批量获取预测信号"""
    service = PredictionService(db)
    codes = [code.strip() for code in stock_codes.split(",")]

    signals = []
    for code in codes[:10]:
        signal = service.predict(code)
        if signal:
            signals.append(signal)

    return signals


@router.get("/performance", response_model=ModelPerformance)
def get_model_performance(
    model_type: str = "LSTM",
    db: Session = Depends(get_db)
):
    """获取模型性能"""
    service = PredictionService(db)
    return service.get_model_performance(model_type)


@router.get("/history", response_model=List[PredictionResponse])
def get_prediction_history(
    stock_code: str,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """获取预测历史"""
    from app.models.prediction import Prediction
    predictions = db.query(Prediction).filter(
        Prediction.stock_code == stock_code
    ).order_by(
        Prediction.created_at.desc()
    ).limit(limit).all()

    return predictions
