from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from app.strategies.base import BaseStrategy, Signal
from app.services.data_service import DataService


class RSIStrategy(BaseStrategy):
    """RSI策略"""

    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.data_service = DataService()

    @property
    def name(self) -> str:
        return "RSIStrategy"

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices[-(period+1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        signals = []
        rsi_period = self.config.get("rsi_period", 14)
        oversold_threshold = self.config.get("oversold_threshold", 30)
        overbought_threshold = self.config.get("overbought_threshold", 70)

        for stock_code in stock_codes:
            try:
                history = self.data_service.get_stock_history(stock_code, days=rsi_period + 5)
                if len(history) < rsi_period + 1:
                    continue

                closes = [h.close for h in history]
                rsi = self._calculate_rsi(closes, rsi_period)

                quote = self.data_service.get_stock_quote(stock_code)
                if not quote:
                    continue

                direction = None
                reason = ""

                if rsi <= oversold_threshold:
                    direction = "BUY"
                    reason = f"RSI={rsi:.1f}，处于超卖区域，买入"
                elif rsi >= overbought_threshold:
                    direction = "SELL"
                    reason = f"RSI={rsi:.1f}，处于超买区域，卖出"

                if direction:
                    signal = Signal(
                        stock_code=stock_code,
                        stock_name=quote.stock_name,
                        direction=direction,
                        price=quote.current_price,
                        quantity=100,
                        confidence=0.65,
                        strategy_name=self.name,
                        reason=reason,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
            except Exception as e:
                print(f"RSI策略处理{stock_code}失败: {e}")

        return signals

    def validate_config(self, config: dict) -> bool:
        oversold = config.get("oversold_threshold", 30)
        overbought = config.get("overbought_threshold", 70)
        return 0 < oversold < overbought < 100
