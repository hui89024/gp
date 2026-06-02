# 股票交易自动化系统

一个功能完整的股票交易自动化系统，支持模拟炒股、股票预测、自动交易、复盘分析、历史回测和风控熔断。

## 功能特性

### 核心功能
- **模拟炒股** - 虚拟资金交易练习，支持T+1、涨跌停限制
- **股票预测** - LSTM深度学习模型预测股价走势
- **自动交易** - 策略引擎自动执行交易（均线、RSI、预测信号）
- **复盘分析** - 交易记录分析、策略评估、行为分析

### 增强功能
- **历史回测** - 策略验证，计算收益率、最大回撤、夏普比率
- **风控熔断** - 独立风控系统，防止程序失控
- **告警系统** - 钉钉/邮件通知，异常及时告警

## 技术栈

**后端:**
- Python 3.11+
- FastAPI
- SQLAlchemy + PostgreSQL
- AKShare（股票数据）
- PyTorch（LSTM模型）
- NumPy + Pandas

**前端:**
- React 18 + TypeScript
- Ant Design
- ECharts（K线图）
- Zustand（状态管理）

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

| 页面 | 地址 | 说明 |
|------|------|------|
| 首页 | http://localhost:5173/ | 仪表盘 |
| 交易 | http://localhost:5173/trade | 模拟交易 |
| 预测 | http://localhost:5173/prediction | 股票预测 |
| 复盘 | http://localhost:5173/review | 交易复盘 |
| 自动交易 | http://localhost:5173/auto-trading | 策略管理 |
| API文档 | http://localhost:8000/docs | Swagger UI |

## 项目结构

```
gp/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic Schema
│   │   ├── services/      # 业务服务
│   │   ├── strategies/    # 交易策略
│   │   └── ml/            # 机器学习模型
│   ├── tests/             # 测试文件
│   └── alembic/           # 数据库迁移
├── frontend/
│   ├── src/
│   │   ├── components/    # UI组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API服务
│   │   └── stores/        # 状态管理
├── docs/                  # 文档
├── docker-compose.yml
└── README.md
```

## API端点

### 账户管理
- `POST /api/account/users` - 创建用户
- `GET /api/account/users/{id}` - 获取用户
- `GET /api/account/users/{id}/overview` - 账户概览

### 交易
- `POST /api/trades/buy` - 买入
- `POST /api/trades/sell` - 卖出
- `GET /api/trades/history` - 交易历史
- `GET /api/trades/positions` - 持仓

### 股票数据
- `GET /api/stocks/{code}/quote` - 实时行情
- `GET /api/stocks/{code}/history` - 历史数据
- `GET /api/stocks/{code}/kline` - K线数据

### 预测
- `POST /api/predictions/train/{code}` - 训练模型
- `GET /api/predictions/signal/{code}` - 预测信号

### 复盘
- `GET /api/reviews/daily/{user_id}` - 每日复盘
- `GET /api/reviews/weekly/{user_id}` - 每周复盘
- `GET /api/reviews/comprehensive/{user_id}` - 综合报告

### 自动交易
- `POST /api/auto-trading/strategies` - 创建策略
- `POST /api/auto-trading/tasks` - 创建任务
- `POST /api/auto-trading/tasks/{id}/start` - 启动任务

### 回测
- `POST /api/backtest/run` - 运行回测
- `GET /api/backtest/records` - 回测记录

### 风控
- `GET /api/risk-control/circuit-breaker/status` - 熔断状态
- `POST /api/risk-control/circuit-breaker/reset` - 重置熔断
- `GET /api/risk-control/alerts/records` - 告警记录

## 内置策略

| 策略 | 类型 | 说明 |
|------|------|------|
| PredictionStrategy | 预测 | LSTM模型预测信号 |
| MAStrategy | 技术 | 均线金叉/死叉 |
| RSIStrategy | 技术 | RSI超买/超卖 |

## 风控规则

| 规则 | 默认值 | 说明 |
|------|--------|------|
| 止损 | -5% | 单笔最大亏损 |
| 止盈 | +10% | 单笔最大盈利 |
| 仓位 | 20% | 单只股票最大仓位 |
| 每日交易 | 10次 | 每日最大交易次数 |
| 每日亏损 | 5万 | 每日最大亏损金额 |

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

- [x] 股票预测功能
- [x] 自动交易策略
- [x] 复盘分析系统
- [x] 历史回测系统
- [x] 风控熔断系统
- [ ] 真实券商对接
- [ ] 移动端适配
- [ ] 多账户支持

---

**版本**: v3.0.0  
**最后更新**: 2026-06-02
