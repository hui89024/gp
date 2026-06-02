from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Date, ARRAY
from sqlalchemy.sql import func
from app.database import Base


class BacktestRecord(Base):
    __tablename__ = "backtest_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_name = Column(String(50))
    strategy_config = Column(JSON)
    start_date = Column(Date)
    end_date = Column(Date)
    initial_capital = Column(Float)
    stock_codes = Column(ARRAY(String))

    total_return = Column(Float)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    profit_loss_ratio = Column(Float)
    total_trades = Column(Integer)

    trades = Column(JSON)
    equity_curve = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
