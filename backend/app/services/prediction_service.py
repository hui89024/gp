from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionSignal, ModelPerformance
from app.services.data_service import DataService


def _get_stock_predictor():
    """延迟导入 StockPredictor（依赖 torch）"""
    from app.ml.lstm_model import StockPredictor
    return StockPredictor


class PredictionService:
    """预测服务"""

    def __init__(self, db: Session):
        self.db = db
        self.data_service = DataService()
        self.predictors = {}

    def get_or_create_predictor(self, stock_code: str):
        """获取或创建预测器"""
        if stock_code not in self.predictors:
            StockPredictor = _get_stock_predictor()
            self.predictors[stock_code] = StockPredictor()
        return self.predictors[stock_code]

    def train_model(self, stock_code: str, days: int = 180) -> dict:
        """训练预测模型"""
        history = self.data_service.get_stock_history(stock_code, days)

        if len(history) < 40:
            return {"success": False, "message": f"历史数据不足: {len(history)}条，需要至少40条"}

        prices = [h.close for h in history]
        volumes = [h.volume for h in history]

        predictor = self.get_or_create_predictor(stock_code)
        result = predictor.train(prices, volumes)

        return result

    def predict(self, stock_code: str) -> Optional[PredictionSignal]:
        """生成预测信号"""
        quote = self.data_service.get_stock_quote(stock_code)
        if not quote:
            return None

        history = self.data_service.get_stock_history(stock_code, 60)
        if len(history) < 30:
            return None

        prices = [h.close for h in history]
        volumes = [h.volume for h in history]

        predictor = self.get_or_create_predictor(stock_code)

        if not predictor.is_trained:
            train_result = self.train_model(stock_code)
            if not train_result.get("success"):
                return None

        prediction = predictor.predict(prices, volumes)

        confidence = prediction["confidence"]
        if confidence > 0.7:
            signal_strength = "STRONG"
        elif confidence > 0.6:
            signal_strength = "MEDIUM"
        else:
            signal_strength = "WEAK"

        pred_record = Prediction(
            stock_code=stock_code,
            model_type="LSTM",
            predicted_direction=prediction["direction"],
            predicted_price=prediction["predicted_price"],
            confidence=confidence,
            prediction_date=datetime.now(),
            target_date=datetime.now() + timedelta(days=1)
        )
        self.db.add(pred_record)
        self.db.commit()

        return PredictionSignal(
            stock_code=stock_code,
            stock_name=quote.stock_name,
            current_price=quote.current_price,
            predicted_direction=prediction["direction"],
            predicted_price=prediction["predicted_price"],
            confidence=confidence,
            signal_strength=signal_strength,
            model_type="LSTM",
            prediction_date=datetime.now()
        )

    def get_model_performance(self, model_type: str = "LSTM") -> ModelPerformance:
        """获取模型性能统计"""
        predictions = self.db.query(Prediction).filter(
            Prediction.model_type == model_type,
            Prediction.actual_result.isnot(None)
        ).all()

        if not predictions:
            return ModelPerformance(
                model_type=model_type,
                total_predictions=0,
                correct_predictions=0,
                accuracy=0.0,
                avg_confidence=0.0
            )

        total = len(predictions)
        correct = sum(1 for p in predictions if p.predicted_direction == p.actual_result)
        avg_confidence = sum(p.confidence for p in predictions) / total

        return ModelPerformance(
            model_type=model_type,
            total_predictions=total,
            correct_predictions=correct,
            accuracy=correct / total if total > 0 else 0.0,
            avg_confidence=avg_confidence
        )
