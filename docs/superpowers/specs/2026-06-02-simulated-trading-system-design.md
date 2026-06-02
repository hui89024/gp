# 模拟交易系统设计文档

## 1. 项目概述

### 1.1 项目目标

构建一个完整的模拟交易系统，支持多市场交易、高级订单类型、策略回测和交易心理分析。

**核心功能：**
- 多市场支持：A股、港股、美股
- 高级订单类型：限价单、市价单、止损单、止盈单、条件单
- 策略回测：基于历史数据的策略测试和优化
- 交易心理分析：情绪分析、纪律分析、行为模式识别

### 1.2 技术选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | React 18 + TypeScript | 类型安全，组件化 |
| UI组件库 | Ant Design 5 | 企业级UI组件 |
| 图表库 | ECharts 5 + TradingView | 专业金融图表 |
| 状态管理 | Zustand | 轻量级状态管理 |
| 后端框架 | FastAPI | 高性能异步框架 |
| ORM | SQLAlchemy 2.0 | 异步支持 |
| 任务队列 | Celery + Redis | 异步任务处理 |
| 数据库 | PostgreSQL 15 | 主数据库 |
| 时序数据库 | TimescaleDB | 行情数据存储 |
| 缓存 | Redis 7 | 缓存和实时数据 |
| 实时通信 | Socket.IO | WebSocket支持 |
| 部署 | Docker + Docker Compose | 容器化部署 |

### 1.3 数据源

使用免费API获取股票数据：
- AKShare：A股行情、财务数据
- 港股数据接口
- 美股数据接口

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (React + TypeScript)               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │ 交易终端   │ │ 数据分析   │ │ 策略管理   │ │ 系统设置 │ │
│  │ Trading    │ │ Analytics  │ │ Strategy   │ │ Settings │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API网关层 (Nginx)                         │
│  - 负载均衡  - 限流  - 认证  - 路由                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端服务层 (FastAPI)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 交易模块   │  │ 数据模块   │  │ 分析模块   │         │
│  │ Trading    │  │ Data       │  │ Analytics  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                 ┌─────────────┐                             │
│                 │ 核心服务   │                             │
│                 │ Core       │                             │
│                 └──────┬──────┘                             │
│                        │                                    │
│           ┌────────────┼────────────┐                       │
│           ▼            ▼            ▼                       │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│     │ 任务队列 │ │ 缓存服务 │ │ 通知服务 │                 │
│     │ Celery   │ │ Redis    │ │ WebSocket│                 │
│     └──────────┘ └──────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL │  │ TimescaleDB │  │ Redis      │         │
│  │ 业务数据   │  │ 时序数据   │  │ 缓存/实时  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

**交易模块 (Trading)**
- 虚拟账户管理（多市场支持）
- 订单系统（高级订单类型）
- 撮合引擎（模拟真实交易规则）
- 持仓管理（跨市场合并）

**数据模块 (Data)**
- 多市场数据获取（A股、港股、美股）
- 实时行情推送（WebSocket）
- 历史数据存储（TimescaleDB）
- 数据清洗和标准化

**分析模块 (Analytics)**
- 策略回测引擎
- 交易心理分析
- 行为模式识别
- 绩效评估报告

**核心服务 (Core)**
- 用户认证和授权
- 风险控制引擎
- 策略引擎
- 通知和告警

## 3. 数据模型

### 3.1 核心数据表

**用户账户表 (users)**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    initial_capital DECIMAL(15,2) DEFAULT 1000000,
    current_capital DECIMAL(15,2),
    risk_level VARCHAR(20) DEFAULT 'MODERATE',  -- CONSERVATIVE/MODERATE/AGGRESSIVE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**多市场账户表 (market_accounts)**
```sql
CREATE TABLE market_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    market VARCHAR(10) NOT NULL,  -- CN/HK/US
    currency VARCHAR(3) NOT NULL, -- CNY/HKD/USD
    initial_capital DECIMAL(15,2) NOT NULL,
    current_capital DECIMAL(15,2) NOT NULL,
    exchange_rate DECIMAL(10,6) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, market)
);
```

**持仓表 (positions)**
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    market VARCHAR(10) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50),
    quantity INTEGER NOT NULL,
    avg_cost DECIMAL(15,4),
    current_price DECIMAL(15,4),
    unrealized_pnl DECIMAL(15,2),
    unrealized_pnl_pct DECIMAL(8,4),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, market, stock_code)
);
```

**订单表 (orders)**
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    market VARCHAR(10) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50),
    order_type VARCHAR(20) NOT NULL,  -- MARKET/LIMIT/STOP_LOSS/TAKE_PROFIT/CONDITIONAL
    direction VARCHAR(4) NOT NULL,    -- BUY/SELL
    price DECIMAL(15,4),
    quantity INTEGER NOT NULL,
    filled_quantity INTEGER DEFAULT 0,
    avg_fill_price DECIMAL(15,4),
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/FILLED/PARTIAL/CANCELLED/REJECTED
    time_in_force VARCHAR(10) DEFAULT 'GTC',  -- GTC/IOC/FOK/DAY
    stop_price DECIMAL(15,4),
    condition_type VARCHAR(20),
    condition_value VARCHAR(100),
    strategy_tag VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP
);
```

