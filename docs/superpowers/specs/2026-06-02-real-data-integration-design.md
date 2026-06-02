# 真实数据接入设计文档

**日期**: 2026-06-02
**版本**: v1.0
**状态**: 待审核

## 1. 概述

### 1.1 目标
将现有的模拟炒股系统升级为支持实盘交易的完整系统，接入真实券商、实时行情和基本面数据。

### 1.2 核心需求
- **券商对接**: 东方财富证券实盘交易
- **行情数据**: 延迟行情（免费）
- **基本面数据**: 财务报表、财务指标、行业数据
- **使用场景**: 小额实盘验证

### 1.3 设计原则
- **双模式运行**: 模拟交易和实盘交易并存
- **渐进式迁移**: 保留现有功能，实盘作为新增能力
- **安全第一**: 小额验证，严格风控

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                  前端 (React)                        │
├─────────────────────────────────────────────────────┤
│                  FastAPI 后端                        │
├─────────────┬─────────────┬───────────────────────┤
│  券商对接   │  行情数据    │    基本面数据         │
│  (easytrader)│  (efinance) │    (AKShare)         │
└─────────────┴─────────────┴───────────────────────┘
         │            │               │
         ▼            ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ 东方财富证券 │ │ 东方财富数据 │ │ 公开财务数据 │
│  实盘交易    │ │  行情推送    │ │  财报/指标   │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 2.2 模块划分

| 模块 | 职责 | 技术栈 |
|------|------|--------|
| BrokerService | 券商对接、实盘交易 | easytrader |
| DataService | 行情数据获取 | AKShare + efinance |
| FundamentalService | 基本面数据 | AKShare |
| LiveTradingRiskControl | 实盘风控 | 自研 |
| TradingEngine | 交易引擎（支持双模式） | SQLAlchemy |

## 3. 券商对接模块

### 3.1 技术方案
使用 easytrader 库通过 COM 接口连接东方财富证券客户端。

### 3.2 核心接口

```python
class BrokerService:
    """券商服务"""

    def __init__(self, broker_type: str = "eastmoney"):
        self.user = easytrader.use(broker_type)

    def login(self, account: str, password: str):
        """登录券商账户"""
        self.user.prepare(account, password)

    def buy(self, stock_code: str, price: float, quantity: int) -> dict:
        """买入股票"""
        return self.user.buy(stock_code, price=price, amount=quantity)

    def sell(self, stock_code: str, price: float, quantity: int) -> dict:
        """卖出股票"""
        return self.user.sell(stock_code, price=price, amount=quantity)

    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        return self.user.cancel_entrust(order_id)

    def get_positions(self) -> list:
        """查询持仓"""
        return self.user.position

    def get_balance(self) -> dict:
        """查询资金"""
        return self.user.balance

    def get_today_trades(self) -> list:
        """查询当日成交"""
        return self.user.today_trades

    def get_today_entrusts(self) -> list:
        """查询当日委托"""
        return self.user.today_entrusts
```

### 3.3 账户管理

```python
class BrokerAccount:
    """券商账户配置"""

    broker_type: str  # 券商类型
    account: str  # 资金账号
    password: str  # 密码（加密存储）
    is_active: bool  # 是否激活
```

### 3.4 安全措施
- 账户密码 AES 加密存储
- 登录状态自动维护
- 会话超时自动重连

## 4. 行情数据模块

### 4.1 数据源策略
采用双数据源互备策略：
- **主数据源**: efinance（东方财富数据，更稳定）
- **备用数据源**: AKShare（现有方案，作为降级）

### 4.2 统一数据接口

```python
class DataService:
    """统一数据服务"""

    def __init__(self):
        self.akshare_source = AKShareSource()
        self.efinance_source = EFinanceSource()

    def get_stock_quote(self, stock_code: str) -> StockQuote:
        """获取实时行情 - 自动切换数据源"""
        try:
            return self.efinance_source.get_quote(stock_code)
        except Exception:
            return self.akshare_source.get_quote(stock_code)

    def get_stock_history(self, stock_code: str, days: int) -> List[StockHistory]:
        """获取历史数据"""
        try:
            return self.efinance_source.get_history(stock_code, days)
        except Exception:
            return self.akshare_source.get_history(stock_code, days)

    def get_minute_kline(self, stock_code: str, period: str = "1") -> dict:
        """获取分钟级K线"""
        return self.efinance_source.get_minute_kline(stock_code, period)

    def get_order_book(self, stock_code: str) -> dict:
        """获取盘口数据（五档）"""
        return self.efinance_source.get_order_book(stock_code)
```

### 4.3 新增数据类型

| 数据类型 | 说明 | 更新频率 |
|----------|------|----------|
| 实时行情 | 当前价、涨跌幅、成交量 | 实时 |
| 分钟K线 | 1/5/15/30/60分钟K线 | 分钟级 |
| 盘口数据 | 五档买卖价量 | 实时 |
| 资金流向 | 主力/散户资金流向 | 日级 |

## 5. 基本面数据模块

### 5.1 数据来源
- AKShare 财务数据接口
- 东方财富公开数据

