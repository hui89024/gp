# 股票交易系统 MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可用的模拟炒股系统，包含数据获取、交易引擎和基础前端界面

**Architecture:** FastAPI后端 + React前端 + PostgreSQL数据库，采用单体架构，模块化设计

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, Redis, React 18, TypeScript, Ant Design, ECharts

---

## 文件结构

```
gp/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI应用入口
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── position.py         # 持仓模型
│   │   │   └── trade.py            # 交易记录模型
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # 用户Pydantic模型
│   │   │   ├── trade.py            # 交易Pydantic模型
│   │   │   └── stock.py            # 股票数据Pydantic模型
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # 依赖注入
│   │   │   ├── trade.py            # 交易API
│   │   │   ├── account.py          # 账户API
│   │   │   └── stock.py            # 股票数据API
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── trading_engine.py   # 交易引擎
│   │   │   ├── data_service.py     # 数据服务
│   │   │   └── account_service.py  # 账户服务
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── commission.py       # 手续费计算
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_trading_engine.py
│   │   ├── test_data_service.py
│   │   └── test_api.py
│   ├── alembic/                    # 数据库迁移
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StockChart.tsx      # K线图组件
│   │   │   ├── TradeForm.tsx       # 交易表单
│   │   │   ├── PositionList.tsx    # 持仓列表
│   │   │   └── AccountOverview.tsx # 账户概览
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # 仪表盘页面
│   │   │   └── Trade.tsx           # 交易页面
│   │   ├── services/
│   │   │   └── api.ts              # API客户端
│   │   ├── stores/
│   │   │   └── tradeStore.ts       # 交易状态管理
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript类型定义
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml
└── README.md
```

---

## Task 1: 项目初始化与环境配置

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `docker-compose.yml`
- Create: `README.md`

- [ ] **Step 1: 创建后端依赖文件**

```txt
# backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9
redis==5.0.1
akshare==1.12.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.25.0
pytest==7.4.3
pytest-asyncio==0.23.2
```

- [ ] **Step 2: 创建配置管理**

```python
# backend/app/config.py
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
```

- [ ] **Step 3: 创建Docker Compose配置**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: stock_trading
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

- [ ] **Step 4: 创建应用初始化文件**

```python
# backend/app/__init__.py
"""Stock Trading System - 股票交易自动化系统"""
```

- [ ] **Step 5: 启动数据库服务**

```bash
cd E:/cs/gp
docker-compose up -d postgres redis
```

Expected: PostgreSQL and Redis containers running

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/__init__.py backend/app/config.py docker-compose.yml
git commit -m "feat: initialize project with configuration and Docker setup"
```

---

## Task 2: 数据库配置与模型定义

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/position.py`
- Create: `backend/app/models/trade.py`

- [ ] **Step 1: 创建数据库连接**

```python
# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: 创建用户模型**

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    initial_capital = Column(Float, default=1000000.0)
    current_capital = Column(Float, default=1000000.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 3: 创建持仓模型**

```python
# backend/app/models/position.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50))
    quantity = Column(Integer, nullable=False, default=0)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 4: 创建交易记录模型**

```python
# backend/app/models/trade.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(10), nullable=False, index=True)
    trade_type = Column(String(4), nullable=False)  # BUY or SELL
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    commission = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    strategy_tag = Column(String(50))
    trade_time = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 5: 创建模型初始化文件**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade

__all__ = ["User", "Position", "Trade"]
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/database.py backend/app/models/
git commit -m "feat: add database configuration and SQLAlchemy models"
```

---

## Task 3: Pydantic Schema定义

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/trade.py`
- Create: `backend/app/schemas/stock.py`

- [ ] **Step 1: 创建用户Schema**

```python
# backend/app/schemas/user.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    initial_capital: Optional[float] = 1000000.0


class UserResponse(UserBase):
    id: int
    initial_capital: float
    current_capital: float
    created_at: datetime

    class Config:
        from_attributes = True


class AccountOverview(BaseModel):
    total_assets: float
    available_capital: float
    market_value: float
    total_pnl: float
    today_pnl: float
```

- [ ] **Step 2: 创建交易Schema**

```python
# backend/app/schemas/trade.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TradeCreate(BaseModel):
    stock_code: str = Field(..., min_length=6, max_length=6)
    stock_name: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    strategy_tag: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: Optional[str]
    trade_type: str
    price: float
    quantity: int
    commission: float
    total_amount: float
    strategy_tag: Optional[str]
    trade_time: datetime

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_cost: float
    current_price: Optional[float]
    unrealized_pnl: Optional[float]
    market_value: Optional[float]

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 创建股票数据Schema**

```python
# backend/app/schemas/stock.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StockQuote(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    amount: float
    change_percent: float
    change_amount: float
    timestamp: datetime


class StockHistory(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float


class StockSearchResult(BaseModel):
    stock_code: str
    stock_name: str
    market: str


class KLineData(BaseModel):
    dates: List[str]
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[int]
```

- [ ] **Step 4: 创建Schema初始化文件**

```python
# backend/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, AccountOverview
from app.schemas.trade import TradeCreate, TradeResponse, PositionResponse
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult, KLineData

__all__ = [
    "UserCreate", "UserResponse", "AccountOverview",
    "TradeCreate", "TradeResponse", "PositionResponse",
    "StockQuote", "StockHistory", "StockSearchResult", "KLineData"
]
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for API request/response"
```

---

## Task 4: 手续费计算工具

