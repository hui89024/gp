import pytest
from datetime import datetime, time
from app.services.market_rules import (
    MarketRules, CNRules, HKRules, USRules,
    MarketRulesFactory, PriceLimitType
)


def test_cn_trading_hours():
    rules = CNRules()
    assert rules.is_trading_time(datetime(2026, 6, 2, 10, 0)) == True
    assert rules.is_trading_time(datetime(2026, 6, 2, 14, 0)) == True
    assert rules.is_trading_time(datetime(2026, 6, 2, 8, 0)) == False
    assert rules.is_trading_time(datetime(2026, 6, 2, 12, 0)) == False
    assert rules.is_trading_time(datetime(2026, 6, 2, 16, 0)) == False


def test_cn_price_limit():
    rules = CNRules()
    # Normal ±10%
    assert rules.check_price_limit(100.0, 110.0, PriceLimitType.NORMAL) == True
    assert rules.check_price_limit(100.0, 111.0, PriceLimitType.NORMAL) == False
    assert rules.check_price_limit(100.0, 90.0, PriceLimitType.NORMAL) == True
    assert rules.check_price_limit(100.0, 89.0, PriceLimitType.NORMAL) == False
    # STAR ±20%
    assert rules.check_price_limit(100.0, 120.0, PriceLimitType.STAR) == True
    assert rules.check_price_limit(100.0, 121.0, PriceLimitType.STAR) == False
    # ST ±5%
    assert rules.check_price_limit(100.0, 105.0, PriceLimitType.ST) == True
    assert rules.check_price_limit(100.0, 106.0, PriceLimitType.ST) == False


def test_cn_lot_size():
    rules = CNRules()
    assert rules.validate_quantity(100) == True
    assert rules.validate_quantity(200) == True
    assert rules.validate_quantity(150) == False
    assert rules.validate_quantity(0) == False


def test_cn_commission():
    rules = CNRules()
    buy_commission = rules.calculate_commission("BUY", 10.0, 1000)
    assert buy_commission["commission"] == max(10.0 * 1000 * 0.00025, 5.0)
    assert buy_commission["stamp_tax"] == 0.0
    assert buy_commission["transfer_fee"] == 10.0 * 1000 * 0.00001

    sell_commission = rules.calculate_commission("SELL", 10.0, 1000)
    assert sell_commission["commission"] == max(10.0 * 1000 * 0.00025, 5.0)
    assert sell_commission["stamp_tax"] == 10.0 * 1000 * 0.001
    assert sell_commission["transfer_fee"] == 10.0 * 1000 * 0.00001


def test_hk_trading_hours():
    rules = HKRules()
    assert rules.is_trading_time(datetime(2026, 6, 2, 10, 0)) == True
    assert rules.is_trading_time(datetime(2026, 6, 2, 15, 0)) == True
    assert rules.is_trading_time(datetime(2026, 6, 2, 12, 30)) == False


def test_hk_no_price_limit():
    rules = HKRules()
    assert rules.check_price_limit(100.0, 200.0) == True
    assert rules.check_price_limit(100.0, 50.0) == True


def test_hk_lot_size():
    rules = HKRules()
    assert rules.validate_quantity(100, "00700") == True
    assert rules.validate_quantity(50, "00700") == False
    assert rules.validate_quantity(1000, "99999") == True
    assert rules.validate_quantity(500, "99999") == False


def test_us_trading_hours():
    rules = USRules()
    assert rules.is_trading_time(datetime(2026, 6, 2, 10, 0)) == True
    assert rules.is_trading_time(datetime(2026, 6, 2, 15, 0)) == True
    assert rules.is_trading_time(datetime(2026, 6, 2, 3, 0)) == False


def test_us_no_price_limit():
    rules = USRules()
    assert rules.check_price_limit(100.0, 500.0) == True
    assert rules.check_price_limit(100.0, 10.0) == True


def test_us_lot_size():
    rules = USRules()
    assert rules.validate_quantity(1) == True
    assert rules.validate_quantity(0) == False


def test_market_rules_factory():
    cn_rules = MarketRulesFactory.get_rules("CN")
    assert isinstance(cn_rules, CNRules)
    hk_rules = MarketRulesFactory.get_rules("HK")
    assert isinstance(hk_rules, HKRules)
    us_rules = MarketRulesFactory.get_rules("US")
    assert isinstance(us_rules, USRules)
    with pytest.raises(ValueError):
        MarketRulesFactory.get_rules("INVALID")
