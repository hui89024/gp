# 股票交易自动化系统设计文档

## 1. 项目概述

### 1.1 项目目标

构建一个实用的股票交易辅助工具，包含四大核心功能：
- 股票预测：基于深度学习预测股价走势
- 模拟炒股：虚拟资金交易练习
- 自动炒股：自动化交易执行（后期实现）
- 股票复盘：交易历史回顾与分析

### 1.2 技术选型

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI |
| 前端框架 | React + TypeScript |
| UI组件库 | Ant Design |
| 图表库 | ECharts |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 任务队列 | Celery |
| 机器学习 | PyTorch |

### 1.3 数据源

使用免费API获取股票数据：
- AKShare：A股行情、财务数据
- Tushare：补充数据源

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────┐
│           前端 (React + TypeScript)       │
│  - 模拟交易界面                           │
│  - 预测结果展示                           │
│  - 复盘分析面板                           │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         后端 (FastAPI + Python)          │
│  - 交易引擎                              │
│  - 预测服务                              │
│  - 复盘分析                              │
│  - 数据服务                              │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           数据层                          │
│  - PostgreSQL (交易记录、用户数据)        │
│  - Redis (缓存、实时数据)                │
│  - 免费API (股票行情)                    │
└─────────────────────────────────────────┘
```

### 2.2 模块职责

**交易引擎**
- 虚拟账户管理（初始资金、充值、提现）
- 订单系统（限价单、市价单）
- 撮合引擎（模拟真实交易规则）
- 持仓管理（股票、成本、盈亏）

**预测服务**
- 模型训练与保存
- 实时预测与信号生成
- 模型评估与更新

**复盘分析**
- 交易记录分析
- 策略表现评估
- 行为模式识别

**数据服务**
- 数据获取与清洗
- 实时行情推送
- 历史数据存储

## 3. 模块详细设计

### 3.1 交易引擎

**交易规则**
- T+1交易制度（当天买入次日可卖）
- 涨跌停限制（±10%，创业板±20%）
- 交易时间（9:30-11:30, 13:00-15:00）
- 手续费模拟（佣金0.025%，印花税0.1%，过户费0.001%）

**订单类型**
- 限价单：指定价格买入/卖出
- 市价单：按当前最优价格成交

**撮合逻辑**
1. 检查账户资金/持仓
2. 验证交易规则（T+1、涨跌停）
3. 模拟撮合（考虑滑点）
4. 更新账户和持仓

### 3.2 预测服务

**模型架构**

LSTM模型：
- 输入：历史价格、成交量、技术指标
- 输出：未来1-5天涨跌概率
- 结构：2层LSTM + 全连接层

Transformer模型：
- 输入：多维时间序列
- 输出：价格区间预测
- 结构：标准Transformer编码器

集成策略：
- 加权平均：根据模型历史表现分配权重
- 投票机制：多模型投票决定最终信号

**预测输出**
- 涨跌概率（未来1-5天）
- 目标价区间（±5%）
- 买入/卖出信号（强/中/弱）

### 3.3 复盘分析

**分析维度**

交易记录分析：
- 每笔交易详情（时间、价格、数量）
- 盈亏统计（总盈亏、单笔盈亏）
- 胜率分析（盈利交易占比）

策略表现评估：
- 收益率（年化、累计）
- 夏普比率（风险调整收益）
- 最大回撤（最大亏损幅度）

行为分析：
- 持仓时间分布
- 情绪指标（追涨杀跌识别）
- 常见错误识别（频繁交易、重仓单只）

### 3.4 数据服务

**数据源配置**

AKShare：
- 实时行情：stock_zh_a_spot_em()
- 历史数据：stock_zh_a_hist()
- 财务数据：stock_financial_analysis_indicator()

Tushare：
- 补充数据源
- 备用方案

**数据处理流程**
1. 数据获取：定时从API拉取
2. 数据清洗：异常值处理、缺失值填充
3. 数据存储：写入PostgreSQL
4. 数据缓存：实时数据存入Redis

## 4. 数据模型

### 4.1 核心数据表

**用户账户表 (users)**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    initial_capital DECIMAL(15,2) DEFAULT 1000000,
    current_capital DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**持仓表 (positions)**
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    quantity INTEGER NOT NULL,
    avg_cost DECIMAL(10,2),
    current_price DECIMAL(10,2),
    unrealized_pnl DECIMAL(15,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**交易记录表 (trades)**
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stock_code VARCHAR(10) NOT NULL,
    trade_type VARCHAR(4) NOT NULL, -- BUY/SELL
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    commission DECIMAL(10,2),
    trade_time TIMESTAMP NOT NULL,
    strategy_tag VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**预测记录表 (predictions)**
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    model_type VARCHAR(20) NOT NULL, -- LSTM/Transformer/Ensemble
    predicted_direction VARCHAR(4), -- UP/DOWN
    confidence DECIMAL(5,4),
    actual_result VARCHAR(4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**复盘记录表 (reviews)**
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    review_date DATE NOT NULL,
    total_pnl DECIMAL(15,2),
    win_rate DECIMAL(5,4),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 数据关系

```
users (1) ──→ (N) positions
users (1) ──→ (N) trades
users (1) ──→ (N) reviews
predictions (1) ──→ (N) trades (可选关联)
```

## 5. API设计

### 5.1 交易模块

```
POST   /api/trades/buy      # 买入订单
POST   /api/trades/sell     # 卖出订单
GET    /api/trades/history  # 交易历史
GET    /api/positions       # 当前持仓
GET    /api/account/balance # 账户余额
```

### 5.2 预测模块

```
GET    /api/predictions/{stock_code}  # 获取预测
POST   /api/predictions/train         # 触发模型训练
GET    /api/predictions/signals       # 获取交易信号
```

### 5.3 复盘模块

```
GET    /api/reviews/daily    # 每日复盘
GET    /api/reviews/weekly   # 周度复盘
GET    /api/reviews/strategy # 策略分析
POST   /api/reviews/notes    # 添加复盘笔记
```

### 5.4 数据模块

```
GET    /api/stocks/{code}/quote      # 实时行情
GET    /api/stocks/{code}/history    # 历史数据
GET    /api/stocks/search            # 股票搜索
```

### 5.5 响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-06-01T10:30:00Z"
}
```