### 5.2 核心接口

```python
class FundamentalService:
    """基本面数据服务"""

    def get_financial_report(self, stock_code: str) -> dict:
        """获取财务报表"""
        return {
            "balance_sheet": self._get_balance_sheet(stock_code),
            "income_statement": self._get_income_statement(stock_code),
            "cash_flow": self._get_cash_flow(stock_code)
        }

    def get_financial_indicators(self, stock_code: str) -> dict:
        """获取财务指标"""
        return {
            "pe_ratio": self._get_pe_ratio(stock_code),
            "pb_ratio": self._get_pb_ratio(stock_code),
            "roe": self._get_roe(stock_code),
            "gross_margin": self._get_gross_margin(stock_code)
        }

    def get_industry_data(self, industry: str) -> dict:
        """获取行业数据"""
        return {
            "industry_average": self._get_industry_average(industry),
            "industry_ranking": self._get_industry_ranking(industry)
        }

    def get_company_info(self, stock_code: str) -> dict:
        """获取公司基本信息"""
        return {
            "company_name": self._get_company_name(stock_code),
            "main_business": self._get_main_business(stock_code),
            "shareholders": self._get_shareholders(stock_code)
        }
```

### 5.3 数据存储
- 财务数据每日更新
- 缓存到 PostgreSQL
- 提供数据更新时间戳
- 支持历史数据查询

## 6. 风控与安全模块

### 6.1 实盘交易风控

```python
class LiveTradingRiskControl:
    """实盘风控系统"""

    # 小额验证模式限制
    MAX_INITIAL_CAPITAL = 100000  # 初始资金上限10万
    MAX_SINGLE_TRADE_AMOUNT = 10000  # 单笔最大1万
    MAX_DAILY_TRADES = 10  # 每日最多10笔
    MAX_DAILY_LOSS = 5000  # 每日最大亏损5000
    MAX_POSITION_RATIO = 0.2  # 单只股票最大仓位20%
    STOP_LOSS_RATIO = -0.05  # 止损线-5%

    def validate_trade(self, trade_request: dict) -> Tuple[bool, str]:
        """交易前验证"""
        # 1. 检查交易金额
        if trade_request["amount"] > self.MAX_SINGLE_TRADE_AMOUNT:
            return False, f"单笔交易金额不能超过{self.MAX_SINGLE_TRADE_AMOUNT}元"

        # 2. 检查每日交易次数
        if self._get_today_trade_count() >= self.MAX_DAILY_TRADES:
            return False, f"每日交易次数不能超过{self.MAX_DAILY_TRADES}次"

        # 3. 检查每日亏损
        if self._get_today_loss() >= self.MAX_DAILY_LOSS:
            return False, f"每日亏损已达上限{self.MAX_DAILY_LOSS}元"

        # 4. 检查仓位集中度
        if self._check_position_concentration(trade_request):
            return False, "仓位过于集中"

        return True, "验证通过"

    def emergency_stop(self):
        """紧急熔断"""
        # 暂停所有自动交易
        # 发送告警通知
        pass

    def check_stop_loss(self):
        """检查止损"""
        # 遍历所有持仓
        # 检查是否触发止损
        # 自动平仓
        pass
```

### 6.2 安全措施

| 安全措施 | 实现方式 |
|----------|----------|
| 账户安全 | AES加密存储券商账户信息 |
| 交易确认 | 大额交易（>5000元）需二次确认 |
| 日志审计 | 所有交易操作完整记录，不可篡改 |
| 异常告警 | 异常交易实时钉钉/邮件通知 |
| 访问控制 | API接口认证，操作权限控制 |

### 6.3 告警规则

| 告警类型 | 触发条件 | 通知方式 |
|----------|----------|----------|
| 交易异常 | 单笔>1万、日亏损>5000 | 钉钉+邮件 |
| 账户异常 | 登录失败、会话断开 | 钉钉 |
| 系统异常 | 数据源故障、服务宕机 | 钉钉+邮件 |
| 风控触发 | 触发止损、熔断 | 钉钉+邮件 |

## 7. 数据库设计

### 7.1 新增表

```sql
-- 券商账户表
CREATE TABLE broker_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    broker_type VARCHAR(50) NOT NULL,
    account VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实盘交易记录表
CREATE TABLE live_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    broker_account_id INTEGER REFERENCES broker_accounts(id),
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50),
    trade_type VARCHAR(10) NOT NULL,  -- BUY/SELL
    price DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    commission DECIMAL(10, 2),
    broker_order_id VARCHAR(100),  -- 券商订单号
    status VARCHAR(20) DEFAULT 'pending',  -- pending/filled/cancelled/failed
    trade_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    strategy_tag VARCHAR(50)
);

-- 基本面数据表
CREATE TABLE fundamental_data (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL,  -- balance_sheet/income/cash_flow/indicators
    data JSONB NOT NULL,
    report_date DATE NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, data_type, report_date)
);

-- 风控记录表
CREATE TABLE risk_control_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,  -- trade_rejected/stop_loss/circuit_breaker
    event_detail JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7.2 修改现有表

```sql
-- 用户表新增字段
ALTER TABLE users ADD COLUMN trading_mode VARCHAR(20) DEFAULT 'simulation';
-- trading_mode: simulation/live