**交易记录表 (trades)**
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_id INTEGER REFERENCES orders(id),
    market VARCHAR(10) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    trade_type VARCHAR(4) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    quantity INTEGER NOT NULL,
    commission DECIMAL(15,2),
    tax DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    strategy_tag VARCHAR(50),
    trade_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**回测记录表 (backtest_records)**
```sql
CREATE TABLE backtest_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(50) NOT NULL,
    market VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL,
    final_capital DECIMAL(15,2) NOT NULL,
    total_return DECIMAL(8,4),
    annual_return DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    win_rate DECIMAL(8,4),
    total_trades INTEGER,
    config JSONB,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**交易心理分析表 (trading_psychology)**
```sql
CREATE TABLE trading_psychology (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    analysis_date DATE NOT NULL,
    emotion_score DECIMAL(5,2),  -- 情绪得分 0-100
    discipline_score DECIMAL(5,2),  -- 纪律得分 0-100
    risk_adherence DECIMAL(5,2),  -- 风险遵守度 0-100
    patterns JSONB,  -- 行为模式
    recommendations JSONB,  -- 改进建议
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 数据关系

```
users (1) ──→ (N) market_accounts
users (1) ──→ (N) positions
users (1) ──→ (N) orders
users (1) ──→ (N) trades
users (1) ──→ (N) backtest_records
users (1) ──→ (N) trading_psychology
orders (1) ──→ (N) trades
```

### 3.3 索引设计

```sql
-- 性能优化索引
CREATE INDEX idx_positions_user_market ON positions(user_id, market);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_stock_code ON orders(stock_code);
CREATE INDEX idx_trades_user_time ON trades(user_id, trade_time DESC);
CREATE INDEX idx_trades_stock_code ON trades(stock_code);
CREATE INDEX idx_backtest_user_strategy ON backtest_records(user_id, strategy_name);
```

## 4. API设计

### 4.1 API架构

**RESTful API设计原则：**
- 资源导向：每个URL代表一个资源
- 统一接口：使用标准HTTP方法
- 无状态：每个请求包含所有必要信息
- 分层系统：客户端无需关心中间层

**API版本管理：**
```
/api/v1/...
```

### 4.2 核心API端点

**用户认证**
```
POST   /api/v1/auth/register          # 用户注册
POST   /api/v1/auth/login             # 用户登录
POST   /api/v1/auth/logout            # 用户登出
POST   /api/v1/auth/refresh           # 刷新token
GET    /api/v1/auth/me                # 获取当前用户信息
```

**账户管理**
```
GET    /api/v1/accounts               # 获取账户列表
GET    /api/v1/accounts/{market}      # 获取指定市场账户
POST   /api/v1/accounts               # 创建市场账户
PUT    /api/v1/accounts/{id}          # 更新账户信息
GET    /api/v1/accounts/{id}/balance  # 获取账户余额
```

**交易操作**
```
POST   /api/v1/orders                 # 创建订单
GET    /api/v1/orders                 # 获取订单列表
GET    /api/v1/orders/{id}            # 获取订单详情
PUT    /api/v1/orders/{id}            # 更新订单
DELETE /api/v1/orders/{id}            # 取消订单
POST   /api/v1/orders/{id}/execute    # 执行订单（模拟撮合）
```

**持仓管理**
```
GET    /api/v1/positions              # 获取所有持仓
GET    /api/v1/positions/{market}     # 获取指定市场持仓
GET    /api/v1/positions/{id}         # 获取持仓详情
PUT    /api/v1/positions/{id}         # 更新持仓信息
```

**交易记录**
```
GET    /api/v1/trades                 # 获取交易记录
GET    /api/v1/trades/{id}            # 获取交易详情
GET    /api/v1/trades/statistics      # 获取交易统计
```

**股票数据**
```
GET    /api/v1/stocks/search          # 搜索股票
GET    /api/v1/stocks/{market}/{code}/quote      # 实时行情
GET    /api/v1/stocks/{market}/{code}/history    # 历史数据
GET    /api/v1/stocks/{market}/{code}/kline      # K线数据
GET    /api/v1/stocks/{market}/{code}/depth      # 盘口数据
```

**策略管理**
```
POST   /api/v1/strategies             # 创建策略
GET    /api/v1/strategies             # 获取策略列表
GET    /api/v1/strategies/{id}        # 获取策略详情
PUT    /api/v1/strategies/{id}        # 更新策略
DELETE /api/v1/strategies/{id}        # 删除策略
POST   /api/v1/strategies/{id}/enable # 启用策略
POST   /api/v1/strategies/{id}/disable # 禁用策略
```

**回测系统**
```
POST   /api/v1/backtest               # 创建回测任务
GET    /api/v1/backtest               # 获取回测列表
GET    /api/v1/backtest/{id}          # 获取回测详情
GET    /api/v1/backtest/{id}/results  # 获取回测结果
DELETE /api/v1/backtest/{id}          # 删除回测
```

**交易心理分析**
```
GET    /api/v1/psychology/analysis    # 获取心理分析
GET    /api/v1/psychology/patterns    # 获取行为模式
GET    /api/v1/psychology/recommendations # 获取改进建议
POST   /api/v1/psychology/assessment  # 提交心理评估
```

### 4.3 响应格式

**成功响应**
```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-06-02T10:30:00Z",
  "request_id": "req_123456789"
}
```

**错误响应**
```json
{
  "code": 400,
  "message": "Invalid request",
  "errors": [
    {
      "field": "quantity",
      "message": "必须是100的整数倍"
    }
  ],
  "timestamp": "2026-06-02T10:30:00Z",
  "request_id": "req_123456789"
}
```

**分页响应**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

### 4.4 认证和授权

**JWT Token认证：**
- Access Token：有效期2小时
- Refresh Token：有效期7天
- 支持多设备登录

**权限控制：**
- 基于角色的访问控制（RBAC）
- 资源级别的权限控制
- API限流保护

## 5. 交易规则与高级订单类型

### 5.1 多市场交易规则

**A股市场：**
```typescript
const CN_RULES = {
  market: 'CN',
  currency: 'CNY',
  tradingHours: [
    { start: '09:30', end: '11:30' },
    { start: '13:00', end: '15:00' },
  ],
  callAuction: [
    { start: '09:15', end: '09:25' },
    { start: '14:57', end: '15:00' },
  ],
  priceLimit: {
    normal: { up: 0.10, down: -0.10 },      // ±10%
    star: { up: 0.20, down: -0.20 },         // 科创板 ±20%
    gem: { up: 0.20, down: -0.20 },          // 创业板 ±20%
    st: { up: 0.05, down: -0.05 },           // ST股 ±5%
  },
  lotSize: 100,                               // 最小交易单位
  tPlusN: 1,                                  // T+1交易制度
  commission: {
    min: 5,                                   // 最低佣金
    rate: 0.00025,                            // 佣金费率 0.025%
    stampDuty: 0.001,                         // 印花税 0.1% (卖出)
    transferFee: 0.00001,                     // 过户费 0.001%
  },
};
```

**港股市场：**
```typescript
const HK_RULES = {
  market: 'HK',
  currency: 'HKD',
  tradingHours: [
    { start: '09:30', end: '12:00' },
    { start: '13:00', end: '16:00' },
  ],
  callAuction: [
    { start: '09:00', end: '09:30' },
  ],
  priceLimit: null,                           // 无涨跌停限制
  lotSize: {                                  // 每手股数（按股票不同）
    '00700': 100,                             // 腾讯
    '09988': 100,                             // 阿里
    default: 1000,
  },
  tPlusN: 0,                                  // T+0交易制度
  commission: {
    min: 50,                                  // 最低佣金
    rate: 0.0003,                             // 佣金费率 0.03%
    stampDuty: 0.0013,                        // 印花税 0.13%
    tradingFee: 0.00005,                      // 交易费 0.005%
    sfc: 0.000027,                            // 证监会征费 0.0027%
  },
};
```

**美股市场：**
```typescript
const US_RULES = {
  market: 'US',
  currency: 'USD',
  tradingHours: [
    { start: '09:30', end: '16:00' },        // 美东时间
  ],
  preMarket: { start: '04:00', end: '09:30' },
  afterHours: { start: '16:00', end: '20:00' },
  priceLimit: null,                           // 无涨跌停限制
  lotSize: 1,                                 // 最小交易单位1股
  tPlusN: 0,                                  // T+0交易制度
  commission: {
    rate: 0,                                  // 零佣金
    sec: 0.0000278,                           // SEC费
    taf: 0.000166,                            // TAF费
  },
};
```

### 5.2 高级订单类型

**限价单 (Limit Order)**
```typescript
interface LimitOrder {
  type: 'LIMIT';
  price: number;           // 指定价格
  quantity: number;        // 数量
  timeInForce: 'GTC' | 'IOC' | 'FOK' | 'DAY';
}
```

**市价单 (Market Order)**
```typescript
interface MarketOrder {
  type: 'MARKET';
  quantity: number;        // 数量
  slippage?: number;       // 滑点容忍度 (默认0.5%)
}
```

**止损单 (Stop Loss Order)**
```typescript
interface StopLossOrder {
  type: 'STOP_LOSS';
  stopPrice: number;       // 触发价格
  quantity: number;        // 数量
  timeInForce: 'GTC' | 'DAY';
}
```

**止盈单 (Take Profit Order)**
```typescript
interface TakeProfitOrder {
  type: 'TAKE_PROFIT';
  targetPrice: number;     // 目标价格
  quantity: number;        // 数量
  timeInForce: 'GTC' | 'DAY';
}
```

**止损止盈单 (OCO - One Cancels Other)**
```typescript
interface OCOOrder {
  type: 'OCO';
  stopPrice: number;       // 止损触发价
  targetPrice: number;     // 止盈目标价
  quantity: number;        // 数量
}
```

**条件单 (Conditional Order)**
```typescript
interface ConditionalOrder {
  type: 'CONDITIONAL';
  condition: {
    field: 'price' | 'volume' | 'time';
    operator: '>' | '<' | '>=' | '<=' | '==';
    value: number | string;
  };
  action: {
    orderType: 'LIMIT' | 'MARKET';
    price?: number;
    quantity: number;
  };
}
```

### 5.3 订单撮合引擎

**撮合逻辑：**
```python
class MatchingEngine:
    """撮合引擎"""
    
    def match(self, order: Order, market_data: MarketData) -> TradeResult:
        """
        撮合订单
        
        Args:
            order: 待撮合订单
            market_data: 市场数据
            
        Returns:
            撮合结果
        """
        # 1. 检查订单状态
        if order.status != 'PENDING':
            return TradeResult(success=False, message="订单状态错误")
        
        # 2. 检查交易时间
        if not self._is_trading_time(order.market):
            return TradeResult(success=False, message="非交易时间")
        
        # 3. 检查涨跌停限制
        if not self._check_price_limit(order, market_data):
            return TradeResult(success=False, message="价格超出涨跌停限制")
        
        # 4. 根据订单类型执行撮合
        if order.order_type == 'MARKET':
            return self._match_market_order(order, market_data)
        elif order.order_type == 'LIMIT':
            return self._match_limit_order(order, market_data)
        elif order.order_type == 'STOP_LOSS':
            return self._match_stop_loss_order(order, market_data)
        elif order.order_type == 'TAKE_PROFIT':
            return self._match_take_profit_order(order, market_data)
        elif order.order_type == 'CONDITIONAL':
            return self._match_conditional_order(order, market_data)
        
        return TradeResult(success=False, message="不支持的订单类型")
    
    def _match_market_order(self, order: Order, market_data: MarketData) -> TradeResult:
        """撮合市价单"""
        # 获取最优价格
        if order.direction == 'BUY':
            price = market_data.ask_price  # 卖一价
        else:
            price = market_data.bid_price  # 买一价
        
        # 应用滑点
        slippage = order.slippage or 0.005
        if order.direction == 'BUY':
            price *= (1 + slippage)
        else:
            price *= (1 - slippage)
        
        return self._execute_trade(order, price)
    
    def _match_limit_order(self, order: Order, market_data: MarketData) -> TradeResult:
        """撮合限价单"""
        if order.direction == 'BUY':
            # 买入限价单：当前卖一价 <= 限价
            if market_data.ask_price <= order.price:
                return self._execute_trade(order, market_data.ask_price)
        else:
            # 卖出限价单：当前买一价 >= 限价
            if market_data.bid_price >= order.price:
                return self._execute_trade(order, market_data.bid_price)
        
        return TradeResult(success=False, message="限价单未达到成交条件")
```

## 6. 前端界面设计

### 6.1 设计理念

**数据密集型 + 移动优先：**
- 参考Bloomberg Terminal的数据密度
- 响应式设计，适配各种屏幕尺寸
- 深色主题，减少视觉疲劳
- 信息层次清晰，重点突出

### 6.2 页面结构

**主导航：**
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  交易终端  数据分析  策略管理  系统设置    [用户] │
└─────────────────────────────────────────────────────────────┘
```

**交易终端页面（核心页面）：**
```
┌─────────────────────────────────────────────────────────────┐
│  市场选择: [A股 ▼] [港股 ▼] [美股 ▼]  搜索: [________] 🔍 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  K线图区域 (TradingView)                            │   │
│  │  - 多周期切换 (1分/5分/15分/30分/60分/日/周/月)    │   │
│  │  - 技术指标叠加 (MA/MACD/RSI/KDJ/BOLL)             │   │
│  │  - 画线工具                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ 盘口数据    │ │ 订单簿      │ │ 交易表单            │   │
│  │ 买1-5       │ │ 限价单      │ │ 买入/卖出           │   │
│  │ 卖1-5       │ │ 市价单      │ │ 价格/数量           │   │
│  │             │ │ 止损单      │ │ 高级选项            │   │
│  │             │ │ 止盈单      │ │ [下单]              │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  标签页: [持仓] [订单] [交易记录] [策略]            │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  数据表格                                   │   │   │
│  │  │  - 可排序列                                 │   │   │
│  │  │  - 可筛选                                   │   │   │
│  │  │  - 实时更新                                 │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 核心组件设计

**K线图组件：**
- 基于TradingView Lightweight Charts
- 支持多周期切换
- 技术指标叠加
- 画线工具
- 响应式布局

**订单表单组件：**
- 订单类型选择（限价/市价/止损/止盈）
- 价格输入（支持微调）
- 数量输入（支持100股整数倍）
- 高级选项（有效期、条件单）
- 实时预览订单金额

**持仓列表组件：**
- 实时更新盈亏
- 多市场分组
- 快速卖出按钮
- 盈亏高亮显示

**数据表格组件：**
- 虚拟滚动（大数据量）
- 列排序和筛选
- 实时数据更新
- 导出功能

### 6.4 响应式设计

**断点设计：**
```typescript
const breakpoints = {
  xs: '480px',    // 手机竖屏
  sm: '576px',    // 手机横屏
  md: '768px',    // 平板竖屏
  lg: '992px',    // 平板横屏
  xl: '1200px',   // 桌面
  xxl: '1600px',  // 大桌面
};
```

**移动端适配：**
- 底部导航栏
- 手势操作（滑动切换）
- 简化信息展示
- 触摸友好的控件

### 6.5 主题设计

**深色主题（默认）：**
```typescript
const darkTheme = {
  background: '#1a1a1a',
  surface: '#2d2d2d',
  primary: '#1890ff',
  success: '#52c41a',
  error: '#ff4d4f',
  warning: '#faad14',
  text: '#ffffff',
  textSecondary: '#8c8c8c',
};
```

**浅色主题：**
```typescript
const lightTheme = {
  background: '#f5f5f5',
  surface: '#ffffff',
  primary: '#1890ff',
  success: '#52c41a',
  error: '#ff4d4f',
  warning: '#faad14',
  text: '#000000',
  textSecondary: '#8c8c8c',
};
```

### 6.6 实时数据流

**WebSocket连接：**
- 实时行情推送
- 订单状态更新
- 持仓盈亏更新
- 系统通知

**数据更新策略：**
- 行情数据：每秒更新
- 持仓数据：每5秒更新
- 订单状态：实时推送
- 图表数据：按需加载

## 7. 回测系统

### 7.1 回测引擎架构

```
┌─────────────────────────────────────────────────────────────┐
│                    回测系统架构                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 数据加载器 │  │ 策略执行器 │  │ 结果分析器 │         │
│  │ DataLoader │  │ Strategy   │  │ Analyzer   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                 ┌─────────────┐                             │
│                 │ 回测引擎   │                             │
│                 │ Backtest   │                             │
│                 └──────┬──────┘                             │
│                        │                                    │
│           ┌────────────┼────────────┐                       │
│           ▼            ▼            ▼                       │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│     │ 模拟账户 │ │ 交易记录 │ │ 绩效统计 │                 │
│     │ Account  │ │ Trades   │ │ Stats    │                 │
│     └──────────┘ └──────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 回测引擎实现

**核心类设计：**
```python
class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.data_loader = DataLoader()
        self.strategy = None
        self.account = SimulatedAccount(config.initial_capital)
        self.trade_history = []
        self.equity_curve = []
    
    def set_strategy(self, strategy: BaseStrategy):
        """设置策略"""
        self.strategy = strategy
    
    async def run(self, start_date: date, end_date: date) -> BacktestResult:
        """
        运行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果
        """
        # 1. 加载历史数据
        data = await self.data_loader.load(
            market=self.config.market,
            stock_codes=self.config.stock_codes,
            start_date=start_date,
            end_date=end_date
        )
        
        # 2. 初始化策略
        self.strategy.initialize(data)
        
        # 3. 遍历每个交易日
        for trading_day in data.trading_days:
            # 获取当日数据
            day_data = data.get_day_data(trading_day)
            
            # 生成交易信号
            signals = self.strategy.generate_signals(day_data)
            
            # 执行交易
            for signal in signals:
                trade_result = self._execute_signal(signal, day_data)
                if trade_result.success:
                    self.trade_history.append(trade_result.trade)
            
            # 更新持仓价格
            self.account.update_positions(day_data.close_prices)
            
            # 记录权益曲线
            self.equity_curve.append({
                'date': trading_day,
                'equity': self.account.total_equity,
                'cash': self.account.cash,
                'positions_value': self.account.positions_value
            })
        
        # 4. 生成回测结果
        return self._generate_result()
    
    def _execute_signal(self, signal: Signal, day_data: DayData) -> TradeResult:
        """执行交易信号"""
        # 检查账户资金/持仓
        if signal.direction == 'BUY':
            if self.account.cash < signal.price * signal.quantity:
                return TradeResult(success=False, message="资金不足")
        else:
            position = self.account.get_position(signal.stock_code)
            if not position or position.quantity < signal.quantity:
                return TradeResult(success=False, message="持仓不足")
        
        # 模拟交易执行
        trade = Trade(
            stock_code=signal.stock_code,
            trade_type=signal.direction,
            price=signal.price,
            quantity=signal.quantity,
            trade_time=day_data.date,
            strategy_tag=signal.strategy_name
        )
        
        # 更新账户
        self.account.execute_trade(trade)
        
        return TradeResult(success=True, trade=trade)
```

### 7.3 绩效指标计算

**核心指标：**
```python
class PerformanceAnalyzer:
    """绩效分析器"""
    
    def calculate_metrics(self, equity_curve: List[Dict], trades: List[Trade]) -> PerformanceMetrics:
        """
        计算绩效指标
        
        Args:
            equity_curve: 权益曲线
            trades: 交易记录
            
        Returns:
            绩效指标
        """
        returns = self._calculate_returns(equity_curve)
        
        return PerformanceMetrics(
            # 收益指标
            total_return=self._calculate_total_return(equity_curve),
            annual_return=self._calculate_annual_return(equity_curve),
            monthly_returns=self._calculate_monthly_returns(equity_curve),
            
            # 风险指标
            max_drawdown=self._calculate_max_drawdown(equity_curve),
            max_drawdown_duration=self._calculate_max_drawdown_duration(equity_curve),
            volatility=self._calculate_volatility(returns),
            downside_volatility=self._calculate_downside_volatility(returns),
            
            # 风险调整收益
            sharpe_ratio=self._calculate_sharpe_ratio(returns),
            sortino_ratio=self._calculate_sortino_ratio(returns),
            calmar_ratio=self._calculate_calmar_ratio(equity_curve),
            
            # 交易指标
            total_trades=len(trades),
            winning_trades=len([t for t in trades if t.pnl > 0]),
            losing_trades=len([t for t in trades if t.pnl < 0]),
            win_rate=self._calculate_win_rate(trades),
            profit_factor=self._calculate_profit_factor(trades),
            avg_win=self._calculate_avg_win(trades),
            avg_loss=self._calculate_avg_loss(trades),
            max_consecutive_wins=self._calculate_max_consecutive_wins(trades),
            max_consecutive_losses=self._calculate_max_consecutive_losses(trades),
            
            # 时间指标
            avg_holding_period=self._calculate_avg_holding_period(trades),
            avg_trades_per_month=self._calculate_avg_trades_per_month(trades),
        )
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """计算最大回撤"""
        peak = equity_curve[0]['equity']
        max_dd = 0
        
        for point in equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            
            dd = (peak - point['equity']) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        if not returns:
            return 0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
        
        # 年化处理
        annual_return = avg_return * 252
        annual_std = std_return * np.sqrt(252)
        
        return (annual_return - risk_free_rate) / annual_std
```

### 7.4 回测报告

**报告内容：**
```python
@dataclass
class BacktestReport:
    """回测报告"""
    summary: str                           # 概述
    performance_metrics: PerformanceMetrics # 绩效指标
    equity_curve: List[Dict]              # 权益曲线
    monthly_returns: List[Dict]           # 月度收益
    drawdown_chart: List[Dict]            # 回撤图表
    trade_analysis: TradeAnalysis         # 交易分析
    strategy_analysis: StrategyAnalysis   # 策略分析
    recommendations: List[str]            # 改进建议
```

**可视化图表：**
1. 权益曲线图
2. 月度收益热力图
3. 回撤图
4. 交易分布图
5. 持仓时间分布图

### 7.5 策略优化

**参数优化：**
```python
class StrategyOptimizer:
    """策略优化器"""
    
    def optimize(
        self,
        strategy_class: type,
        param_grid: Dict[str, List],
        data: MarketData,
        metric: str = 'sharpe_ratio'
    ) -> OptimizationResult:
        """
        网格搜索优化策略参数
        
        Args:
            strategy_class: 策略类
            param_grid: 参数网格
            data: 历史数据
            metric: 优化目标指标
            
        Returns:
            优化结果
        """
        results = []
        
        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_grid)
        
        for params in param_combinations:
            # 创建策略实例
            strategy = strategy_class(**params)
            
            # 运行回测
            engine = BacktestEngine(self.config)
            engine.set_strategy(strategy)
            result = await engine.run(data.start_date, data.end_date)
            
            results.append({
                'params': params,
                'result': result
            })
        
        # 按目标指标排序
        results.sort(key=lambda x: x['result'].performance_metrics[metric], reverse=True)
        
        return OptimizationResult(
            best_params=results[0]['params'],
            best_result=results[0]['result'],
            all_results=results
        )