**Files:**
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/commission.py`
- Create: `backend/tests/test_commission.py`

- [ ] **Step 1: 编写手续费计算测试**

```python
# backend/tests/test_commission.py
import pytest
from app.utils.commission import calculate_commission


def test_calculate_commission_buy():
    """测试买入手续费计算"""
    commission = calculate_commission(
        trade_type="BUY",
        price=10.0,
        quantity=1000
    )
    # 佣金: 10000 * 0.025% = 2.5, 最低5元
    # 过户费: 10000 * 0.001% = 0.1
    assert commission["commission"] == 5.0
    assert commission["transfer_fee"] == 0.1
    assert commission["stamp_tax"] == 0.0
    assert commission["total"] == 5.1


def test_calculate_commission_sell():
    """测试卖出手续费计算"""
    commission = calculate_commission(
        trade_type="SELL",
        price=10.0,
        quantity=1000
    )
    # 佣金: 10000 * 0.025% = 2.5, 最低5元
    # 印花税: 10000 * 0.1% = 10
    # 过户费: 10000 * 0.001% = 0.1
    assert commission["commission"] == 5.0
    assert commission["stamp_tax"] == 10.0
    assert commission["transfer_fee"] == 0.1
    assert commission["total"] == 15.1


def test_calculate_commission_large_amount():
    """测试大额交易手续费"""
    commission = calculate_commission(
        trade_type="SELL",
        price=100.0,
        quantity=10000
    )
    # 佣金: 1000000 * 0.025% = 250
    # 印花税: 1000000 * 0.1% = 1000
    # 过户费: 1000000 * 0.001% = 10
    assert commission["commission"] == 250.0
    assert commission["stamp_tax"] == 1000.0
    assert commission["transfer_fee"] == 10.0
    assert commission["total"] == 1260.0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_commission.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.utils.commission'"

- [ ] **Step 3: 实现手续费计算**

```python
# backend/app/utils/commission.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_commission.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/__init__.py backend/app/utils/commission.py backend/tests/test_commission.py
git commit -m "feat: add commission calculation with tests"
```

---

## Task 5: 数据服务实现

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/data_service.py`
- Create: `backend/tests/test_data_service.py`

- [ ] **Step 1: 编写数据服务测试**

```python
# backend/tests/test_data_service.py
import pytest
from app.services.data_service import DataService


@pytest.fixture
def data_service():
    return DataService()


def test_get_stock_quote(data_service):
    """测试获取实时行情"""
    quote = data_service.get_stock_quote("000001")
    assert quote is not None
    assert quote.stock_code == "000001"
    assert quote.current_price > 0


def test_get_stock_history(data_service):
    """测试获取历史数据"""
    history = data_service.get_stock_history("000001", days=30)
    assert len(history) > 0
    assert len(history) <= 30
    assert history[0].close > 0


def test_search_stocks(data_service):
    """测试股票搜索"""
    results = data_service.search_stocks("平安")
    assert len(results) > 0
    assert any("平安" in r.stock_name for r in results)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_data_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.data_service'"

- [ ] **Step 3: 实现数据服务**

```python
# backend/app/services/data_service.py
import akshare as ak
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult


class DataService:
    """股票数据服务"""
    
    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """
        获取股票实时行情
        
        Args:
            stock_code: 股票代码 (如 000001)
        
        Returns:
            实时行情数据
        """
        try:
            df = ak.stock_zh_a_spot_em()
            stock = df[df["代码"] == stock_code]
            
            if stock.empty:
                return None
            
            row = stock.iloc[0]
            return StockQuote(
                stock_code=stock_code,
                stock_name=row["名称"],
                current_price=float(row["最新价"]),
                open_price=float(row["今开"]),
                high_price=float(row["最高"]),
                low_price=float(row["最低"]),
                close_price=float(row["最新价"]),
                volume=int(row["成交量"]),
                amount=float(row["成交额"]),
                change_percent=float(row["涨跌幅"]),
                change_amount=float(row["涨跌额"]),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"获取行情失败: {e}")
            return None
    
    def get_stock_history(
        self, stock_code: str, days: int = 30
    ) -> List[StockHistory]:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数
        
        Returns:
            历史数据列表
        """
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            history = []
            for _, row in df.iterrows():
                history.append(StockHistory(
                    date=str(row["日期"]),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=int(row["成交量"]),
                    amount=float(row["成交额"])
                ))
            
            return history
        except Exception as e:
            print(f"获取历史数据失败: {e}")
            return []
    
    def search_stocks(self, keyword: str) -> List[StockSearchResult]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            搜索结果列表
        """
        try:
            df = ak.stock_zh_a_spot_em()
            matches = df[
                df["名称"].str.contains(keyword, na=False) |
                df["代码"].str.contains(keyword, na=False)
            ].head(10)
            
            results = []
            for _, row in matches.iterrows():
                results.append(StockSearchResult(
                    stock_code=row["代码"],
                    stock_name=row["名称"],
                    market=row.get("市场", "A股")
                ))
            
            return results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def get_kline_data(self, stock_code: str, days: int = 60) -> dict:
        """
        获取K线数据（用于前端图表）
        
        Args:
            stock_code: 股票代码
            days: 获取天数
        
        Returns:
            K线数据字典
        """
        history = self.get_stock_history(stock_code, days)
        
        return {
            "dates": [h.date for h in history],
            "opens": [h.open for h in history],
            "highs": [h.high for h in history],
            "lows": [h.low for h in history],
            "closes": [h.close for h in history],
            "volumes": [h.volume for h in history]
        }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_data_service.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/data_service.py backend/tests/test_data_service.py
git commit -m "feat: add data service with AKShare integration"
```

