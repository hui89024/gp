from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from app.strategies.base import BaseStrategy, Signal
from app.services.data_service import DataService


class MAStrategy(BaseStrategy):
    """均线策略"""

    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.data_service = DataService()

    @property
    def name(self) -> str:
        return "MAStrategy"

    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        signals = []
        short_period = self.config.get("short_period", 5)
        long_period = self.config.get("long_period", 20)

        for stock_code in stock_codes:
            try:
                history = self.data_service.get_stock_history(stock_code, days=long_period + 5)
                if len(history) < long_period:
                    continue

                closes = [h.close for h in history]
                short_ma = np.mean(closes[-short_period:])
                long_ma = np.mean(closes[-long_period:])
                prev_short_ma = np.mean(closes[-(short_period+1):-1])
                prev_long_ma = np.mean(closes[-(long_period+1):-1])

                quote = self.data_service.get_stock_quote(stock_code)
                if not quote:
                    continue

                direction = None
                reason = ""

                if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                    direction = "BUY"
                    reason = f"MA{short_period}上穿MA{long_period}，金叉买入"
                elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                    direction = "SELL"
                    reason = f"MA{short_period}下穿MA{long_period}，死叉卖出"

                if direction:
                    signal = Signal(
                        stock_code=stock_code,
                        stock_name=quote.stock_name,
                        direction=direction,
                        price=quote.current_price,
                        quantity=100,
                        confidence=0.6,
                        strategy_name=self.name,
                        reason=reason,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
            except Exception as e:
                print(f"均线策略处理{stock_code}失败: {e}")

        return signals

    def validate_config(self, config: dict) -> bool:
        short_period = config.get("short_period", 5)
        long_period = config.get("long_period", 20)
        return 0 < short_period < long_period
