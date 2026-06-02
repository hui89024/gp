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

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # 实盘交易配置
    BROKER_TYPE: str = "eastmoney"
    BROKER_ACCOUNT: str = ""
    BROKER_PASSWORD: str = ""
    ENCRYPTION_KEY: str = ""  # AES加密密钥

    # 数据源配置
    PRIMARY_DATA_SOURCE: str = "efinance"
    FALLBACK_DATA_SOURCE: str = "akshare"

    # 实盘风控配置
    LIVE_MAX_INITIAL_CAPITAL: float = 100000.0
    LIVE_MAX_SINGLE_TRADE: float = 10000.0
    LIVE_MAX_DAILY_TRADES: int = 10
    LIVE_MAX_DAILY_LOSS: float = 5000.0
    LIVE_MAX_POSITION_RATIO: float = 0.2
    LIVE_STOP_LOSS_RATIO: float = -0.05

    class Config:
        env_file = ".env"


settings = Settings()
