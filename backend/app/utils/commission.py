from app.config import settings


def calculate_commission(trade_type: str, price: float, quantity: int) -> dict:
    """
    计算交易手续费

    Args:
        trade_type: 交易类型 (BUY/SELL)
        price: 成交价格
        quantity: 成交数量

    Returns:
        手续费明细字典
    """
    total_amount = price * quantity

    # 佣金：最低5元
    commission = max(total_amount * settings.COMMISSION_RATE, 5.0)

    # 印花税：仅卖出时收取
    stamp_tax = total_amount * settings.STAMP_TAX_RATE if trade_type == "SELL" else 0.0

    # 过户费
    transfer_fee = total_amount * settings.TRANSFER_FEE_RATE

    total = commission + stamp_tax + transfer_fee

    return {
        "commission": round(commission, 2),
        "stamp_tax": round(stamp_tax, 2),
        "transfer_fee": round(transfer_fee, 2),
        "total": round(total, 2)
    }