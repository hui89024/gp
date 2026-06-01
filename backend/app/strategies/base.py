from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class Signal:
    stock_code: str
    stock_name: str
    direction: str  # BUY/SELL
    price: float
    quantity: int
    confidence: float
    strategy_name: str
    reason: str
    timestamp: datetime


class BaseStrategy(ABC):
    """策略基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass
