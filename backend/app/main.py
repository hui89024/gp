from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account_router, trade_router, stock_router
from app.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="股票交易系统",
    description="模拟炒股系统API",
    version="1.0.0"
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


@app.get("/")
def root():
    return {"message": "股票交易系统 API"}


@app.get("/health")
def health():
    return {"status": "healthy"}