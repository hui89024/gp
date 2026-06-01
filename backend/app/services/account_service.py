from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.position import Position
from app.schemas.user import AccountOverview


class AccountService:
    """账户服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        username: str,
        initial_capital: float = 1000000.0
    ) -> User:
        """
        创建用户

        Args:
            username: 用户名
            initial_capital: 初始资金

        Returns:
            创建的用户
        """
        user = User(
            username=username,
            initial_capital=initial_capital,
            current_capital=initial_capital
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()

    def get_account_overview(self, user_id: int) -> AccountOverview:
        """
        获取账户概览

        Args:
            user_id: 用户ID

        Returns:
            账户概览
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 计算持仓市值
        positions = self.db.query(Position).filter(
            Position.user_id == user_id
        ).all()

        market_value = sum(
            p.quantity * (p.current_price or p.avg_cost)
            for p in positions
        )

        total_assets = user.current_capital + market_value
        total_pnl = total_assets - user.initial_capital

        return AccountOverview(
            total_assets=total_assets,
            available_capital=user.current_capital,
            market_value=market_value,
            total_pnl=total_pnl,
            today_pnl=0.0
        )