```

## 8. 交易心理分析

### 8.1 分析维度

**情绪分析：**
- 贪婪指标：追涨行为、过度持仓
- 恐惧指标：恐慌性卖出、过早止损
- 情绪周期：情绪波动与交易行为关联

**纪律分析：**
- 计划执行率：实际交易与计划的一致性
- 风险遵守度：止损止盈执行情况
- 仓位控制：仓位管理的合理性

**行为模式识别：**
- 追涨杀跌：高位买入、低位卖出
- 频繁交易：过度交易倾向
- 重仓单只：集中持仓风险
- 补仓摊薄：下跌时持续买入
- 过早止盈：盈利时过早卖出

### 8.2 分析引擎实现

**核心类设计：**
```python
class TradingPsychologyAnalyzer:
    """交易心理分析器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze(self, user_id: int, period_days: int = 30) -> PsychologyReport:
        """
        分析交易心理
        
        Args:
            user_id: 用户ID
            period_days: 分析周期（天）
            
        Returns:
            心理分析报告
        """
        # 获取交易数据
        trades = self._get_trades(user_id, period_days)
        positions = self._get_positions(user_id)
        orders = self._get_orders(user_id, period_days)
        
        # 计算各项指标
        emotion_score = self._analyze_emotion(trades, positions)
        discipline_score = self._analyze_discipline(trades, orders)
        patterns = self._identify_patterns(trades, positions)
        risk_adherence = self._analyze_risk_adherence(trades, orders)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            emotion_score, discipline_score, patterns, risk_adherence
        )
        
        return PsychologyReport(
            user_id=user_id,
            analysis_date=date.today(),
            emotion_score=emotion_score,
            discipline_score=discipline_score,
            risk_adherence=risk_adherence,
            patterns=patterns,
            recommendations=recommendations
        )
    
    def _analyze_emotion(self, trades: List[Trade], positions: List[Position]) -> float:
        """
        分析情绪得分
        
        Returns:
            情绪得分 0-100 (越高越理性)
        """
        score = 100.0
        
        # 检查追涨行为
        chase_buy_count = sum(1 for t in trades if self._is_chase_buy(t))
        if chase_buy_count > 0:
            score -= min(20, chase_buy_count * 5)
        
        # 检查恐慌性卖出
        panic_sell_count = sum(1 for t in trades if self._is_panic_sell(t))
        if panic_sell_count > 0:
            score -= min(20, panic_sell_count * 5)
        
        # 检查情绪周期
        emotion_cycle = self._detect_emotion_cycle(trades)
        if emotion_cycle:
            score -= 10
        
        return max(0, score)
    
    def _analyze_discipline(self, trades: List[Trade], orders: List[Order]) -> float:
        """
        分析纪律得分
        
        Returns:
            纪律得分 0-100 (越高越有纪律)
        """
        score = 100.0
        
        # 检查计划执行率
        plan_execution_rate = self._calculate_plan_execution_rate(orders)
        score *= plan_execution_rate
        
        # 检查止损执行率
        stop_loss_execution_rate = self._calculate_stop_loss_execution_rate(orders)
        score *= stop_loss_execution_rate
        
        # 检查交易频率
        trade_frequency = self._calculate_trade_frequency(trades)
        if trade_frequency > 10:  # 每日超过10笔
            score -= min(30, (trade_frequency - 10) * 3)
        
        return max(0, score)
    
    def _identify_patterns(self, trades: List[Trade], positions: List[Position]) -> List[BehaviorPattern]:
        """
        识别行为模式
        
        Returns:
            行为模式列表
        """
        patterns = []
        
        # 检查追涨杀跌
        if self._detect_chase_pattern(trades):
            patterns.append(BehaviorPattern(
                name="追涨杀跌",
                description="在股价高位买入，低位卖出",
                severity="HIGH",
                frequency=self._calculate_pattern_frequency(trades, "chase"),
                impact="通常导致亏损",
                suggestion="避免追涨，设置合理买入价位"
            ))
        
        # 检查频繁交易
        if self._detect_frequent_trading(trades):
            patterns.append(BehaviorPattern(
                name="频繁交易",
                description="交易频率过高，增加交易成本",
                severity="MEDIUM",
                frequency=self._calculate_pattern_frequency(trades, "frequent"),
                impact="增加交易成本，降低收益",
                suggestion="减少交易频率，提高交易质量"
            ))
        
        # 检查重仓单只
        if self._detect_concentrated_position(positions):
            patterns.append(BehaviorPattern(
                name="重仓单只",
                description="单只股票仓位过重，风险集中",
                severity="HIGH",
                frequency=1.0,
                impact="风险集中，可能造成重大损失",
                suggestion="分散投资，单只股票仓位不超过20%"
            ))
        
        return patterns
```

### 8.3 改进建议生成

**智能建议系统：**
```python
class RecommendationEngine:
    """建议引擎"""
    
    def generate(self, report: PsychologyReport) -> List[Recommendation]:
        """
        生成改进建议
        
        Args:
            report: 心理分析报告
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 情绪相关建议
        if report.emotion_score < 60:
            recommendations.append(Recommendation(
                category="情绪管理",
                priority="HIGH",
                title="控制情绪化交易",
                description="您的情绪得分较低，建议采取以下措施：",
                actions=[
                    "设置每日最大亏损限额，达到后停止交易",
                    "避免在市场剧烈波动时做决策",
                    "使用条件单代替手动交易",
                    "记录每笔交易的情绪状态"
                ]
            ))
        
        # 纪律相关建议
        if report.discipline_score < 60:
            recommendations.append(Recommendation(
                category="交易纪律",
                priority="HIGH",
                title="提高交易纪律",
                description="您的纪律得分较低，建议采取以下措施：",
                actions=[
                    "制定详细的交易计划并严格执行",
                    "设置自动止损止盈",
                    "限制每日交易次数",
                    "定期复盘交易记录"
                ]
            ))
        
        # 行为模式相关建议
        for pattern in report.patterns:
            if pattern.severity == "HIGH":
                recommendations.append(Recommendation(
                    category="行为纠正",
                    priority="MEDIUM",
                    title=f"纠正{pattern.name}行为",
                    description=pattern.description,
                    actions=[pattern.suggestion]
                ))
        
        return recommendations