## 6. 前端界面设计

### 6.1 主要页面

**首页 - 交易仪表盘**
- 账户总览（总资产、今日盈亏）
- 持仓列表（实时刷新）
- 实时K线图
- 快捷操作按钮

**交易页面**
- 股票搜索
- 订单表单（价格、数量）
- 盘口数据
- 成交确认

**预测页面**
- 预测结果展示
- 信号强度指示
- 历史预测准确率

**复盘页面**
- 收益曲线图
- 策略表现对比
- 行为分析报告
- 复盘笔记

### 6.2 核心组件

- K线图组件：ECharts封装，支持技术指标叠加
- 订单表单组件：价格、数量输入，实时计算金额
- 持仓列表组件：实时刷新，盈亏高亮
- 复盘图表组件：收益曲线、胜率饼图、回撤图

## 7. 开发计划

### 7.1 MVP阶段（模拟炒股）

**第一周：项目搭建**
- 初始化项目结构
- 配置开发环境
- 搭建基础框架

**第二周：数据服务**
- 实现AKShare数据获取
- 数据清洗和存储
- 实时行情推送

**第三周：交易引擎**
- 实现账户管理
- 实现订单系统
- 实现撮合引擎

**第四周：前端界面**
- 实现交易界面
- 实现持仓展示
- 实现K线图

### 7.2 完整功能阶段

**第五周：预测服务**
- 实现LSTM模型
- 实现Transformer模型
- 实现集成策略

**第六周：复盘分析**
- 实现交易记录分析
- 实现策略评估
- 实现行为分析

**第七周：自动交易**
- 实现交易信号生成
- 实现自动下单
- 实现风险控制

**第八周：优化完善**
- 性能优化
- 用户体验改进
- 测试和修复

## 8. 风险与应对

### 8.1 技术风险

| 风险 | 应对措施 |
|------|----------|
| 数据源不稳定 | 多数据源备份，异常重试 |
| 模型预测不准 | 持续优化，人工审核 |
| 系统性能瓶颈 | 缓存优化，异步处理 |

### 8.2 业务风险

| 风险 | 应对措施 |
|------|----------|
| 用户过度依赖 | 风险提示，模拟环境 |
| 交易规则变化 | 灵活配置，定期更新 |

## 9. 后续扩展

### 9.1 功能扩展
- 多账户支持
- 社交功能（分享策略）
- 移动端适配

### 9.2 技术扩展
- 微服务架构
- 实时数据流处理
- 云端部署

---

**文档版本**: v1.0  
**创建日期**: 2026-06-01  
**最后更新**: 2026-06-01
