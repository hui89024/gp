import pytest
from app.utils.commission import calculate_commission


def test_calculate_commission_buy():
    """测试买入手续费计算"""
    commission = calculate_commission(
        trade_type="BUY",
        price=10.0,
        quantity=1000
    )
    # 佣金: 10000 * 0.025% = 2.5, 最低5元
    # 过户费: 10000 * 0.001% = 0.1
    assert commission["commission"] == 5.0
    assert commission["transfer_fee"] == 0.1
    assert commission["stamp_tax"] == 0.0
    assert commission["total"] == 5.1


def test_calculate_commission_sell():
    """测试卖出手续费计算"""
    commission = calculate_commission(
        trade_type="SELL",
        price=10.0,
        quantity=1000
    )
    # 佣金: 10000 * 0.025% = 2.5, 最低5元
    # 印花税: 10000 * 0.1% = 10
    # 过户费: 10000 * 0.001% = 0.1
    assert commission["commission"] == 5.0
    assert commission["stamp_tax"] == 10.0
    assert commission["transfer_fee"] == 0.1
    assert commission["total"] == 15.1


def test_calculate_commission_large_amount():
    """测试大额交易手续费"""
    commission = calculate_commission(
        trade_type="SELL",
        price=100.0,
        quantity=10000
    )
    # 佣金: 1000000 * 0.025% = 250
    # 印花税: 1000000 * 0.1% = 1000
    # 过户费: 1000000 * 0.001% = 10
    assert commission["commission"] == 250.0
    assert commission["stamp_tax"] == 1000.0
    assert commission["transfer_fee"] == 10.0
    assert commission["total"] == 1260.0