from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/stock_trading"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 应用配置
    APP_NAME: str = "Stock Trading System"
    DEBUG: bool = True

    # 交易配置
    INITIAL_CAPITAL: float = 1000000.0  # 初始资金100万
    COMMISSION_RATE: float = 0.00025    # 佣金费率0.025%
    STAMP_TAX_RATE: float = 0.001       # 印花税0.1%
    TRANSFER_FEE_RATE: float = 0.00001  # 过户费0.001%

    class Config:
        env_file = ".env"


settings = Settings()
