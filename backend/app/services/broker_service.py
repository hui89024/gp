import easytrader
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.services.encryption import encryption_service


class BrokerService:
    """券商对接服务"""

    def __init__(self, db: Session):
        self.db = db
        self._user = None
        self._account_id = None

    def login(self, account_id: int) -> bool:
        """登录券商账户"""
        broker_account = self.db.query(BrokerAccount).filter(
            BrokerAccount.id == account_id,
            BrokerAccount.is_active == True
        ).first()

        if not broker_account:
            raise ValueError("券商账户不存在或已禁用")

        password = encryption_service.decrypt(broker_account.password_encrypted)

        self._user = easytrader.use(broker_account.broker_type)
        self._user.prepare(broker_account.account, password)

        broker_account.last_login_at = datetime.utcnow()
        self.db.commit()
        self._account_id = account_id
        return True

    def buy(self, stock_code: str, price: float, quantity: int) -> dict:
        """买入股票"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.buy(stock_code, price=price, amount=quantity)

    def sell(self, stock_code: str, price: float, quantity: int) -> dict:
        """卖出股票"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.sell(stock_code, price=price, amount=quantity)

    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.cancel_entrust(order_id)

    def get_positions(self) -> List[dict]:
        """查询持仓"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.position

    def get_balance(self) -> dict:
        """查询资金"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.balance

    def get_today_trades(self) -> list:
        """查询当日成交"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.today_trades

    def get_today_entrusts(self) -> list:
        """查询当日委托"""
        if not self._user:
            raise RuntimeError("请先登录券商账户")
        return self._user.today_entrusts
