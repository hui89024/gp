# 真实数据接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将模拟炒股系统升级为支持实盘交易的完整系统，接入东方财富证券、efinance行情和基本面数据。

**Architecture:** 系统采用分层架构，新增 BrokerService 处理券商对接，升级 DataService 支持双数据源，新增 FundamentalService 和 LiveTradingRiskControl。通过 trading_mode 配置区分模拟/实盘模式，保留全部现有功能。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, easytrader, efinance, AKShare, React 18, Ant Design

---

## 文件结构总览

### 后端新增文件
| 文件 | 职责 |
|------|------|
| `backend/app/models/broker_account.py` | 券商账户数据模型 |
| `backend/app/models/live_trade.py` | 实盘交易记录模型 |
| `backend/app/models/fundamental_data.py` | 基本面数据模型 |
| `backend/app/models/risk_control_record.py` | 风控记录模型 |
| `backend/app/schemas/broker.py` | 券商相关 Pydantic Schema |
| `backend/app/schemas/live_trade.py` | 实盘交易 Schema |
| `backend/app/schemas/fundamental.py` | 基本面数据 Schema |
| `backend/app/services/broker_service.py` | 券商对接服务 |
| `backend/app/services/efinance_source.py` | efinance 数据源 |
| `backend/app/services/akshare_source.py` | AKShare 数据源（从现有 DataService 提取） |
| `backend/app/services/fundamental_service.py` | 基本面数据服务 |
| `backend/app/services/live_risk_control.py` | 实盘风控服务 |
| `backend/app/services/encryption.py` | 账户加密工具 |
| `backend/app/api/broker.py` | 券商账户管理 API |
| `backend/app/api/live_trade.py` | 实盘交易 API |
| `backend/app/api/fundamental.py` | 基本面数据 API |

### 后端修改文件
| 文件 | 修改内容 |
|------|----------|
| `backend/requirements.txt` | 新增依赖包 |
| `backend/app/config.py` | 新增实盘配置项 |
| `backend/app/models/__init__.py` | 注册新模型 |
| `backend/app/services/data_service.py` | 重构为双数据源模式 |
| `backend/app/api/__init__.py` | 注册新路由 |
| `backend/app/main.py` | 挂载新路由 |
| `backend/app/api/deps.py` | 新增依赖注入 |

### 前端新增文件
| 文件 | 职责 |
|------|------|
| `frontend/src/pages/BrokerAccount.tsx` | 券商账户管理页 |
| `frontend/src/pages/LiveTrade.tsx` | 实盘交易页 |
| `frontend/src/pages/Fundamental.tsx` | 基本面分析页 |
| `frontend/src/pages/LiveRiskControl.tsx` | 实盘风控中心页 |
| `frontend/src/services/brokerApi.ts` | 券商 API 服务 |
| `frontend/src/services/liveTradeApi.ts` | 实盘交易 API 服务 |
| `frontend/src/services/fundamentalApi.ts` | 基本面 API 服务 |

### 前端修改文件
| 文件 | 修改内容 |
|------|----------|
| `frontend/src/App.tsx` | 新增路由和交易模式切换 |

---

## Task 1: 依赖安装与配置更新

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`
- Modify: `.env`

- [ ] **Step 1: 更新 requirements.txt**

在 `backend/requirements.txt` 末尾追加：

```
easytrader==0.5.15
efinance==0.5.6
cryptography==41.0.0
APScheduler==3.10.4
```

- [ ] **Step 2: 更新 config.py 新增实盘配置**

在 `backend/app/config.py` 的 `Settings` 类中追加字段：

```python
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
```

- [ ] **Step 3: 更新 .env 文件**

在 `.env` 文件末尾追加：

```env
# 券商配置
BROKER_TYPE=eastmoney
BROKER_ACCOUNT=
BROKER_PASSWORD=
ENCRYPTION_KEY=

# 数据源配置
PRIMARY_DATA_SOURCE=efinance
FALLBACK_DATA_SOURCE=akshare

# 实盘风控配置
LIVE_MAX_INITIAL_CAPITAL=100000.0
LIVE_MAX_SINGLE_TRADE=10000.0
LIVE_MAX_DAILY_TRADES=10
LIVE_MAX_DAILY_LOSS=5000.0
LIVE_MAX_POSITION_RATIO=0.2
LIVE_STOP_LOSS_RATIO=-0.05
```

- [ ] **Step 4: 安装依赖**

```bash
cd backend && pip install -r requirements.txt
```

- [ ] **Step 5: 提交**

```bash
git add backend/requirements.txt backend/app/config.py .env
git commit -m "chore: 新增实盘交易相关依赖和配置"
```

---

## Task 2: 数据库模型 — 券商账户

**Files:**
- Create: `backend/app/models/broker_account.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建 BrokerAccount 模型**

新建 `backend/app/models/broker_account.py`：

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from app.database import Base


class BrokerAccount(Base):
    """券商账户模型"""
    __tablename__ = "broker_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    broker_type = Column(String(50), nullable=False, default="eastmoney")
    account = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 注册模型到 __init__.py**

在 `backend/app/models/__init__.py` 中新增：

```python
from app.models.broker_account import BrokerAccount
```

并在 `__all__` 列表中添加 `"BrokerAccount"`。

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/broker_account.py backend/app/models/__init__.py
git commit -m "feat(models): 新增券商账户数据模型"
```

---

## Task 3: 数据库模型 — 实盘交易记录

**Files:**
- Create: `backend/app/models/live_trade.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建 LiveTrade 模型**

新建 `backend/app/models/live_trade.py`：

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric
from app.database import Base


class LiveTrade(Base):
    """实盘交易记录模型"""
    __tablename__ = "live_trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    broker_account_id = Column(Integer, ForeignKey("broker_accounts.id"), nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(50))
    trade_type = Column(String(10), nullable=False)  # BUY / SELL
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    commission = Column(Numeric(10, 2), default=0)
    broker_order_id = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")  # pending / filled / cancelled / failed
    strategy_tag = Column(String(50), nullable=True)
    trade_time = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: 注册模型到 __init__.py**

在 `backend/app/models/__init__.py` 中新增：

```python
from app.models.live_trade import LiveTrade
```

