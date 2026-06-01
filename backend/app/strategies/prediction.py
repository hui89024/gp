from typing import List, Dict, Any
from datetime import datetime
from app.strategies.base import BaseStrategy, Signal
from app.services.data_service import DataService


class PredictionStrategy(BaseStrategy):
    """预测信号策略"""

    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.db = db_session
        self.data_service = DataService()
        self.prediction_service = None
        if db_session:
            from app.services.prediction_service import PredictionService
            self.prediction_service = PredictionService(db_session)

    @property
    def name(self) -> str:
        return "PredictionStrategy"

    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        signals = []
        confidence_threshold = self.config.get("confidence_threshold", 0.7)

        for stock_code in stock_codes:
            try:
                quote = self.data_service.get_stock_quote(stock_code)
                if not quote:
                    continue

                if self.prediction_service:
                    prediction = self.prediction_service.predict(stock_code)

                    if prediction and prediction.confidence >= confidence_threshold:
                        direction = "BUY" if prediction.predicted_direction == "UP" else "SELL"

                        signal = Signal(
                            stock_code=stock_code,
                            stock_name=quote.stock_name,
                            direction=direction,
                            price=quote.current_price,
                            quantity=100,
                            confidence=prediction.confidence,
                            strategy_name=self.name,
                            reason=f"LSTM预测{direction}，置信度{prediction.confidence:.1%}",
                            timestamp=datetime.now()
                        )
                        signals.append(signal)
            except Exception as e:
                print(f"预测策略处理{stock_code}失败: {e}")

        return signals

    def validate_config(self, config: dict) -> bool:
        if "confidence_threshold" not in config:
            return False
        threshold = config["confidence_threshold"]
        return 0 < threshold <= 1
