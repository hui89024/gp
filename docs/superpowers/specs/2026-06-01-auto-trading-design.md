# 自动炒股系统设计文档

## 1. 项目概述

### 1.1 项目目标

在现有股票交易系统基础上，增加自动炒股功能：
- 支持多种交易策略（预测信号、技术指标、规则引擎）
- 支持多种执行方式（定时轮询、实时监控、收盘后批量）
- 完善的风险控制机制
- 模拟资金和真实资金双模式

### 1.2 核心功能

1. **策略引擎** - 可插拔的策略架构，支持多种策略并行运行
2. **执行引擎** - 支持定时、实时、批量三种执行模式
3. **风控系统** - 止损止盈、仓位控制、交易频率、资金管理
4. **资金模式** - 模拟资金和真实资金双轨运行

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端界面                                │
│  - 策略管理页面                                              │
│  - 风控配置页面                                              │
│  - 自动交易监控面板                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端服务                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  策略引擎   │  │  执行引擎   │  │  风控系统   │         │
│  │  Strategy   │  │  Executor   │  │  RiskCtrl   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                 ┌─────────────┐                             │
│                 │  交易引擎   │                             │
│                 │  Trading    │                             │
│                 └──────┬──────┘                             │
│                        │                                    │
│           ┌────────────┼────────────┐                       │
│           ▼            ▼            ▼                       │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│     │模拟资金  │ │真实资金  │ │数据服务  │                 │
│     │SimFund   │ │RealFund  │ │DataSvc   │                 │
│     └──────────┘ └──────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

**策略引擎 (StrategyEngine)**
- 策略注册与管理
- 策略信号生成
- 多策略组合与冲突处理

**执行引擎 (ExecutionEngine)**
- 定时任务调度（APScheduler）
- 实时行情监控
- 批量任务处理

**风控系统 (RiskControl)**
- 止损止盈检查
- 仓位限制检查
- 交易频率限制
- 资金限额检查

**资金管理 (FundManager)**
- 模拟资金管理
- 真实资金接口（券商API）
- 资金模式切换

## 3. 模块详细设计

### 3.1 策略引擎

#### 3.1.1 策略接口

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Signal:
    stock_code: str
    stock_name: str
    direction: str  # BUY/SELL
    price: float
    quantity: int
    confidence: float
    strategy_name: str
    reason: str
    timestamp: datetime