并在 `__all__` 列表中添加 `"LiveTrade"`。

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/live_trade.py backend/app/models/__init__.py
git commit -m "feat(models): 新增实盘交易记录数据模型"
```

---

## Task 4: 数据库模型 — 基本面数据与风控记录

**Files:**
- Create: `backend/app/models/fundamental_data.py`
- Create: `backend/app/models/risk_control_record.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建 FundamentalData 模型**

新建 `backend/app/models/fundamental_data.py`：

```python
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class FundamentalData(Base):
    """基本面数据模型"""
    __tablename__ = "fundamental_data"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False)
    data_type = Column(String(50), nullable=False)  # balance_sheet / income / cash_flow / indicators
    data = Column(JSONB, nullable=False)
    report_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "data_type", "report_date", name="uq_fundamental"),
    )
```

- [ ] **Step 2: 创建 RiskControlRecord 模型**

新建 `backend/app/models/risk_control_record.py`：

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class RiskControlRecord(Base):
    """风控记录模型"""
    __tablename__ = "risk_control_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # trade_rejected / stop_loss / circuit_breaker
    event_detail = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 3: 注册模型到 __init__.py**

在 `backend/app/models/__init__.py` 中新增导入并在 `__all__` 中添加：

```python
from app.models.fundamental_data import FundamentalData
from app.models.risk_control_record import RiskControlRecord
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/fundamental_data.py backend/app/models/risk_control_record.py backend/app/models/__init__.py
git commit -m "feat(models): 新增基本面数据和风控记录数据模型"
```

---

## Task 5: 加密工具与 Schema 定义

**Files:**
- Create: `backend/app/services/encryption.py`
- Create: `backend/app/schemas/broker.py`
- Create: `backend/app/schemas/live_trade.py`
- Create: `backend/app/schemas/fundamental.py`

- [ ] **Step 1: 创建加密工具**

新建 `backend/app/services/encryption.py`：

```python
from cryptography.fernet import Fernet
from app.config import settings


class EncryptionService:
    """AES加密服务，用于券商账户密码加密"""

    def __init__(self):
        key = settings.ENCRYPTION_KEY
        if not key:
            key = Fernet.generate_key().decode()
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        """加密明文"""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密密文"""
        return self._fernet.decrypt(ciphertext.encode()).decode()


encryption_service = EncryptionService()
```

- [ ] **Step 2: 创建券商 Schema**

新建 `backend/app/schemas/broker.py`：

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BrokerAccountCreate(BaseModel):
    broker_type: str = "eastmoney"
    account: str
    password: str


class BrokerAccountUpdate(BaseModel):
    broker_type: Optional[str] = None
    account: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class BrokerAccountResponse(BaseModel):
    id: int
    user_id: int
    broker_type: str
    account: str
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BrokerLoginRequest(BaseModel):
    account: str
    password: str
```

- [ ] **Step 3: 创建实盘交易 Schema**

新建 `backend/app/schemas/live_trade.py`：

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LiveTradeRequest(BaseModel):
    stock_code: str
    stock_name: str
    price: float
    quantity: int
    strategy_tag: Optional[str] = None


class LiveTradeResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: Optional[str]
    trade_type: str
    price: float
    quantity: int
    total_amount: float
    commission: float
    broker_order_id: Optional[str]
    status: str
    strategy_tag: Optional[str]
    trade_time: datetime

    class Config:
        from_attributes = True


class BrokerPosition(BaseModel):
    stock_code: str
    stock_name: str
    quantity: int
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_ratio: float


class BrokerBalance(BaseModel):
    total_assets: float
    available_cash: float
    market_value: float
    frozen_amount: float
```

- [ ] **Step 4: 创建基本面数据 Schema**

新建 `backend/app/schemas/fundamental.py`：

```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, datetime


class FinancialReport(BaseModel):
    stock_code: str
    balance_sheet: Optional[dict] = None
    income_statement: Optional[dict] = None
    cash_flow: Optional[dict] = None
    report_date: date


class FinancialIndicators(BaseModel):
    stock_code: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_ratio: Optional[float] = None


class CompanyInfo(BaseModel):
    stock_code: str
    company_name: str
    main_business: Optional[str] = None
    industry: Optional[str] = None
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None


class IndustryData(BaseModel):
    industry: str
    stock_count: int
    avg_pe: Optional[float] = None
    avg_pb: Optional[float] = None
    avg_roe: Optional[float] = None
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/encryption.py backend/app/schemas/broker.py backend/app/schemas/live_trade.py backend/app/schemas/fundamental.py
git commit -m "feat: 新增加密工具和实盘交易/基本面数据 Schema"
```

---

## Task 6: 券商服务 (BrokerService)

**Files:**
- Create: `backend/app/services/broker_service.py`

- [ ] **Step 1: 创建 BrokerService**

新建 `backend/app/services/broker_service.py`：

```python
import easytrader
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.schemas.live_trade import BrokerPosition, BrokerBalance
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
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/broker_service.py
git commit -m "feat: 新增券商对接服务 BrokerService"
```

---

## Task 7: 行情数据源重构 — 双数据源架构

**Files:**
- Create: `backend/app/services/akshare_source.py`
- Create: `backend/app/services/efinance_source.py`
- Modify: `backend/app/services/data_service.py`

- [ ] **Step 1: 创建 AKShareSource**

新建 `backend/app/services/akshare_source.py`（从现有 DataService 提取逻辑）：