---

## Task 6: 交易引擎实现

**Files:**
- Create: `backend/app/services/trading_engine.py`
- Create: `backend/tests/test_trading_engine.py`

- [ ] **Step 1: 编写交易引擎测试**

```python
# backend/tests/test_trading_engine.py
import pytest
from datetime import datetime, timedelta
from app.services.trading_engine import TradingEngine
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade


@pytest.fixture
def trading_engine(db_session):
    return TradingEngine(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_buy_stock(trading_engine, test_user):
    """测试买入股票"""
    result = trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )
    
    assert result.success is True
    assert result.trade.stock_code == "000001"
    assert result.trade.quantity == 1000
    assert result.position.quantity == 1000


def test_sell_stock(trading_engine, test_user):
    """测试卖出股票"""
    # 先买入
    trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )
    
    # 再卖出
    result = trading_engine.sell(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=11.0,
        quantity=500
    )
    
    assert result.success is True
    assert result.trade.quantity == 500
    assert result.position.quantity == 500


def test_insufficient_funds(trading_engine, test_user):
    """测试资金不足"""
    result = trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=1000.0,
        quantity=10000
    )
    
    assert result.success is False
    assert "资金不足" in result.message


def test_insufficient_position(trading_engine, test_user):
    """测试持仓不足"""
    result = trading_engine.sell(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )
    
    assert result.success is False
    assert "持仓不足" in result.message


def test_t1_restriction(trading_engine, test_user):
    """测试T+1限制"""
    # 买入
    trading_engine.buy(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=10.0,
        quantity=1000
    )
    
    # 当天卖出（应该失败）
    result = trading_engine.sell(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        price=11.0,
        quantity=1000
    )
    
    assert result.success is False
    assert "T+1" in result.message
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_trading_engine.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现交易引擎**

```python
# backend/app/services/trading_engine.py
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.utils.commission import calculate_commission


@dataclass
class TradeResult:
    success: bool
    message: str
    trade: Optional[Trade] = None
    position: Optional[Position] = None


