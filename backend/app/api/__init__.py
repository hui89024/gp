from app.api.account import router as account_router
from app.api.trade import router as trade_router
from app.api.stock import router as stock_router
from app.api.prediction import router as prediction_router
from app.api.review import router as review_router
from app.api.auto_trading import router as auto_trading_router
from app.api.backtest import router as backtest_router

__all__ = [
    "account_router", "trade_router", "stock_router",
    "prediction_router", "review_router", "auto_trading_router", "backtest_router"
]