```

## 9. 实施计划

### 9.1 开发阶段

**阶段一：基础架构（第1-2周）**
- 项目结构重构
- 数据库迁移
- 基础API框架
- 用户认证系统

**阶段二：交易引擎（第3-4周）**
- 多市场交易规则
- 高级订单类型
- 撮合引擎
- 风险控制

**阶段三：数据服务（第5-6周）**
- 多市场数据源接入
- 实时行情推送
- 历史数据存储
- 数据清洗标准化

**阶段四：前端界面（第7-8周）**
- 交易终端页面
- K线图组件
- 订单表单
- 持仓管理

**阶段五：分析系统（第9-10周）**
- 回测引擎
- 绩效分析
- 交易心理分析
- 报告生成

**阶段六：自动交易（第11-12周）**
- 策略引擎
- 执行引擎
- 风控系统
- 监控面板

### 9.2 里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1 | 第2周末 | 基础架构完成，用户认证可用 |
| M2 | 第4周末 | 交易引擎完成，支持多市场交易 |
| M3 | 第6周末 | 数据服务完成，实时行情可用 |
| M4 | 第8周末 | 前端界面完成，交易终端可用 |
| M5 | 第10周末 | 分析系统完成，回测和心理分析可用 |
| M6 | 第12周末 | 自动交易完成，系统完整交付 |

### 9.3 风险与应对

**技术风险：**
- 多市场数据源不稳定 → 多数据源备份，异常重试
- 实时数据延迟高 → WebSocket优化，数据压缩
- 回测性能差 → 数据缓存，并行计算

**业务风险：**
- 交易规则变化 → 规则配置化，定期更新
- 用户需求变更 → 迭代开发，快速响应
- 市场异常情况 → 异常检测，自动暂停

## 10. 后续扩展

### 10.1 功能扩展
- 社交交易功能
- 排行榜和竞赛
- 移动端原生应用
- 多语言支持

### 10.2 技术扩展
- 微服务架构演进
- 实时数据流处理
- 云端部署
- 机器学习优化

---

**文档版本**: v1.0  
**创建日期**: 2026-06-02  
**最后更新**: 2026-06-02