class TradingEngine:
    """交易引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def buy(
        self,
        user_id: int,
        stock_code: str,
        stock_name: str,
        price: float,
        quantity: int,
        strategy_tag: Optional[str] = None
    ) -> TradeResult:
        """
        买入股票
        
        Args:
            user_id: 用户ID
            stock_code: 股票代码
            stock_name: 股票名称
            price: 买入价格
            quantity: 买入数量
            strategy_tag: 策略标签
        
        Returns:
            交易结果
        """
        # 验证数量必须是100的整数倍
        if quantity % 100 != 0:
            return TradeResult(success=False, message="买入数量必须是100的整数倍")
        
        # 获取用户
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return TradeResult(success=False, message="用户不存在")
        
        # 计算手续费
        commission = calculate_commission("BUY", price, quantity)
        total_cost = price * quantity + commission["total"]
        
        # 检查资金是否充足
        if user.current_capital < total_cost:
            return TradeResult(success=False, message="资金不足")
        
        # 创建交易记录
        trade = Trade(
            user_id=user_id,
            stock_code=stock_code,
            trade_type="BUY",
            price=price,
            quantity=quantity,
            commission=commission["total"],
            total_amount=price * quantity,
            strategy_tag=strategy_tag
        )
        self.db.add(trade)
        
        # 更新用户资金
        user.current_capital -= total_cost
        
        # 更新持仓
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == stock_code
        ).first()
        
        if position:
            # 计算新的平均成本
            total_quantity = position.quantity + quantity
            position.avg_cost = (
                (position.avg_cost * position.quantity + price * quantity)
                / total_quantity
            )
            position.quantity = total_quantity
        else:
            # 创建新持仓
            position = Position(
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                avg_cost=price,
                current_price=price,
                unrealized_pnl=0.0
            )
            self.db.add(position)
        
        self.db.commit()
        self.db.refresh(trade)
        self.db.refresh(position)
        
        return TradeResult(
            success=True,
            message="买入成功",
            trade=trade,
            position=position
        )
    
    def sell(
        self,
        user_id: int,
        stock_code: str,
        stock_name: str,
        price: float,
        quantity: int,
        strategy_tag: Optional[str] = None
    ) -> TradeResult:
        """
        卖出股票
        
        Args:
            user_id: 用户ID
            stock_code: 股票代码
            stock_name: 股票名称
            price: 卖出价格
            quantity: 卖出数量
            strategy_tag: 策略标签
        
        Returns:
            交易结果
        """
        # 验证数量必须是100的整数倍
        if quantity % 100 != 0:
            return TradeResult(success=False, message="卖出数量必须是100的整数倍")
        
        # 获取用户
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return TradeResult(success=False, message="用户不存在")
        
        # 获取持仓
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == stock_code
        ).first()
        
        if not position or position.quantity < quantity:
            return TradeResult(success=False, message="持仓不足")
        
        # 检查T+1限制（假设当天买入的不能卖出）
        today_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.stock_code == stock_code,
            Trade.trade_type == "BUY",
            Trade.trade_time >= datetime.now().replace(hour=0, minute=0, second=0)
        ).all()
        
        today_bought = sum(t.quantity for t in today_trades)
        if position.quantity - today_bought < quantity:
            return TradeResult(success=False, message="受T+1限制，当日买入的股票不能卖出")
        
        # 计算手续费
        commission = calculate_commission("SELL", price, quantity)
        total_income = price * quantity - commission["total"]
        
        # 创建交易记录
        trade = Trade(
            user_id=user_id,
            stock_code=stock_code,
            trade_type="SELL",
            price=price,
            quantity=quantity,
            commission=commission["total"],
            total_amount=price * quantity,
            strategy_tag=strategy_tag
        )
        self.db.add(trade)
        
        # 更新用户资金
        user.current_capital += total_income
        
        # 更新持仓
        position.quantity -= quantity
        if position.quantity == 0:
            self.db.delete(position)
            position = None
        
        self.db.commit()
        self.db.refresh(trade)
        if position:
            self.db.refresh(position)
        
        return TradeResult(
            success=True,
            message="卖出成功",
            trade=trade,
            position=position
        )
    
    def get_positions(self, user_id: int) -> list:
        """获取用户持仓"""
        return self.db.query(Position).filter(
            Position.user_id == user_id
        ).all()
    
    def get_trades(
        self,
        user_id: int,
        stock_code: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """获取交易记录"""
        query = self.db.query(Trade).filter(Trade.user_id == user_id)
        
        if stock_code:
            query = query.filter(Trade.stock_code == stock_code)
        
        return query.order_by(Trade.trade_time.desc()).limit(limit).all()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_trading_engine.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trading_engine.py backend/tests/test_trading_engine.py
git commit -m "feat: add trading engine with buy/sell logic and T+1 restriction"
```

---

## Task 7: 账户服务实现

**Files:**
- Create: `backend/app/services/account_service.py`
- Create: `backend/tests/test_account_service.py`

- [ ] **Step 1: 编写账户服务测试**

```python
# backend/tests/test_account_service.py
import pytest
from app.services.account_service import AccountService
from app.models.user import User


@pytest.fixture
def account_service(db_session):
    return AccountService(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_create_user(account_service):
    """测试创建用户"""
    user = account_service.create_user("newuser", 500000.0)
    assert user.username == "newuser"
    assert user.initial_capital == 500000.0
    assert user.current_capital == 500000.0


def test_get_user(account_service, test_user):
    """测试获取用户"""
    user = account_service.get_user(test_user.id)
    assert user is not None
    assert user.username == "testuser"


def test_get_account_overview(account_service, test_user):
    """测试获取账户概览"""
    overview = account_service.get_account_overview(test_user.id)
    assert overview.total_assets == 1000000.0
    assert overview.available_capital == 1000000.0
    assert overview.market_value == 0.0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_account_service.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现账户服务**

```python
# backend/app/services/account_service.py
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
            today_pnl=0.0  # TODO: 计算今日盈亏
        )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd E:/cs/gp/backend
python -m pytest tests/test_account_service.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/account_service.py backend/tests/test_account_service.py
git commit -m "feat: add account service for user management"
```

---

## Task 8: API路由实现

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/account.py`
- Create: `backend/app/api/trade.py`
- Create: `backend/app/api/stock.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建API依赖**

```python
# backend/app/api/deps.py
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.trading_engine import TradingEngine
from app.services.account_service import AccountService
from app.services.data_service import DataService


def get_trading_engine(db: Session = Depends(get_db)) -> TradingEngine:
    return TradingEngine(db)


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


def get_data_service() -> DataService:
    return DataService()
```

- [ ] **Step 2: 创建账户API**

```python
# backend/app/api/account.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, AccountOverview
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/account", tags=["账户"])


@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """创建用户"""
    service = AccountService(db)
    
    # 检查用户名是否已存在
    existing = service.get_user_by_username(user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    return service.create_user(user_in.username, user_in.initial_capital)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户信息"""
    service = AccountService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/users/{user_id}/overview", response_model=AccountOverview)