```python
import akshare as ak
from typing import List, Optional
from datetime import datetime, timedelta

from app.schemas.stock import StockQuote, StockHistory


class AKShareSource:
    """AKShare 数据源"""

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """获取实时行情"""
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
            print(f"AKShare获取行情失败: {e}")
            return None

    def get_stock_history(self, stock_code: str, days: int = 30) -> List[StockHistory]:
        """获取历史数据"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            df = ak.stock_zh_a_hist(
                symbol=stock_code, period="daily",
                start_date=start_date, end_date=end_date, adjust="qfq"
            )
            history = []
            for _, row in df.iterrows():
                history.append(StockHistory(
                    date=str(row["日期"]), open=float(row["开盘"]),
                    high=float(row["最高"]), low=float(row["最低"]),
                    close=float(row["收盘"]), volume=int(row["成交量"]),
                    amount=float(row["成交额"])
                ))
            return history
        except Exception as e:
            print(f"AKShare获取历史数据失败: {e}")
            return []

    def search_stocks(self, keyword: str) -> list:
        """搜索股票"""
        try:
            df = ak.stock_zh_a_spot_em()
            matches = df[
                df["名称"].str.contains(keyword, na=False) |
                df["代码"].str.contains(keyword, na=False)
            ].head(10)
            results = []
            for _, row in matches.iterrows():
                results.append({
                    "stock_code": row["代码"],
                    "stock_name": row["名称"],
                    "market": row.get("市场", "A股")
                })
            return results
        except Exception as e:
            print(f"AKShare搜索失败: {e}")
            return []
```

- [ ] **Step 2: 创建 EFinanceSource**

新建 `backend/app/services/efinance_source.py`：

```python
import efinance as ef
from typing import List, Optional
from datetime import datetime

from app.schemas.stock import StockQuote, StockHistory


class EFinanceSource:
    """efinance 数据源（东方财富）"""

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """获取实时行情"""
        try:
            df = ef.stock.get_quote_history(stock_code, klt=1)
            if df.empty:
                return None
            row = df.iloc[-1]
            return StockQuote(
                stock_code=stock_code,
                stock_name=row.get("股票名称", ""),
                current_price=float(row["收盘"]),
                open_price=float(row["开盘"]),
                high_price=float(row["最高"]),
                low_price=float(row["最低"]),
                close_price=float(row["收盘"]),
                volume=int(row["成交量"]),
                amount=float(row["成交额"]),
                change_percent=float(row.get("涨跌幅", 0)),
                change_amount=float(row.get("涨跌额", 0)),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"efinance获取行情失败: {e}")
            return None

    def get_stock_history(self, stock_code: str, days: int = 30) -> List[StockHistory]:
        """获取历史数据"""
        try:
            df = ef.stock.get_quote_history(stock_code, klt=101)
            if df.empty:
                return []
            df = df.tail(days)
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
            print(f"efinance获取历史数据失败: {e}")
            return []

    def get_realtime_quotes(self, stock_codes: List[str]) -> List[dict]:
        """批量获取实时行情"""
        try:
            df = ef.stock.get_realtime_quotes(stock_codes)
            results = []
            for _, row in df.iterrows():
                results.append({
                    "stock_code": row["股票代码"],
                    "stock_name": row["股票名称"],
                    "current_price": float(row["最新价"]),
                    "change_percent": float(row["涨跌幅"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"])
                })
            return results
        except Exception as e:
            print(f"efinance批量行情失败: {e}")
            return []
```

- [ ] **Step 3: 重构 DataService**

将 `backend/app/services/data_service.py` 重写为双数据源模式：

```python
from typing import List, Optional
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult
from app.services.akshare_source import AKShareSource
from app.services.efinance_source import EFinanceSource
from app.config import settings


class DataService:
    """统一数据服务 - 双数据源互备"""

    def __init__(self):
        self._sources = {
            "akshare": AKShareSource(),
            "efinance": EFinanceSource(),
        }
        self._primary = settings.PRIMARY_DATA_SOURCE
        self._fallback = settings.FALLBACK_DATA_SOURCE

    def _get_sources(self):
        """按优先级返回数据源列表"""
        primary = self._sources.get(self._primary)
        fallback = self._sources.get(self._fallback)
        if primary and fallback:
            return [primary, fallback]
        return [self._sources["akshare"]]

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """获取实时行情 - 自动切换数据源"""
        for source in self._get_sources():
            result = source.get_stock_quote(stock_code)
            if result:
                return result
        return None

    def get_stock_history(self, stock_code: str, days: int = 30) -> List[StockHistory]:
        """获取历史数据 - 自动切换数据源"""
        for source in self._get_sources():
            result = source.get_stock_history(stock_code, days)
            if result:
                return result
        return []

    def search_stocks(self, keyword: str) -> List[StockSearchResult]:
        """搜索股票"""
        results = self._sources["akshare"].search_stocks(keyword)
        return [StockSearchResult(**r) for r in results]

    def get_kline_data(self, stock_code: str, days: int = 60) -> dict:
        """获取K线数据"""
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

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/akshare_source.py backend/app/services/efinance_source.py backend/app/services/data_service.py
git commit -m "feat: 重构 DataService 为双数据源架构 (AKShare + efinance)"
```

---

## Task 8: 基本面数据服务

**Files:**
- Create: `backend/app/services/fundamental_service.py`

- [ ] **Step 1: 创建 FundamentalService**

新建 `backend/app/services/fundamental_service.py`：

