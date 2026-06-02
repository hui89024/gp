from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Optional
from enum import Enum


class PriceLimitType(Enum):
    NORMAL = "normal"  # 普通股票
    STAR = "star"      # 科创板
    GEM = "gem"        # 创业板
    ST = "st"          # ST股


class MarketRules(ABC):
    """市场规则基类"""

    @property
    @abstractmethod
    def market(self) -> str:
        pass

    @property
    @abstractmethod
    def currency(self) -> str:
        pass

    @abstractmethod
    def is_trading_time(self, dt: datetime) -> bool:
        pass

    @abstractmethod
    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        pass

    @abstractmethod
    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        pass

    @abstractmethod
    def get_t_plus_n(self) -> int:
        pass


class CNRules(MarketRules):
    """A股市场规则"""

    @property
    def market(self) -> str:
        return "CN"

    @property
    def currency(self) -> str:
        return "CNY"

    def is_trading_time(self, dt: datetime) -> bool:
        t = dt.time()
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)
        return (morning_start <= t <= morning_end) or (afternoon_start <= t <= afternoon_end)

    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        if limit_type is None:
            limit_type = PriceLimitType.NORMAL
        change_pct = (target_price - base_price) / base_price
        limits = {
            PriceLimitType.NORMAL: 0.10,
            PriceLimitType.STAR: 0.20,
            PriceLimitType.GEM: 0.20,
            PriceLimitType.ST: 0.05,
        }
        limit = limits.get(limit_type, 0.10)
        return -limit <= change_pct <= limit

    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        return quantity > 0 and quantity % 100 == 0

    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        total_amount = price * quantity
        commission = max(total_amount * 0.00025, 5.0)
        stamp_tax = total_amount * 0.001 if trade_type == "SELL" else 0.0
        transfer_fee = total_amount * 0.00001
        total = commission + stamp_tax + transfer_fee
        return {
            "commission": round(commission, 2),
            "stamp_tax": round(stamp_tax, 2),
            "transfer_fee": round(transfer_fee, 2),
            "total": round(total, 2)
        }

    def get_t_plus_n(self) -> int:
        return 1  # T+1


class HKRules(MarketRules):
    """港股市场规则"""

    LOT_SIZES = {
        "00700": 100,   # 腾讯
        "09988": 100,   # 阿里
        "00005": 400,   # 汇丰
        "default": 1000
    }

    @property
    def market(self) -> str:
        return "HK"

    @property
    def currency(self) -> str:
        return "HKD"

    def is_trading_time(self, dt: datetime) -> bool:
        t = dt.time()
        morning_start = time(9, 30)
        morning_end = time(12, 0)
        afternoon_start = time(13, 0)
        afternoon_end = time(16, 0)
        return (morning_start <= t <= morning_end) or (afternoon_start <= t <= afternoon_end)

    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        return True  # 港股无涨跌停限制

    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        if stock_code and stock_code in self.LOT_SIZES:
            lot_size = self.LOT_SIZES[stock_code]
        else:
            lot_size = self.LOT_SIZES["default"]
        return quantity > 0 and quantity % lot_size == 0

    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        total_amount = price * quantity
        commission = max(total_amount * 0.0003, 50.0)
        stamp_tax = total_amount * 0.0013
        trading_fee = total_amount * 0.00005
        sfc = total_amount * 0.000027
        total = commission + stamp_tax + trading_fee + sfc
        return {
            "commission": round(commission, 2),
            "stamp_tax": round(stamp_tax, 2),
            "trading_fee": round(trading_fee, 2),
            "sfc": round(sfc, 2),
            "total": round(total, 2)
        }

    def get_t_plus_n(self) -> int:
        return 0  # T+0


class USRules(MarketRules):
    """美股市场规则"""

    @property
    def market(self) -> str:
        return "US"

    @property
    def currency(self) -> str:
        return "USD"

    def is_trading_time(self, dt: datetime) -> bool:
        t = dt.time()
        regular_start = time(9, 30)
        regular_end = time(16, 0)
        return regular_start <= t <= regular_end

    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        return True  # 美股无涨跌停限制

    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        return quantity > 0  # 美股可以买1股

    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        total_amount = price * quantity
        commission = 0.0  # 零佣金
        sec = total_amount * 0.0000278
        taf = total_amount * 0.000166
        total = commission + sec + taf
        return {
            "commission": round(commission, 2),
            "sec": round(sec, 2),
            "taf": round(taf, 2),
            "total": round(total, 2)
        }

    def get_t_plus_n(self) -> int:
        return 0  # T+0


class MarketRulesFactory:
    """市场规则工厂"""

    _rules = {
        "CN": CNRules,
        "HK": HKRules,
        "US": USRules,
    }

    @classmethod
    def get_rules(cls, market: str) -> MarketRules:
        if market not in cls._rules:
            raise ValueError(f"不支持的市场: {market}")
        return cls._rules[market]()