class BaseStrategy(ABC):
    """策略基类"""
    
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @abstractmethod
    def generate_signals(self, stock_codes: List[str]) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            stock_codes: 监控的股票代码列表
        
        Returns:
            交易信号列表
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证策略配置是否有效"""
        pass
```

#### 3.1.2 内置策略

**1. 预测信号策略 (PredictionStrategy)**
- 使用LSTM模型预测结果
- 置信度超过阈值时触发信号
- 配置参数：置信度阈值、目标股票列表

**2. 均线策略 (MAStrategy)**
- 金叉（短期均线上穿长期均线）买入
- 死叉（短期均线下穿长期均线）卖出
- 配置参数：短期周期、长期周期

**3. RSI策略 (RSIStrategy)**
- RSI低于超卖阈值买入
- RSI高于超买阈值卖出
- 配置参数：RSI周期、超买阈值、超卖阈值

**4. 规则引擎策略 (RuleStrategy)**
- 用户自定义条件表达式
- 支持比较运算符（>, <, >=, <=, ==）
- 支持逻辑运算符（AND, OR）
- 配置参数：规则表达式

#### 3.1.3 策略管理

```python
class StrategyEngine:
    """策略引擎"""
    
    def __init__(self):
        self.strategies = {}
    
    def register(self, strategy: BaseStrategy):
        """注册策略"""
        self.strategies[strategy.name()] = strategy
    
    def unregister(self, name: str):
        """注销策略"""
        del self.strategies[name]
    
    def get_all_signals(self, stock_codes: List[str]) -> List[Signal]:
        """获取所有策略的信号"""
        all_signals = []
        for strategy in self.strategies.values():
            signals = strategy.generate_signals(stock_codes)
            all_signals.extend(signals)
        return all_signals
    
    def resolve_conflicts(self, signals: List[Signal]) -> List[Signal]:
        """解决策略冲突"""
        # 同一股票的相反信号，按置信度决定
        resolved = {}
        for signal in signals:
            key = signal.stock_code
            if key not in resolved:
                resolved[key] = signal
            elif signal.confidence > resolved[key].confidence:
                resolved[key] = signal
        return list(resolved.values())
```

### 3.2 执行引擎

#### 3.2.1 执行模式

**定时轮询模式**
- 使用APScheduler调度
- 可配置执行间隔（分钟级）
- 适合大多数场景

**实时监控模式**
- WebSocket推送行情
- 毫秒级响应
- 适合高频策略

**批量执行模式**
- 收盘后分析
- 次日开盘执行
- 适合中长线策略

#### 3.2.2 执行器实现

```python
from enum import Enum
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class ExecutionMode(Enum):
    POLLING = "polling"        # 定时轮询
    REALTIME = "realtime"      # 实时监控
    BATCH = "batch"            # 批量执行

class ExecutionEngine:
    """执行引擎"""
    
    def __init__(self, strategy_engine, risk_control, fund_manager):
        self.strategy_engine = strategy_engine
        self.risk_control = risk_control
        self.fund_manager = fund_manager
        self.scheduler = AsyncIOScheduler()
        self.running = False
    
    def start(self, mode: ExecutionMode, config: dict):
        """启动执行引擎"""
        if mode == ExecutionMode.POLLING:
            interval = config.get("interval_minutes", 5)
            self.scheduler.add_job(
                self._execute_cycle,
                'interval',
                minutes=interval,
                id='polling_job'
            )
        elif mode == ExecutionMode.BATCH:
            # 每天15:30执行分析
            self.scheduler.add_job(
                self._batch_analysis,
                'cron',
                hour=15,
                minute=30,
                id='batch_analysis'
            )
            # 每天09:30执行交易
            self.scheduler.add_job(
                self._batch_execute,
                'cron',
                hour=9,
                minute=30,
                id='batch_execute'
            )
        
        self.scheduler.start()
        self.running = True
    
    def stop(self):
        """停止执行引擎"""
        self.scheduler.shutdown()
        self.running = False
    
    async def _execute_cycle(self):
        """执行一个交易周期"""
        # 1. 获取监控的股票列表
        stock_codes = self._get_watchlist()
        
        # 2. 生成信号
        signals = self.strategy_engine.get_all_signals(stock_codes)
        
        # 3. 解决冲突
        signals = self.strategy_engine.resolve_conflicts(signals)
        
        # 4. 风控检查
        approved_signals = []
        for signal in signals:
            if self.risk_control.check(signal):
                approved_signals.append(signal)
        
        # 5. 执行交易
        for signal in approved_signals:
            await self.fund_manager.execute_trade(signal)
    
    async def _batch_analysis(self):
        """批量分析（收盘后）"""
        stock_codes = self._get_watchlist()
        signals = self.strategy_engine.get_all_signals(stock_codes)
        self._pending_signals = signals
    
    async def _batch_execute(self):
        """批量执行（开盘时）"""
        if hasattr(self, '_pending_signals'):
            for signal in self._pending_signals:
                if self.risk_control.check(signal):
                    await self.fund_manager.execute_trade(signal)
            self._pending_signals = []
```

### 3.3 风控系统

#### 3.3.1 风控规则

```python
@dataclass
class RiskConfig:
    # 止损止盈
    stop_loss_pct: float = -0.05      # 止损比例 -5%
    take_profit_pct: float = 0.10     # 止盈比例 10%
    
    # 仓位控制
    max_position_pct: float = 0.20    # 单只股票最大仓位 20%
    max_total_position_pct: float = 0.80  # 总仓位上限 80%
    
    # 交易频率
    max_daily_trades: int = 10        # 每日最大交易次数
    max_weekly_trades: int = 30       # 每周最大交易次数
    
    # 资金管理
    max_daily_loss: float = 50000.0   # 每日最大亏损 5万
    max_single_trade: float = 100000.0  # 单笔最大交易金额 10万
```

#### 3.3.2 风控检查

```python
class RiskControl:
    """风控系统"""
    
    def __init__(self, config: RiskConfig, db: Session):
        self.config = config
        self.db = db
    
    def check(self, signal: Signal, user_id: int) -> tuple[bool, str]:
        """
        风控检查
        
        Returns:
            (是否通过, 原因)
        """
        checks = [
            self._check_stop_loss,
            self._check_take_profit,
            self._check_position_limit,
            self._check_trade_frequency,
            self._check_daily_loss,
            self._check_single_trade,
        ]
        
        for check in checks:
            passed, reason = check(signal, user_id)
            if not passed:
                return False, reason
        
        return True, "通过"
    
    def _check_position_limit(self, signal: Signal, user_id: int) -> tuple[bool, str]:
        """检查仓位限制"""
        # 获取当前持仓
        position = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.stock_code == signal.stock_code
        ).first()
        
        # 获取账户总资产
        account = self._get_account_overview(user_id)
        
        if position:
            position_value = position.quantity * signal.price
            position_pct = position_value / account.total_assets
            
            if position_pct > self.config.max_position_pct:
                return False, f"仓位超限: {position_pct:.1%} > {self.config.max_position_pct:.1%}"
        
        return True, "通过"
    
    def _check_trade_frequency(self, signal: Signal, user_id: int) -> tuple[bool, str]:
        """检查交易频率"""
        today = datetime.now().replace(hour=0, minute=0, second=0)
        
        daily_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= today
        ).count()
        
        if daily_trades >= self.config.max_daily_trades:
            return False, f"今日交易次数已达上限: {daily_trades}"
        
        return True, "通过"
```

### 3.4 资金管理

#### 3.4.1 资金模式

```python
class FundMode(Enum):
    SIMULATED = "simulated"  # 模拟资金
    REAL = "real"            # 真实资金

class FundManager:
    """资金管理器"""
    
    def __init__(self, mode: FundMode, db: Session):
        self.mode = mode
        self.db = db
    
    async def execute_trade(self, signal: Signal, user_id: int) -> TradeResult:
        """执行交易"""
        if self.mode == FundMode.SIMULATED:
            return await self._execute_simulated(signal, user_id)
        else:
            return await self._execute_real(signal, user_id)
    
    async def _execute_simulated(self, signal: Signal, user_id: int) -> TradeResult:
        """模拟资金交易"""
        engine = TradingEngine(self.db)
        
        if signal.direction == "BUY":
            return engine.buy(
                user_id=user_id,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                price=signal.price,
                quantity=signal.quantity,
                strategy_tag=signal.strategy_name
            )
        else:
            return engine.sell(
                user_id=user_id,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                price=signal.price,
                quantity=signal.quantity,
                strategy_tag=signal.strategy_name
            )
    
    async def _execute_real(self, signal: Signal, user_id: int) -> TradeResult:
        """真实资金交易"""
        # 调用券商API
        # 这里是示例，实际需要对接具体券商
        broker = self._get_broker(user_id)
        
        try:
            order = await broker.place_order(
                stock_code=signal.stock_code,
                direction=signal.direction,
                price=signal.price,
                quantity=signal.quantity
            )
            
            # 记录交易
            trade = Trade(
                user_id=user_id,
                stock_code=signal.stock_code,
                trade_type=signal.direction,
                price=signal.price,
                quantity=signal.quantity,
                total_amount=signal.price * signal.quantity,
                strategy_tag=signal.strategy_name
            )
            self.db.add(trade)
            self.db.commit()
            
            return TradeResult(success=True, message="交易成功", trade=trade)
        except Exception as e:
            return TradeResult(success=False, message=str(e))
```

### 3.5 数据模型

#### 3.5.1 策略配置表

```sql
CREATE TABLE strategy_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(50) NOT NULL,
    strategy_type VARCHAR(20) NOT NULL,  -- PREDICTION/MA/RSI/RULE
    config JSONB NOT NULL,               -- 策略配置参数
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.5.2 自动交易任务表

```sql
CREATE TABLE auto_trade_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    execution_mode VARCHAR(20) NOT NULL,  -- POLLING/REALTIME/BATCH
    interval_minutes INTEGER,             -- 轮询间隔
    watchlist TEXT[],                     -- 监控股票列表
    enabled BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.5.3 风控配置表

```sql
CREATE TABLE risk_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    stop_loss_pct FLOAT DEFAULT -0.05,
    take_profit_pct FLOAT DEFAULT 0.10,
    max_position_pct FLOAT DEFAULT 0.20,
    max_total_position_pct FLOAT DEFAULT 0.80,
    max_daily_trades INTEGER DEFAULT 10,
    max_weekly_trades INTEGER DEFAULT 30,
    max_daily_loss FLOAT DEFAULT 50000.0,
    max_single_trade FLOAT DEFAULT 100000.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.5.4 自动交易日志表

```sql
CREATE TABLE auto_trade_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    task_id INTEGER REFERENCES auto_trade_tasks(id),
    signal_source VARCHAR(50),
    stock_code VARCHAR(10),
    direction VARCHAR(4),
    price FLOAT,
    quantity INTEGER,
    confidence FLOAT,
    risk_check_passed BOOLEAN,
    risk_check_reason VARCHAR(200),
    execution_result VARCHAR(20),  -- SUCCESS/FAILED/SKIPPED
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6 API设计

#### 3.6.1 策略管理API

```
POST   /api/strategies                    # 创建策略配置
GET    /api/strategies                    # 获取策略列表
GET    /api/strategies/{id}               # 获取策略详情
PUT    /api/strategies/{id}               # 更新策略配置
DELETE /api/strategies/{id}               # 删除策略
POST   /api/strategies/{id}/enable        # 启用策略
POST   /api/strategies/{id}/disable       # 禁用策略
```

#### 3.6.2 自动交易任务API

```
POST   /api/auto-trading/tasks            # 创建任务
GET    /api/auto-trading/tasks            # 获取任务列表
PUT    /api/auto-trading/tasks/{id}       # 更新任务
DELETE /api/auto-trading/tasks/{id}       # 删除任务
POST   /api/auto-trading/tasks/{id}/start # 启动任务
POST   /api/auto-trading/tasks/{id}/stop  # 停止任务
GET    /api/auto-trading/status           # 获取运行状态
```

#### 3.6.3 风控配置API

```
GET    /api/risk-config                   # 获取风控配置
PUT    /api/risk-config                   # 更新风控配置
```

#### 3.6.4 自动交易日志API

```
GET    /api/auto-trading/logs             # 获取交易日志
GET    /api/auto-trading/logs/{id}        # 获取日志详情
GET    /api/auto-trading/statistics       # 获取统计数据
```

### 3.7 前端界面设计

#### 3.7.1 自动交易监控页面

```
┌─────────────────────────────────────────────────────────────┐
│  自动交易监控                                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  运行状态       │  │  今日统计       │                  │
│  │  状态: 运行中   │  │  交易次数: 5    │                  │
│  │  模式: 定时轮询 │  │  盈亏: +2300    │                  │
│  │  间隔: 5分钟    │  │  胜率: 60%      │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│  策略列表                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 策略名称    │ 类型    │ 状态  │ 今日信号 │ 操作     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ LSTM预测    │ 预测    │ 启用  │ 3       │ [禁用]   │   │
│  │ 均线策略    │ 技术    │ 启用  │ 2       │ [禁用]   │   │
│  │ RSI策略     │ 技术    │ 禁用  │ 0       │ [启用]   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  最近交易记录                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 时间      │ 股票    │ 方向 │ 价格   │ 数量 │ 策略   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 10:30:00  │ 000001  │ 买入 │ 10.50  │ 1000 │ LSTM  │   │
│  │ 10:25:00  │ 000002  │ 卖出 │ 15.20  │ 500  │ 均线  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 3.7.2 策略配置页面

```
┌─────────────────────────────────────────────────────────────┐
│  策略配置                                                    │
├─────────────────────────────────────────────────────────────┤
│  策略类型: [预测信号 ▼]                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 预测信号策略配置                                      │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 监控股票: [000001, 000002, 000003]                  │   │
│  │ 置信度阈值: [0.7]                                   │   │
│  │ 信号有效期: [30] 分钟                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 风控设置                                              │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 止损比例: [-5%]                                      │   │
│  │ 止盈比例: [10%]                                      │   │
│  │ 单只仓位上限: [20%]                                  │   │
│  │ 每日最大交易: [10] 次                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [保存配置]  [测试策略]                                      │
└─────────────────────────────────────────────────────────────┘
```

## 4. 实现计划

### 4.1 Phase 1: 策略引擎基础

- 实现策略基类和接口
- 实现预测信号策略（复用现有LSTM模型）
- 实现均线策略
- 策略配置数据模型

### 4.2 Phase 2: 执行引擎

- 实现定时轮询模式
- 实现批量执行模式
- 自动交易任务管理

### 4.3 Phase 3: 风控系统

- 实现止损止盈检查
- 实现仓位控制检查
- 实现交易频率限制
- 实现资金限额检查

### 4.4 Phase 4: 前端界面

- 自动交易监控页面
- 策略配置页面
- 风控配置页面
- 交易日志页面

### 4.5 Phase 5: 真实资金对接

- 券商API接口设计
- 模拟/真实资金切换
- 订单状态同步

## 5. 风险与应对

### 5.1 技术风险

| 风险 | 应对措施 |
|------|----------|
| 策略信号冲突 | 置信度优先级机制 |
| 执行延迟 | 异步处理，队列缓冲 |
| 数据不一致 | 事务管理，幂等设计 |

### 5.2 业务风险

| 风险 | 应对措施 |
|------|----------|
| 策略失效 | 回测验证，小资金测试 |
| 市场异常 | 异常检测，自动暂停 |
| 资金损失 | 严格风控，模拟优先 |

---

**文档版本**: v1.0  
**创建日期**: 2026-06-01  
**最后更新**: 2026-06-01