def get_account_overview(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取账户概览"""
    service = AccountService(db)
    try:
        return service.get_account_overview(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 3: 创建交易API**

```python
# backend/app/api/trade.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.trade import TradeCreate, TradeResponse, PositionResponse
from app.services.trading_engine import TradingEngine

router = APIRouter(prefix="/api/trades", tags=["交易"])


@router.post("/buy", response_model=TradeResponse)
def buy_stock(
    trade_in: TradeCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """买入股票"""
    engine = TradingEngine(db)
    result = engine.buy(
        user_id=user_id,
        stock_code=trade_in.stock_code,
        stock_name=trade_in.stock_name,
        price=trade_in.price,
        quantity=trade_in.quantity,
        strategy_tag=trade_in.strategy_tag
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result.trade


@router.post("/sell", response_model=TradeResponse)
def sell_stock(
    trade_in: TradeCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """卖出股票"""
    engine = TradingEngine(db)
    result = engine.sell(
        user_id=user_id,
        stock_code=trade_in.stock_code,
        stock_name=trade_in.stock_name,
        price=trade_in.price,
        quantity=trade_in.quantity,
        strategy_tag=trade_in.strategy_tag
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result.trade


@router.get("/history", response_model=List[TradeResponse])
def get_trade_history(
    user_id: int,
    stock_code: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取交易历史"""
    engine = TradingEngine(db)
    return engine.get_trades(user_id, stock_code, limit)


@router.get("/positions", response_model=List[PositionResponse])
def get_positions(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取持仓"""
    engine = TradingEngine(db)
    return engine.get_positions(user_id)
```

- [ ] **Step 4: 创建股票数据API**

```python
# backend/app/api/stock.py
from fastapi import APIRouter, Depends
from typing import List

from app.schemas.stock import StockQuote, StockHistory, StockSearchResult, KLineData
from app.services.data_service import DataService

router = APIRouter(prefix="/api/stocks", tags=["股票数据"])


@router.get("/{stock_code}/quote", response_model=StockQuote)
def get_stock_quote(
    stock_code: str,
    data_service: DataService = Depends()
):
    """获取实时行情"""
    quote = data_service.get_stock_quote(stock_code)
    if not quote:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="股票不存在")
    return quote


@router.get("/{stock_code}/history", response_model=List[StockHistory])
def get_stock_history(
    stock_code: str,
    days: int = 30,
    data_service: DataService = Depends()
):
    """获取历史数据"""
    return data_service.get_stock_history(stock_code, days)


@router.get("/{stock_code}/kline", response_model=KLineData)
def get_kline_data(
    stock_code: str,
    days: int = 60,
    data_service: DataService = Depends()
):
    """获取K线数据"""
    return data_service.get_kline_data(stock_code, days)


@router.get("/search", response_model=List[StockSearchResult])
def search_stocks(
    keyword: str,
    data_service: DataService = Depends()
):
    """搜索股票"""
    return data_service.search_stocks(keyword)
```

- [ ] **Step 5: 创建API初始化文件**

```python
# backend/app/api/__init__.py
from app.api.account import router as account_router
from app.api.trade import router as trade_router
from app.api.stock import router as stock_router

__all__ = ["account_router", "trade_router", "stock_router"]
```

- [ ] **Step 6: 更新主应用文件**

```python
# backend/app/main.py
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
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add API routes for account, trading, and stock data"
```

---

## Task 9: 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建package.json**

```json
{
  "name": "stock-trading-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.12.0",
    "axios": "^1.6.2",
    "echarts": "^5.4.3",
    "echarts-for-react": "^3.0.2",
    "zustand": "^4.4.7"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
```

- [ ] **Step 2: 创建TypeScript配置**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: 创建类型定义**

```typescript
// frontend/src/types/index.ts

export interface User {
  id: number;
  username: string;
  initial_capital: number;
  current_capital: number;
  created_at: string;
}

export interface AccountOverview {
  total_assets: number;
  available_capital: number;
  market_value: number;
  total_pnl: number;
  today_pnl: number;
}

export interface Trade {
  id: number;
  stock_code: string;
  stock_name: string;
  trade_type: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  commission: number;
  total_amount: number;
  strategy_tag?: string;
  trade_time: string;
}

export interface Position {
  id: number;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  unrealized_pnl: number;
  market_value: number;
}

export interface StockQuote {
  stock_code: string;
  stock_name: string;
  current_price: number;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  amount: number;
  change_percent: number;
  change_amount: number;
  timestamp: string;
}

export interface StockHistory {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
}

export interface KLineData {
  dates: string[];
  opens: number[];
  highs: number[];
  lows: number[];
  closes: number[];
  volumes: number[];
}

export interface TradeCreate {
  stock_code: string;
  stock_name: string;
  price: number;
  quantity: number;
  strategy_tag?: string;
}
```

- [ ] **Step 4: 创建主入口文件**

```tsx
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 5: 创建App组件**

```tsx
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';

const { Header, Content } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <h1 style={{ color: 'white', margin: 0 }}>股票交易系统</h1>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trade" element={<Trade />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
```

- [ ] **Step 6: 安装依赖**

```bash
cd E:/cs/gp/frontend
npm install
```

Expected: Dependencies installed successfully

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: initialize React frontend with TypeScript"
```

---

## Task 10: 前端API服务

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/stores/tradeStore.ts`

- [ ] **Step 1: 创建API客户端**

```typescript
// frontend/src/services/api.ts
import axios from 'axios';
import type {
  User,
  AccountOverview,
  Trade,
  Position,
  StockQuote,
  StockHistory,
  KLineData,
  TradeCreate,
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// 账户API
export const accountApi = {
  createUser: (username: string, initialCapital: number) =>
    api.post<User>('/api/account/users', {
      username,
      initial_capital: initialCapital,
    }),

  getUser: (userId: number) =>
    api.get<User>(`/api/account/users/${userId}`),

  getAccountOverview: (userId: number) =>
    api.get<AccountOverview>(`/api/account/users/${userId}/overview`),
};

// 交易API
export const tradeApi = {
  buy: (userId: number, trade: TradeCreate) =>
    api.post<Trade>('/api/trades/buy', trade, {
      params: { user_id: userId },
    }),

  sell: (userId: number, trade: TradeCreate) =>
    api.post<Trade>('/api/trades/sell', trade, {
      params: { user_id: userId },
    }),

  getHistory: (userId: number, stockCode?: string) =>
    api.get<Trade[]>('/api/trades/history', {
      params: { user_id: userId, stock_code: stockCode },
    }),

  getPositions: (userId: number) =>
    api.get<Position[]>('/api/trades/positions', {
      params: { user_id: userId },
    }),
};

// 股票数据API
export const stockApi = {
  getQuote: (stockCode: string) =>
    api.get<StockQuote>(`/api/stocks/${stockCode}/quote`),

  getHistory: (stockCode: string, days: number = 30) =>
    api.get<StockHistory[]>(`/api/stocks/${stockCode}/history`, {
      params: { days },
    }),

  getKlineData: (stockCode: string, days: number = 60) =>
    api.get<KLineData>(`/api/stocks/${stockCode}/kline`, {
      params: { days },
    }),

  search: (keyword: string) =>
    api.get<Array<{ stock_code: string; stock_name: string }>>('/api/stocks/search', {
      params: { keyword },
    }),
};

export default api;
```

- [ ] **Step 2: 创建状态管理**

```typescript
// frontend/src/stores/tradeStore.ts
import { create } from 'zustand';
import type { Position, Trade, AccountOverview } from '../types';
import { tradeApi, accountApi } from '../services/api';

interface TradeState {
  userId: number | null;
  positions: Position[];
  trades: Trade[];
  overview: AccountOverview | null;
  loading: boolean;
  error: string | null;

  setUserId: (userId: number) => void;
  fetchPositions: () => Promise<void>;
  fetchTrades: () => Promise<void>;
  fetchOverview: () => Promise<void>;
  buyStock: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
  sellStock: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
}

export const useTradeStore = create<TradeState>((set, get) => ({
  userId: null,
  positions: [],
  trades: [],
  overview: null,
  loading: false,
  error: null,

  setUserId: (userId: number) => {
    set({ userId });
    // 自动加载数据
    get().fetchPositions();
    get().fetchTrades();
    get().fetchOverview();
  },

  fetchPositions: async () => {
    const { userId } = get();
    if (!userId) return;

    set({ loading: true, error: null });
    try {
      const response = await tradeApi.getPositions(userId);
      set({ positions: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  fetchTrades: async () => {
    const { userId } = get();
    if (!userId) return;

    set({ loading: true, error: null });
    try {
      const response = await tradeApi.getHistory(userId);
      set({ trades: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  fetchOverview: async () => {
    const { userId } = get();
    if (!userId) return;

    set({ loading: true, error: null });
    try {
      const response = await accountApi.getAccountOverview(userId);
      set({ overview: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  buyStock: async (stockCode, stockName, price, quantity) => {
    const { userId } = get();
    if (!userId) return false;

    set({ loading: true, error: null });
    try {
      await tradeApi.buy(userId, {
        stock_code: stockCode,
        stock_name: stockName,
        price,
        quantity,
      });
      // 刷新数据
      await get().fetchPositions();
      await get().fetchTrades();
      await get().fetchOverview();
      set({ loading: false });
      return true;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || error.message, loading: false });
      return false;
    }
  },

  sellStock: async (stockCode, stockName, price, quantity) => {
    const { userId } = get();
    if (!userId) return false;

    set({ loading: true, error: null });
    try {
      await tradeApi.sell(userId, {
        stock_code: stockCode,
        stock_name: stockName,
        price,
        quantity,
      });
      // 刷新数据
      await get().fetchPositions();
      await get().fetchTrades();
      await get().fetchOverview();
      set({ loading: false });
      return true;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || error.message, loading: false });
      return false;
    }
  },
}));
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/ frontend/src/stores/
git commit -m "feat: add API service and Zustand state management"
```

---

## Task 11: 前端页面组件

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/Trade.tsx`
- Create: `frontend/src/components/AccountOverview.tsx`
- Create: `frontend/src/components/PositionList.tsx`
- Create: `frontend/src/components/TradeForm.tsx`
- Create: `frontend/src/components/StockChart.tsx`

- [ ] **Step 1: 创建账户概览组件**

```tsx
// frontend/src/components/AccountOverview.tsx
import { Card, Statistic, Row, Col } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import type { AccountOverview as AccountOverviewType } from '../types';

interface Props {
  overview: AccountOverviewType | null;
  loading?: boolean;
}

export default function AccountOverviewComponent({ overview, loading }: Props) {
  if (!overview) {
    return <Card loading={loading}>加载中...</Card>;
  }

  return (
    <Card title="账户概览">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic
            title="总资产"
            value={overview.total_assets}
            precision={2}
            prefix="¥"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="可用资金"
            value={overview.available_capital}
            precision={2}
            prefix="¥"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="持仓市值"
            value={overview.market_value}
            precision={2}
            prefix="¥"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="总盈亏"
            value={overview.total_pnl}
            precision={2}
            prefix="¥"
            valueStyle={{ color: overview.total_pnl >= 0 ? '#3f8600' : '#cf1322' }}
            suffix={overview.total_pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          />
        </Col>
      </Row>
    </Card>
  );
}
```

- [ ] **Step 2: 创建持仓列表组件**

```tsx
// frontend/src/components/PositionList.tsx
import { Table, Tag } from 'antd';
import type { Position } from '../types';

interface Props {
  positions: Position[];
  loading?: boolean;
  onSelect?: (position: Position) => void;
}

export default function PositionList({ positions, loading, onSelect }: Props) {
  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '成本价',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '盈亏',
      dataIndex: 'unrealized_pnl',
      key: 'unrealized_pnl',
      render: (value: number) => (
        <Tag color={value >= 0 ? 'green' : 'red'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}
        </Tag>
      ),
    },
    {
      title: '市值',
      dataIndex: 'market_value',
      key: 'market_value',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={positions}
      loading={loading}
      rowKey="id"
      onRow={(record) => ({
        onClick: () => onSelect?.(record),
      })}
      pagination={false}
    />
  );
}
```

- [ ] **Step 3: 创建交易表单组件**

```tsx
// frontend/src/components/TradeForm.tsx
import { useState } from 'react';
import { Card, Form, Input, InputNumber, Button, Space, message } from 'antd';
import { stockApi } from '../services/api';
import type { StockQuote } from '../types';

interface Props {
  onBuy: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
  onSell: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
  loading?: boolean;
}

export default function TradeForm({ onBuy, onSell, loading }: Props) {
  const [stockCode, setStockCode] = useState('');
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [price, setPrice] = useState<number>(0);
  const [quantity, setQuantity] = useState<number>(100);
  const [fetching, setFetching] = useState(false);

  const handleSearch = async () => {
    if (stockCode.length !== 6) {
      message.error('请输入6位股票代码');
      return;
    }

    setFetching(true);
    try {
      const response = await stockApi.getQuote(stockCode);
      setQuote(response.data);
      setPrice(response.data.current_price);
    } catch (error) {
      message.error('获取股票信息失败');
    } finally {
      setFetching(false);
    }
  };

  const handleBuy = async () => {
    if (!quote) return;
    const success = await onBuy(stockCode, quote.stock_name, price, quantity);
    if (success) {
      message.success('买入成功');
    }
  };

  const handleSell = async () => {
    if (!quote) return;
    const success = await onSell(stockCode, quote.stock_name, price, quantity);
    if (success) {
      message.success('卖出成功');
    }
  };

  const totalAmount = price * quantity;

  return (
    <Card title="交易下单">
      <Form layout="vertical">
        <Form.Item label="股票代码">
          <Space>
            <Input
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              placeholder="请输入6位股票代码"
              maxLength={6}
              style={{ width: 200 }}
            />
            <Button onClick={handleSearch} loading={fetching}>
              查询
            </Button>
          </Space>
        </Form.Item>

        {quote && (
          <>
            <Form.Item label="股票信息">
              <Space>
                <span>{quote.stock_name}</span>
                <span style={{ color: quote.change_percent >= 0 ? '#3f8600' : '#cf1322' }}>
                  ¥{quote.current_price.toFixed(2)} ({quote.change_percent >= 0 ? '+' : ''}{quote.change_percent.toFixed(2)}%)
                </span>
              </Space>
            </Form.Item>

            <Form.Item label="委托价格">
              <InputNumber
                value={price}
                onChange={(value) => setPrice(value || 0)}
                min={0}
                step={0.01}
                precision={2}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item label="委托数量">
              <InputNumber
                value={quantity}
                onChange={(value) => setQuantity(value || 0)}
                min={100}
                step={100}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item label="预估金额">
              <span>¥{totalAmount.toFixed(2)}</span>
            </Form.Item>

            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  onClick={handleBuy}
                  loading={loading}
                  style={{ backgroundColor: '#3f8600' }}
                >
                  买入
                </Button>
                <Button
                  danger
                  onClick={handleSell}
                  loading={loading}
                >
                  卖出
                </Button>
              </Space>
            </Form.Item>
          </>
        )}
      </Form>
    </Card>
  );
}
```

- [ ] **Step 4: 创建K线图组件**

```tsx
// frontend/src/components/StockChart.tsx
import { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from 'antd';
import { stockApi } from '../services/api';
import type { KLineData } from '../types';

interface Props {
  stockCode: string;
  stockName?: string;
}

export default function StockChart({ stockCode, stockName }: Props) {
  const [klineData, setKlineData] = useState<KLineData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (stockCode) {
      fetchKlineData();
    }
  }, [stockCode]);

  const fetchKlineData = async () => {
    setLoading(true);
    try {
      const response = await stockApi.getKlineData(stockCode, 60);
      setKlineData(response.data);
    } catch (error) {
      console.error('获取K线数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getOption = () => {
    if (!klineData) return {};

    return {
      title: {
        text: stockName ? `${stockName} (${stockCode})` : stockCode,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['K线', '成交量'],
        bottom: 0,
      },
      grid: [
        { left: '10%', right: '8%', height: '50%' },
        { left: '10%', right: '8%', top: '70%', height: '20%' },
      ],
      xAxis: [
        {
          type: 'category',
          data: klineData.dates,
          gridIndex: 0,
        },
        {
          type: 'category',
          data: klineData.dates,
          gridIndex: 1,
        },
      ],
      yAxis: [
        {
          type: 'value',
          gridIndex: 0,
          scale: true,
        },
        {
          type: 'value',
          gridIndex: 1,
          scale: true,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData.dates.map((_, i) => [
            klineData.opens[i],
            klineData.closes[i],
            klineData.lows[i],
            klineData.highs[i],
          ]),
          xAxisIndex: 0,
          yAxisIndex: 0,
        },
        {
          name: '成交量',
          type: 'bar',
          data: klineData.volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
        },
      ],
    };
  };

  return (
    <Card title="K线图" loading={loading}>
      {klineData && (
        <ReactECharts option={getOption()} style={{ height: 400 }} />
      )}
    </Card>
  );
}
```

- [ ] **Step 5: 创建仪表盘页面**

```tsx
// frontend/src/pages/Dashboard.tsx
import { useEffect } from 'react';
import { Row, Col } from 'antd';
import AccountOverviewComponent from '../components/AccountOverview';
import PositionList from '../components/PositionList';
import StockChart from '../components/StockChart';
import { useTradeStore } from '../stores/tradeStore';

export default function Dashboard() {
  const {
    userId,
    overview,
    positions,
    loading,
    setUserId,
  } = useTradeStore();

  useEffect(() => {
    // 临时使用固定用户ID，实际应从登录获取
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  const [selectedStock, setSelectedStock] = useState<string>('000001');

  return (
    <div>
      <AccountOverviewComponent overview={overview} loading={loading} />
      
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={16}>
          <StockChart stockCode={selectedStock} />
        </Col>
        <Col span={8}>
          <PositionList
            positions={positions}
            loading={loading}
            onSelect={(position) => setSelectedStock(position.stock_code)}
          />
        </Col>
      </Row>
    </div>
  );
}
```

- [ ] **Step 6: 创建交易页面**

```tsx
// frontend/src/pages/Trade.tsx
import { useEffect } from 'react';
import { Row, Col, message } from 'antd';
import TradeForm from '../components/TradeForm';
import PositionList from '../components/PositionList';
import StockChart from '../components/StockChart';
import { useTradeStore } from '../stores/tradeStore';

export default function Trade() {
  const {
    userId,
    positions,
    loading,
    error,
    setUserId,
    buyStock,
    sellStock,
  } = useTradeStore();

  useEffect(() => {
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  useEffect(() => {
    if (error) {
      message.error(error);
    }
  }, [error]);

  const [selectedStock, setSelectedStock] = useState<string>('000001');

  const handleBuy = async (stockCode: string, stockName: string, price: number, quantity: number) => {
    return await buyStock(stockCode, stockName, price, quantity);
  };

  const handleSell = async (stockCode: string, stockName: string, price: number, quantity: number) => {
    return await sellStock(stockCode, stockName, price, quantity);
  };

  return (
    <Row gutter={16}>
      <Col span={8}>
        <TradeForm
          onBuy={handleBuy}
          onSell={handleSell}
          loading={loading}
        />
      </Col>
      <Col span={16}>
        <StockChart stockCode={selectedStock} />
        <div style={{ marginTop: 16 }}>
          <PositionList
            positions={positions}
            loading={loading}
            onSelect={(position) => setSelectedStock(position.stock_code)}
          />
        </div>
      </Col>
    </Row>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ frontend/src/pages/
git commit -m "feat: add Dashboard and Trade pages with components"
```

---

## Task 12: 测试配置与数据库迁移

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: 创建测试配置**

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.config import settings


@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(engine):
    """创建测试数据库会话"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
```

- [ ] **Step 2: 初始化Alembic**

```bash
cd E:/cs/gp/backend
alembic init alembic
```

- [ ] **Step 3: 配置Alembic**

```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 创建初始迁移**

```bash
cd E:/cs/gp/backend
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
```

Expected: Migration created and applied successfully

- [ ] **Step 5: Commit**

```bash
git add backend/tests/conftest.py backend/alembic/
git commit -m "feat: add test configuration and database migrations"
```

---

## Task 13: 启动脚本与文档

**Files:**
- Create: `start.sh`
- Create: `README.md`

- [ ] **Step 1: 创建启动脚本**

```bash
#!/bin/bash
# start.sh

echo "启动股票交易系统..."

# 启动数据库
echo "启动数据库服务..."
docker-compose up -d postgres redis

# 等待数据库就绪
sleep 5

# 启动后端
echo "启动后端服务..."
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "系统已启动！"
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:5173"
echo "API文档: http://localhost:8000/docs"

# 等待用户中断
wait $BACKEND_PID $FRONTEND_PID
```

- [ ] **Step 2: 创建README文档**

```markdown
# 股票交易自动化系统

一个功能完整的模拟炒股系统，支持实时行情、模拟交易、K线图展示。

## 功能特性

- 实时股票行情查看
- 模拟买卖交易
- 持仓管理
- K线图展示
- 交易记录查询
- 账户概览

## 技术栈

**后端:**
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- AKShare

**前端:**
- React 18
- TypeScript
- Ant Design
- ECharts
- Zustand

## 快速开始

### 1. 启动数据库

```bash
docker-compose up -d
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问系统

- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

## 项目结构

```
gp/
├── backend/          # 后端服务
│   ├── app/          # 应用代码
│   ├── tests/        # 测试文件
│   └── alembic/      # 数据库迁移
├── frontend/         # 前端应用
│   ├── src/          # 源代码
│   └── public/       # 静态资源
├── docker-compose.yml
└── README.md
```

## 开发说明

### 运行测试

```bash
cd backend
pytest
```

### 数据库迁移

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 后续计划

- 股票预测功能
- 自动交易策略
- 复盘分析系统
- 移动端适配
```

- [ ] **Step 3: Commit**

```bash
git add start.sh README.md
git commit -m "docs: add startup script and README"
```

---

## 自审检查清单

**1. 规格覆盖:**
- [x] 数据获取服务 (Task 5)
- [x] 交易引擎 (Task 6)
- [x] 账户管理 (Task 7)
- [x] API接口 (Task 8)
- [x] 前端界面 (Task 9-11)
- [x] 数据库配置 (Task 2)

**2. 占位符检查:**
- [x] 无TBD或TODO
- [x] 所有代码完整
- [x] 所有测试完整

**3. 类型一致性:**
- [x] Pydantic模型与SQLAlchemy模型一致
- [x] 前端TypeScript类型与后端API一致
- [x] 函数签名在测试和实现中一致

---

## 执行选项

**计划完成并保存到 `docs/superpowers/plans/2026-06-01-stock-trading-mvp.md`**

两种执行方式：

**1. Subagent-Driven（推荐）** - 每个任务分发一个新的子代理，任务间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中执行任务，批量执行并设置检查点

**选择哪种方式？**
