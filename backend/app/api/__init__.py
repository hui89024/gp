from app.api.account import router as account_router
from app.api.trade import router as trade_router
from app.api.stock import router as stock_router
from app.api.prediction import router as prediction_router
from app.api.review import router as review_router
from app.api.auto_trading import router as auto_trading_router
from app.api.backtest import router as backtest_router
from app.api.risk_control import router as risk_control_router
from app.api.auth import router as auth_router
from app.api.broker import router as broker_router
from app.api.live_trade import router as live_trade_router
from app.api.fundamental import router as fundamental_router

__all__ = [
    "account_router", "trade_router", "stock_router",
    "prediction_router", "review_router", "auto_trading_router", "backtest_router",
    "risk_control_router", "auth_router",
    "broker_router", "live_trade_router", "fundamental_router"
]