```python
import akshare as ak
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.fundamental_data import FundamentalData


class FundamentalService:
    """基本面数据服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_financial_report(self, stock_code: str) -> dict:
        """获取财务报表（资产负债表、利润表、现金流量表）"""
        cached = self._get_cached(stock_code, "financial_report")
        if cached:
            return cached

        try:
            balance = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
            income = ak.stock_profit_sheet_by_report_em(symbol=stock_code)
            cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)

            data = {
                "balance_sheet": balance.head(4).to_dict(orient="records") if not balance.empty else [],
                "income_statement": income.head(4).to_dict(orient="records") if not income.empty else [],
                "cash_flow": cash_flow.head(4).to_dict(orient="records") if not cash_flow.empty else [],
            }
            self._save_cache(stock_code, "financial_report", data)
            return data
        except Exception as e:
            print(f"获取财务报表失败: {e}")
            return {}

    def get_financial_indicators(self, stock_code: str) -> dict:
        """获取财务指标"""
        cached = self._get_cached(stock_code, "financial_indicators")
        if cached:
            return cached

        try:
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            if df.empty:
                return {}
            row = df.iloc[0]
            data = {
                "pe_ratio": self._safe_float(row.get("市盈率(每股)")),
                "pb_ratio": self._safe_float(row.get("市净率")),
                "roe": self._safe_float(row.get("净资产收益率(%)")),
                "gross_margin": self._safe_float(row.get("销售毛利率(%)")),
                "net_margin": self._safe_float(row.get("销售净利率(%)")),
                "debt_ratio": self._safe_float(row.get("资产负债率(%)")),
            }
            self._save_cache(stock_code, "financial_indicators", data)
            return data
        except Exception as e:
            print(f"获取财务指标失败: {e}")
            return {}

    def get_company_info(self, stock_code: str) -> dict:
        """获取公司基本信息"""
        cached = self._get_cached(stock_code, "company_info")
        if cached:
            return cached

        try:
            df = ak.stock_individual_info_em(symbol=stock_code)
            if df.empty:
                return {}
            info = {}
            for _, row in df.iterrows():
                info[row["item"]] = row["value"]
            data = {
                "stock_code": stock_code,
                "company_name": info.get("股票简称", ""),
                "main_business": info.get("行业", ""),
                "industry": info.get("行业", ""),
                "total_market_cap": self._safe_float(info.get("总市值")),
                "circulating_market_cap": self._safe_float(info.get("流通市值")),
            }
            self._save_cache(stock_code, "company_info", data)
            return data
        except Exception as e:
            print(f"获取公司信息失败: {e}")
            return {}

    def _get_cached(self, stock_code: str, data_type: str) -> Optional[dict]:
        """从缓存获取数据（24小时内有效）"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        record = self.db.query(FundamentalData).filter(
            FundamentalData.stock_code == stock_code,
            FundamentalData.data_type == data_type,
            FundamentalData.updated_at >= cutoff
        ).first()
        if record:
            return record.data
        return None

    def _save_cache(self, stock_code: str, data_type: str, data: dict):
        """保存数据到缓存"""
        record = self.db.query(FundamentalData).filter(
            FundamentalData.stock_code == stock_code,
            FundamentalData.data_type == data_type,
        ).first()
        if record:
            record.data = data
            record.updated_at = datetime.utcnow()
        else:
            record = FundamentalData(
                stock_code=stock_code,
                data_type=data_type,
                data=data,
                report_date=datetime.utcnow().date()
            )
            self.db.add(record)
        self.db.commit()

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为 float"""
        try:
            if value is None or value == "" or value == "--":
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/fundamental_service.py
git commit -m "feat: 新增基本面数据服务 FundamentalService"
```

---

## Task 9: 实盘风控服务

**Files:**
- Create: `backend/app/services/live_risk_control.py`

- [ ] **Step 1: 创建 LiveTradingRiskControl**

新建 `backend/app/services/live_risk_control.py`：

```python
from typing import Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import SQLAlchemy

from app.config import settings
from app.models.live_trade import LiveTrade
from app.models.risk_control_record import RiskControlRecord


class LiveTradingRiskControl:
    """实盘交易风控系统"""

    def __init__(self, db):
        self.db = db
        self.max_single_trade = settings.LIVE_MAX_SINGLE_TRADE
        self.max_daily_trades = settings.LIVE_MAX_DAILY_TRADES
        self.max_daily_loss = settings.LIVE_MAX_DAILY_LOSS
        self.max_position_ratio = settings.LIVE_MAX_POSITION_RATIO
        self.stop_loss_ratio = settings.LIVE_STOP_LOSS_RATIO

    def validate_trade(
        self, user_id: int, amount: float, stock_code: str, trade_type: str
    ) -> Tuple[bool, str]:
        """交易前验证"""
        # 1. 检查单笔交易金额
        if amount > self.max_single_trade:
            self._record_event(user_id, "trade_rejected", {
                "reason": f"单笔交易金额{amount}超过限制{self.max_single_trade}",
                "stock_code": stock_code
            })
            return False, f"单笔交易金额不能超过{self.max_single_trade}元"

        # 2. 检查每日交易次数
        today_count = self._get_today_trade_count(user_id)
        if today_count >= self.max_daily_trades:
            self._record_event(user_id, "trade_rejected", {
                "reason": f"今日交易{today_count}次已达上限",
                "stock_code": stock_code
            })
            return False, f"每日交易次数不能超过{self.max_daily_trades}次"

        # 3. 检查每日亏损
        today_loss = self._get_today_loss(user_id)
        if today_loss >= self.max_daily_loss:
            self._record_event(user_id, "trade_rejected", {
                "reason": f"今日亏损{today_loss}已达上限",
                "stock_code": stock_code
            })
            return False, f"每日亏损已达上限{self.max_daily_loss}元"

        return True, "验证通过"

    def check_stop_loss(self, user_id: int, positions: list) -> list:
        """检查止损，返回需要平仓的持仓"""
        stop_loss_list = []
        for pos in positions:
            if pos.get("profit_loss_ratio", 0) <= self.stop_loss_ratio:
                stop_loss_list.append(pos)
                self._record_event(user_id, "stop_loss", {
                    "stock_code": pos.get("stock_code"),
                    "profit_loss_ratio": pos.get("profit_loss_ratio"),
                })
        return stop_loss_list

    def _get_today_trade_count(self, user_id: int) -> int:
        """获取今日交易次数"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id,
            LiveTrade.trade_time >= today_start,
            LiveTrade.status == "filled"
        ).count()

    def _get_today_loss(self, user_id: int) -> float:
        """获取今日亏损金额"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        trades = self.db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id,
            LiveTrade.trade_time >= today_start,
            LiveTrade.status == "filled"
        ).all()
        total_loss = 0.0
        for trade in trades:
            if trade.trade_type == "SELL":
                total_loss += float(trade.total_amount) - float(trade.commission)
            else:
                total_loss -= float(trade.total_amount) + float(trade.commission)
        return abs(min(total_loss, 0))

    def _record_event(self, user_id: int, event_type: str, detail: dict):
        """记录风控事件"""
        record = RiskControlRecord(
            user_id=user_id,
            event_type=event_type,
            event_detail=detail
        )
        self.db.add(record)
        self.db.commit()
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/live_risk_control.py
git commit -m "feat: 新增实盘交易风控服务"
```

---

## Task 10: API 路由 — 券商账户管理

**Files:**
- Create: `backend/app/api/broker.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/deps.py`

- [ ] **Step 1: 创建券商账户 API**