-- 交易表新增字段
ALTER TABLE trades ADD COLUMN broker_order_id VARCHAR(100);
ALTER TABLE trades ADD COLUMN is_live_trade BOOLEAN DEFAULT false;
```

## 8. API 设计

### 8.1 券商账户管理

```
POST   /api/broker/accounts          # 添加券商账户
GET    /api/broker/accounts          # 获取券商账户列表
PUT    /api/broker/accounts/{id}     # 更新券商账户
DELETE /api/broker/accounts/{id}     # 删除券商账户
POST   /api/broker/accounts/{id}/login  # 登录券商
```

### 8.2 实盘交易

```
POST   /api/live-trades/buy          # 实盘买入
POST   /api/live-trades/sell         # 实盘卖出
POST   /api/live-trades/cancel/{id}  # 撤单
GET    /api/live-trades/positions    # 查询实盘持仓
GET    /api/live-trades/balance      # 查询资金
GET    /api/live-trades/history      # 实盘交易历史
```

### 8.3 基本面数据

```
GET    /api/fundamental/{code}/report       # 财务报表
GET    /api/fundamental/{code}/indicators   # 财务指标
GET    /api/fundamental/{code}/company      # 公司信息
GET    /api/fundamental/industry/{name}     # 行业数据
```

### 8.4 风控管理

```
GET    /api/risk-control/live/status        # 实盘风控状态
PUT    /api/risk-control/live/config        # 更新风控配置
POST   /api/risk-control/live/emergency-stop # 紧急熔断
GET    /api/risk-control/live/records       # 风控记录
```

## 9. 前端设计

### 9.1 新增页面

| 页面 | 路由 | 功能 |
|------|------|------|
| 券商账户管理 | /broker | 管理券商账户、登录状态 |
| 实盘交易 | /live-trade | 实盘买卖、持仓查询 |
| 基本面分析 | /fundamental/{code} | 财务报表、指标分析 |
| 风控中心 | /risk-control | 风控配置、告警记录 |

### 9.2 交易模式切换
在顶部导航栏增加交易模式切换开关：
- 模拟交易（默认）
- 实盘交易

切换时需二次确认，并显示当前账户资金信息。

## 10. 实施计划

### 10.1 阶段一：基础架构（第1-2周）
- [ ] 新增数据库表
- [ ] 实现 BrokerService 基础框架
- [ ] 实现 DataService 双数据源
- [ ] 配置管理（.env）

### 10.2 阶段二：券商对接（第3-4周）
- [ ] 实现 easytrader 集成
- [ ] 实现券商账户管理
- [ ] 实现基础交易功能
- [ ] 实现账户安全加密

### 10.3 阶段三：数据增强（第5-6周）
- [ ] 实现 efinance 集成
- [ ] 实现基本面数据服务
- [ ] 实现数据缓存机制
- [ ] 实现数据更新定时任务

### 10.4 阶段四：风控与前端（第7-8周）
- [ ] 实现实盘风控系统
- [ ] 实现告警系统
- [ ] 实现前端新页面
- [ ] 实现交易模式切换

### 10.5 阶段五：测试与上线（第9-10周）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 小额实盘验证
- [ ] 文档完善

## 11. 依赖包

### 11.1 新增 Python 依赖

```
easytrader==0.5.15
efinance==0.5.6
cryptography==41.0.0  # 用于账户加密
APScheduler==3.10.4   # 用于定时任务
```

### 11.2 环境变量

```env
# 券商配置
BROKER_TYPE=eastmoney
BROKER_ACCOUNT=
BROKER_PASSWORD=

# 数据源配置
PRIMARY_DATA_SOURCE=efinance
FALLBACK_DATA_SOURCE=akshare

# 风控配置
LIVE_MAX_INITIAL_CAPITAL=100000
LIVE_MAX_SINGLE_TRADE=10000
LIVE_MAX_DAILY_TRADES=10
LIVE_MAX_DAILY_LOSS=5000
LIVE_STOP_LOSS_RATIO=-0.05
```

## 12. 风险评估

### 12.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| easytrader 稳定性 | 交易失败 | 重试机制、异常处理 |
| 数据源故障 | 行情中断 | 双数据源互备 |
| 券商客户端更新 | 接口失效 | 关注更新、快速适配 |

### 12.2 业务风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 策略亏损 | 资金损失 | 严格风控、小额验证 |
| 系统故障 | 无法交易 | 紧急熔断、手动干预 |
| 网络延迟 | 交易延迟 | 本地部署、网络优化 |

## 13. 待确认事项

- [ ] easytrader 是否支持最新版东方财富客户端
- [ ] 东方财富是否需要开通特定权限
- [ ] efinance 免费版的数据延迟具体是多少

## 14. 参考资料

- [easytrader GitHub](https://github.com/shidenggui/easytrader)
- [efinance GitHub](https://github.com/Micro-sheep/efinance)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [东方财富量化平台](https://quant.eastmoney.com)
