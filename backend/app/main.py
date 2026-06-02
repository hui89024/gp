from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    account_router, trade_router, stock_router,
    prediction_router, review_router, auto_trading_router,
    backtest_router, risk_control_router, auth_router,
    broker_router, live_trade_router, fundamental_router,
    market_accounts_router, orders_router
)
from app.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="股票交易系统",
    description="模拟炒股系统API，包含预测、复盘和自动交易功能",
    version="3.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(account_router)
app.include_router(trade_router)
app.include_router(stock_router)
app.include_router(prediction_router)
app.include_router(review_router)
app.include_router(auto_trading_router)
app.include_router(backtest_router)
app.include_router(risk_control_router)
app.include_router(auth_router)
app.include_router(broker_router)
app.include_router(live_trade_router)
app.include_router(fundamental_router)
app.include_router(market_accounts_router)
app.include_router(orders_router)


@app.get("/")
def root():
    return {"message": "股票交易系统 API v3.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}