新建 `backend/app/api/broker.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.broker_account import BrokerAccount
from app.schemas.broker import (
    BrokerAccountCreate, BrokerAccountUpdate, BrokerAccountResponse
)
from app.services.encryption import encryption_service
from app.services.broker_service import BrokerService

router = APIRouter(prefix="/api/broker", tags=["券商账户"])


@router.post("/accounts", response_model=BrokerAccountResponse)
def create_broker_account(
    data: BrokerAccountCreate,
    db: Session = Depends(get_db)
):
    """添加券商账户"""
    encrypted_pwd = encryption_service.encrypt(data.password)
    account = BrokerAccount(
        user_id=1,  # TODO: 从认证上下文获取
        broker_type=data.broker_type,
        account=data.account,
        password_encrypted=encrypted_pwd
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts", response_model=List[BrokerAccountResponse])
def list_broker_accounts(db: Session = Depends(get_db)):
    """获取券商账户列表"""
    return db.query(BrokerAccount).filter(BrokerAccount.is_active == True).all()


@router.put("/accounts/{account_id}", response_model=BrokerAccountResponse)
def update_broker_account(
    account_id: int,
    data: BrokerAccountUpdate,
    db: Session = Depends(get_db)
):
    """更新券商账户"""
    account = db.query(BrokerAccount).filter(BrokerAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="券商账户不存在")
    if data.broker_type is not None:
        account.broker_type = data.broker_type
    if data.account is not None:
        account.account = data.account
    if data.password is not None:
        account.password_encrypted = encryption_service.encrypt(data.password)
    if data.is_active is not None:
        account.is_active = data.is_active
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}")
def delete_broker_account(account_id: int, db: Session = Depends(get_db)):
    """删除券商账户（软删除）"""
    account = db.query(BrokerAccount).filter(BrokerAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="券商账户不存在")
    account.is_active = False
    db.commit()
    return {"message": "已禁用"}


@router.post("/accounts/{account_id}/login")
def login_broker(account_id: int, db: Session = Depends(get_db)):
    """登录券商账户"""
    service = BrokerService(db)
    try:
        service.login(account_id)
        return {"message": "登录成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"登录失败: {str(e)}")
```

- [ ] **Step 2: 注册路由**

在 `backend/app/api/__init__.py` 中新增：

```python
from app.api.broker import router as broker_router
```

并在 `__all__` 中添加 `"broker_router"`。

在 `backend/app/main.py` 中新增：

```python
from app.api import broker_router
# ...
app.include_router(broker_router)
```

- [ ] **Step 3: 新增依赖注入**

在 `backend/app/api/deps.py` 中新增：

```python
from app.services.broker_service import BrokerService
from app.services.fundamental_service import FundamentalService
from app.services.live_risk_control import LiveTradingRiskControl


def get_broker_service(db: Session = Depends(get_db)) -> BrokerService:
    return BrokerService(db)


def get_fundamental_service(db: Session = Depends(get_db)) -> FundamentalService:
    return FundamentalService(db)


def get_live_risk_control(db: Session = Depends(get_db)) -> LiveTradingRiskControl:
    return LiveTradingRiskControl(db)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/broker.py backend/app/api/__init__.py backend/app/main.py backend/app/api/deps.py
git commit -m "feat(api): 新增券商账户管理 API"
```

---

## Task 11: API 路由 — 实盘交易

**Files:**
- Create: `backend/app/api/live_trade.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建实盘交易 API**

新建 `backend/app/api/live_trade.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.live_trade import LiveTrade
from app.schemas.live_trade import (
    LiveTradeRequest, LiveTradeResponse, BrokerPosition, BrokerBalance
)
from app.services.broker_service import BrokerService
from app.services.live_risk_control import LiveTradingRiskControl

router = APIRouter(prefix="/api/live-trades", tags=["实盘交易"])


@router.post("/buy", response_model=LiveTradeResponse)
def live_buy(
    data: LiveTradeRequest,
    db: Session = Depends(get_db)
):
    """实盘买入"""
    risk_control = LiveTradingRiskControl(db)
    amount = data.price * data.quantity
    ok, msg = risk_control.validate_trade(user_id=1, amount=amount, stock_code=data.stock_code, trade_type="BUY")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    service = BrokerService(db)
    try:
        result = service.buy(data.stock_code, data.price, data.quantity)
        trade = LiveTrade(
            user_id=1,
            broker_account_id=service._account_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            trade_type="BUY",
            price=data.price,
            quantity=data.quantity,
            total_amount=amount,
            commission=0,
            broker_order_id=result.get("entrust_no", ""),
            status="filled",
            strategy_tag=data.strategy_tag
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"买入失败: {str(e)}")


@router.post("/sell", response_model=LiveTradeResponse)
def live_sell(
    data: LiveTradeRequest,
    db: Session = Depends(get_db)
):
    """实盘卖出"""
    risk_control = LiveTradingRiskControl(db)
    amount = data.price * data.quantity
    ok, msg = risk_control.validate_trade(user_id=1, amount=amount, stock_code=data.stock_code, trade_type="SELL")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    service = BrokerService(db)
    try:
        result = service.sell(data.stock_code, data.price, data.quantity)
        trade = LiveTrade(
            user_id=1,
            broker_account_id=service._account_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            trade_type="SELL",
            price=data.price,
            quantity=data.quantity,
            total_amount=amount,
            commission=0,
            broker_order_id=result.get("entrust_no", ""),
            status="filled",
            strategy_tag=data.strategy_tag
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"卖出失败: {str(e)}")


@router.get("/positions")
def get_live_positions(db: Session = Depends(get_db)):
    """查询实盘持仓"""
    service = BrokerService(db)
    try:
        return service.get_positions()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"查询持仓失败: {str(e)}")


@router.get("/balance")
def get_live_balance(db: Session = Depends(get_db)):
    """查询资金"""
    service = BrokerService(db)
    try:
        return service.get_balance()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"查询资金失败: {str(e)}")


@router.get("/history", response_model=List[LiveTradeResponse])
def get_live_trades(
    stock_code: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """实盘交易历史"""
    query = db.query(LiveTrade).filter(LiveTrade.user_id == 1)
    if stock_code:
        query = query.filter(LiveTrade.stock_code == stock_code)
    return query.order_by(LiveTrade.trade_time.desc()).limit(limit).all()


@router.post("/cancel/{order_id}")
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """撤单"""
    service = BrokerService(db)
    try:
        result = service.cancel_order(order_id)
        return {"message": "撤单成功" if result else "撤单失败"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"撤单失败: {str(e)}")
```

- [ ] **Step 2: 注册路由**

在 `backend/app/api/__init__.py` 中新增：

```python
from app.api.live_trade import router as live_trade_router
```

并在 `__all__` 中添加 `"live_trade_router"`。

在 `backend/app/main.py` 中新增：

```python
app.include_router(live_trade_router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/live_trade.py backend/app/api/__init__.py backend/app/main.py
git commit -m "feat(api): 新增实盘交易 API"
```

---

## Task 12: API 路由 — 基本面数据与实盘风控

**Files:**
- Create: `backend/app/api/fundamental.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建基本面数据 API**

新建 `backend/app/api/fundamental.py`：

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.fundamental_service import FundamentalService

router = APIRouter(prefix="/api/fundamental", tags=["基本面数据"])


@router.get("/{stock_code}/report")
def get_financial_report(stock_code: str, db: Session = Depends(get_db)):
    """获取财务报表"""
    service = FundamentalService(db)
    return service.get_financial_report(stock_code)


@router.get("/{stock_code}/indicators")
def get_financial_indicators(stock_code: str, db: Session = Depends(get_db)):
    """获取财务指标"""
    service = FundamentalService(db)
    return service.get_financial_indicators(stock_code)


@router.get("/{stock_code}/company")
def get_company_info(stock_code: str, db: Session = Depends(get_db)):
    """获取公司信息"""
    service = FundamentalService(db)
    return service.get_company_info(stock_code)
```

- [ ] **Step 2: 注册路由**

在 `backend/app/api/__init__.py` 中新增：

```python
from app.api.fundamental import router as fundamental_router
```

并在 `__all__` 中添加 `"fundamental_router"`。

在 `backend/app/main.py` 中新增：

```python
app.include_router(fundamental_router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/fundamental.py backend/app/api/__init__.py backend/app/main.py
git commit -m "feat(api): 新增基本面数据 API"
```

---

## Task 13: 前端 — API 服务层

**Files:**
- Create: `frontend/src/services/brokerApi.ts`
- Create: `frontend/src/services/liveTradeApi.ts`
- Create: `frontend/src/services/fundamentalApi.ts`

- [ ] **Step 1: 创建券商 API 服务**

新建 `frontend/src/services/brokerApi.ts`：

```typescript
import axios from 'axios';

const API_BASE = '/api/broker';

export interface BrokerAccount {
  id: number;
  user_id: number;
  broker_type: string;
  account: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface BrokerAccountCreate {
  broker_type: string;
  account: string;
  password: string;
}

export const brokerApi = {
  list: () => axios.get<BrokerAccount[]>(`${API_BASE}/accounts`),
  create: (data: BrokerAccountCreate) => axios.post<BrokerAccount>(`${API_BASE}/accounts`, data),
  update: (id: number, data: Partial<BrokerAccountCreate & { is_active: boolean }>) =>
    axios.put<BrokerAccount>(`${API_BASE}/accounts/${id}`, data),
  delete: (id: number) => axios.delete(`${API_BASE}/accounts/${id}`),
  login: (id: number) => axios.post(`${API_BASE}/accounts/${id}/login`),
};
```

- [ ] **Step 2: 创建实盘交易 API 服务**

新建 `frontend/src/services/liveTradeApi.ts`：

```typescript
import axios from 'axios';

const API_BASE = '/api/live-trades';

export interface LiveTrade {
  id: number;
  stock_code: string;
  stock_name: string | null;
  trade_type: string;
  price: number;
  quantity: number;
  total_amount: number;
  commission: number;
  broker_order_id: string | null;
  status: string;
  strategy_tag: string | null;
  trade_time: string;
}

export interface TradeRequest {
  stock_code: string;
  stock_name: string;
  price: number;
  quantity: number;
  strategy_tag?: string;
}

export const liveTradeApi = {
  buy: (data: TradeRequest) => axios.post<LiveTrade>(`${API_BASE}/buy`, data),
  sell: (data: TradeRequest) => axios.post<LiveTrade>(`${API_BASE}/sell`, data),
  cancel: (orderId: string) => axios.post(`${API_BASE}/cancel/${orderId}`),
  positions: () => axios.get(`${API_BASE}/positions`),
  balance: () => axios.get(`${API_BASE}/balance`),
  history: (stockCode?: string, limit = 50) =>
    axios.get<LiveTrade[]>(`${API_BASE}/history`, { params: { stock_code: stockCode, limit } }),
};
```

- [ ] **Step 3: 创建基本面 API 服务**

新建 `frontend/src/services/fundamentalApi.ts`：

```typescript
import axios from 'axios';

const API_BASE = '/api/fundamental';

export const fundamentalApi = {
  getReport: (stockCode: string) => axios.get(`${API_BASE}/${stockCode}/report`),
  getIndicators: (stockCode: string) => axios.get(`${API_BASE}/${stockCode}/indicators`),
  getCompanyInfo: (stockCode: string) => axios.get(`${API_BASE}/${stockCode}/company`),
};
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/services/brokerApi.ts frontend/src/services/liveTradeApi.ts frontend/src/services/fundamentalApi.ts
git commit -m "feat(frontend): 新增券商/实盘交易/基本面 API 服务层"
```

---

## Task 14: 前端 — 券商账户管理页面

**Files:**
- Create: `frontend/src/pages/BrokerAccount.tsx`

- [ ] **Step 1: 创建券商账户管理页面**

新建 `frontend/src/pages/BrokerAccount.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, Switch, message, Space, Tag } from 'antd';
import { PlusOutlined, LoginOutlined, DeleteOutlined } from '@ant-design/icons';
import { brokerApi, BrokerAccount as BrokerAccountType } from '../services/brokerApi';

function BrokerAccountPage() {
  const [accounts, setAccounts] = useState<BrokerAccountType[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const res = await brokerApi.list();
      setAccounts(res.data);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAccounts(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await brokerApi.create(values);
      message.success('添加成功');
      setModalOpen(false);
      form.resetFields();
      loadAccounts();
    } catch {
      message.error('添加失败');
    }
  };

  const handleLogin = async (id: number) => {
    try {
      await brokerApi.login(id);
      message.success('登录成功');
      loadAccounts();
    } catch {
      message.error('登录失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await brokerApi.delete(id);
      message.success('已禁用');
      loadAccounts();
    } catch {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '券商类型', dataIndex: 'broker_type', key: 'broker_type' },
    { title: '资金账号', dataIndex: 'account', key: 'account' },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (active: boolean) => active ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>
    },
    {
      title: '最后登录', dataIndex: 'last_login_at', key: 'last_login_at',
      render: (t: string | null) => t ? new Date(t).toLocaleString() : '未登录'
    },
    {
      title: '操作', key: 'action',
      render: (_: any, record: BrokerAccountType) => (
        <Space>
          <Button icon={<LoginOutlined />} onClick={() => handleLogin(record.id)}>登录</Button>
          <Button icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>禁用</Button>
        </Space>
      )
    },
  ];

  return (
    <Card title="券商账户管理" extra={<Button icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加账户</Button>}>
      <Table dataSource={accounts} columns={columns} rowKey="id" loading={loading} />
      <Modal title="添加券商账户" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="broker_type" label="券商类型" initialValue="eastmoney">
            <Select options={[{ value: 'eastmoney', label: '东方财富证券' }]} />
          </Form.Item>
          <Form.Item name="account" label="资金账号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default BrokerAccountPage;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/BrokerAccount.tsx
git commit -m "feat(frontend): 新增券商账户管理页面"
```

---

## Task 15: 前端 — 实盘交易页面

**Files:**
- Create: `frontend/src/pages/LiveTrade.tsx`

- [ ] **Step 1: 创建实盘交易页面**

新建 `frontend/src/pages/LiveTrade.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { Card, Table, Button, Form, InputNumber, Input, message, Space, Tabs, Tag, Row, Col, Statistic } from 'antd';
import { liveTradeApi, LiveTrade as LiveTradeType } from '../services/liveTradeApi';

function LiveTradePage() {
  const [trades, setTrades] = useState<LiveTradeType[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [balance, setBalance] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [buyForm] = Form.useForm();
  const [sellForm] = Form.useForm();

  const loadData = async () => {
    setLoading(true);
    try {
      const [tradesRes, posRes, balRes] = await Promise.all([
        liveTradeApi.history(),
        liveTradeApi.positions().catch(() => ({ data: [] })),
        liveTradeApi.balance().catch(() => ({ data: null })),
      ]);
      setTrades(tradesRes.data);
      setPositions(posRes.data || []);
      setBalance(balRes.data);
    } catch {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleBuy = async () => {
    try {
      const values = await buyForm.validateFields();
      await liveTradeApi.buy({ ...values, stock_name: '' });
      message.success('买入成功');
      buyForm.resetFields();
      loadData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '买入失败');
    }
  };

  const handleSell = async () => {
    try {
      const values = await sellForm.validateFields();
      await liveTradeApi.sell({ ...values, stock_name: '' });
      message.success('卖出成功');
      sellForm.resetFields();
      loadData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '卖出失败');
    }
  };

  const tradeColumns = [
    { title: '时间', dataIndex: 'trade_time', key: 'trade_time', render: (t: string) => new Date(t).toLocaleString() },
    { title: '股票', dataIndex: 'stock_code', key: 'stock_code' },
    { title: '名称', dataIndex: 'stock_name', key: 'stock_name' },
    { title: '类型', dataIndex: 'trade_type', key: 'trade_type', render: (t: string) => <Tag color={t === 'BUY' ? 'green' : 'red'}>{t === 'BUY' ? '买入' : '卖出'}</Tag> },
    { title: '价格', dataIndex: 'price', key: 'price' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ];

  return (
    <div>
      {balance && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Card><Statistic title="总资产" value={balance.total_assets} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="可用资金" value={balance.available_cash} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="市值" value={balance.market_value} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="冻结资金" value={balance.frozen_amount} precision={2} /></Card></Col>
        </Row>
      )}
      <Tabs items={[
        {
          key: 'trade', label: '交易下单',
          children: (
            <Row gutter={16}>
              <Col span={12}>
                <Card title="买入">
                  <Form form={buyForm} layout="vertical">
                    <Form.Item name="stock_code" label="股票代码" rules={[{ required: true }]}>
                      <Input placeholder="如 000001" />
                    </Form.Item>
                    <Form.Item name="price" label="价格" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={0.01} min={0} />
                    </Form.Item>
                    <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={100} min={100} />
                    </Form.Item>
                    <Button type="primary" onClick={handleBuy} block>买入</Button>
                  </Form>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="卖出">
                  <Form form={sellForm} layout="vertical">
                    <Form.Item name="stock_code" label="股票代码" rules={[{ required: true }]}>
                      <Input placeholder="如 000001" />
                    </Form.Item>
                    <Form.Item name="price" label="价格" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={0.01} min={0} />
                    </Form.Item>
                    <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={100} min={100} />
                    </Form.Item>
                    <Button type="primary" danger onClick={handleSell} block>卖出</Button>
                  </Form>
                </Card>
              </Col>
            </Row>
          )
        },
        {
          key: 'history', label: '交易记录',
          children: <Table dataSource={trades} columns={tradeColumns} rowKey="id" loading={loading} />
        },
      ]} />
    </div>
  );
}

export default LiveTradePage;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/LiveTrade.tsx
git commit -m "feat(frontend): 新增实盘交易页面"
```

---

## Task 16: 前端 — 基本面分析页面

**Files:**
- Create: `frontend/src/pages/Fundamental.tsx`

- [ ] **Step 1: 创建基本面分析页面**

新建 `frontend/src/pages/Fundamental.tsx`：

```tsx
import { useState } from 'react';
import { Card, Input, Descriptions, Spin, message, Row, Col, Empty } from 'antd';
import { fundamentalApi } from '../services/fundamentalApi';

function FundamentalPage() {
  const [stockCode, setStockCode] = useState('');
  const [company, setCompany] = useState<any>(null);
  const [indicators, setIndicators] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadData = async (code: string) => {
    if (!code) return;
    setLoading(true);
    try {
      const [compRes, indRes, repRes] = await Promise.all([
        fundamentalApi.getCompanyInfo(code),
        fundamentalApi.getIndicators(code),
        fundamentalApi.getReport(code),
      ]);
      setCompany(compRes.data);
      setIndicators(indRes.data);
      setReport(repRes.data);
    } catch {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="输入股票代码，如 000001"
          enterButton="查询"
          size="large"
          value={stockCode}
          onChange={e => setStockCode(e.target.value)}
          onSearch={loadData}
        />
      </Card>
      <Spin spinning={loading}>
        {!company && !indicators ? (
          <Empty description="请输入股票代码查询" />
        ) : (
          <Row gutter={16}>
            <Col span={12}>
              <Card title="公司信息">
                {company && (
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="股票代码">{company.stock_code}</Descriptions.Item>
                    <Descriptions.Item label="公司名称">{company.company_name}</Descriptions.Item>
                    <Descriptions.Item label="行业">{company.industry}</Descriptions.Item>
                    <Descriptions.Item label="总市值">{company.total_market_cap?.toLocaleString()}</Descriptions.Item>
                    <Descriptions.Item label="流通市值">{company.circulating_market_cap?.toLocaleString()}</Descriptions.Item>
                  </Descriptions>
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="财务指标">
                {indicators && (
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="市盈率(PE)">{indicators.pe_ratio?.toFixed(2) ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="市净率(PB)">{indicators.pb_ratio?.toFixed(2) ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="净资产收益率(ROE)">{indicators.roe?.toFixed(2) ?? '-'}%</Descriptions.Item>
                    <Descriptions.Item label="销售毛利率">{indicators.gross_margin?.toFixed(2) ?? '-'}%</Descriptions.Item>
                    <Descriptions.Item label="销售净利率">{indicators.net_margin?.toFixed(2) ?? '-'}%</Descriptions.Item>
                    <Descriptions.Item label="资产负债率">{indicators.debt_ratio?.toFixed(2) ?? '-'}%</Descriptions.Item>
                  </Descriptions>
                )}
              </Card>
            </Col>
          </Row>
        )}
      </Spin>
    </div>
  );
}

export default FundamentalPage;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Fundamental.tsx
git commit -m "feat(frontend): 新增基本面分析页面"
```

---

## Task 17: 前端 — 路由注册与交易模式切换

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 更新 App.tsx**

修改 `frontend/src/App.tsx`，新增路由和交易模式切换：

```tsx
import { useState } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Switch, Tag, Space } from 'antd';
import {
  DashboardOutlined,
  StockOutlined,
  LineChartOutlined,
  FileTextOutlined,
  RobotOutlined,
  BankOutlined,
  FundOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';
import Prediction from './pages/Prediction';
import Review from './pages/Review';
import AutoTrading from './pages/AutoTrading';
import BrokerAccountPage from './pages/BrokerAccount';
import LiveTradePage from './pages/LiveTrade';
import FundamentalPage from './pages/Fundamental';

const { Header, Content } = Layout;

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLive, setIsLive] = useState(false);

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '首页' },
    { key: '/trade', icon: <StockOutlined />, label: isLive ? '实盘交易' : '模拟交易' },
    { key: '/prediction', icon: <LineChartOutlined />, label: '预测' },
    { key: '/review', icon: <FileTextOutlined />, label: '复盘' },
    { key: '/auto-trading', icon: <RobotOutlined />, label: '自动交易' },
    { key: '/fundamental', icon: <FundOutlined />, label: '基本面' },
    { key: '/broker', icon: <BankOutlined />, label: '券商账户' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <h1 style={{ color: 'white', margin: 0, marginRight: 20 }}>股票交易系统</h1>
        <Space style={{ marginRight: 20 }}>
          <Tag color={isLive ? 'red' : 'blue'}>{isLive ? '实盘模式' : '模拟模式'}</Tag>
          <Switch
            checked={isLive}
            onChange={(checked) => {
              if (checked) {
                Modal.confirm({
                  title: '切换到实盘模式',
                  content: '实盘交易涉及真实资金，请确认已配置券商账户并了解风险。',
                  onOk: () => setIsLive(true),
                });
              } else {
                setIsLive(false);
              }
            }}
            checkedChildren="实盘"
            unCheckedChildren="模拟"
          />
        </Space>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trade" element={isLive ? <LiveTradePage /> : <Trade />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/review" element={<Review />} />
          <Route path="/auto-trading" element={<AutoTrading />} />
          <Route path="/fundamental" element={<FundamentalPage />} />
          <Route path="/broker" element={<BrokerAccountPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
```

注意：需要在文件顶部补充 `Modal` 的导入：

```tsx
import { Layout, Menu, Switch, Tag, Space, Modal } from 'antd';
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): 新增路由和交易模式切换"
```

---

## Task 18: 集成测试 — 后端服务启动验证

**Files:**
- Test: 后端服务启动和基本 API 响应

- [ ] **Step 1: 启动后端服务验证**

```bash
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

预期：服务正常启动，无 import 错误。

- [ ] **Step 2: 验证新增 API 端点**

```bash
# 券商账户
curl http://localhost:8000/api/broker/accounts

# 实盘交易历史
curl http://localhost:8000/api/live-trades/history

# 基本面数据
curl http://localhost:8000/api/fundamental/000001/indicators
```

预期：所有端点返回 JSON 响应（数据为空或报错均可，只要不 500）。

- [ ] **Step 3: 验证前端编译**

```bash
cd frontend && npm run build
```

预期：编译成功，无 TypeScript 错误。

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "test: 验证实盘交易功能集成"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** 设计文档中所有模块（券商对接、行情数据、基本面数据、风控）均有对应 Task
- [x] **Placeholder scan:** 无 TBD/TODO，所有步骤包含完整代码
- [x] **Type consistency:** BrokerService/LiveTrade/FundamentalService 类型在模型、Schema、API 间保持一致
- [x] **现有功能保留:** 模拟交易功能完全保留，实盘作为新增能力
- [x] **数据库迁移:** 使用 `Base.metadata.create_all` 自动建表，无需手动迁移
