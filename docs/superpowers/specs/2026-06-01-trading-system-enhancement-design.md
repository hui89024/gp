# 交易系统增强设计文档

## 1. 项目概述

### 1.1 项目目标

基于现有系统，补充以下关键功能：
1. 历史回测系统 - 策略验证的基础
2. 独立风控熔断 - 安全保障，防止爆仓
3. 告警系统 - 运维必备，异常及时通知
4. 参数敏感性分析 - 防止过拟合
5. 纸交易模式 - 实时模拟验证

### 1.2 核心原则

- **回测优先**：任何策略上线前必须通过历史回测
- **风控独立**：风控系统独立于策略，可强制熔断
- **告警及时**：异常发生时秒级通知

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端界面                                │
│  - 回测报告页面                                              │
│  - 风控监控面板                                              │
│  - 告警中心                                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端服务                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  回测引擎   │  │  风控熔断   │  │  告警系统   │         │
│  │  Backtest   │  │  CircuitBrk │  │  AlertSvc   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  策略引擎   │  │  执行引擎   │  │  数据服务   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

**回测引擎 (BacktestEngine)**
- 加载历史数据
- 模拟策略执行
- 计算性能指标
- 生成回测报告

**风控熔断 (CircuitBreaker)**
- 实时监控账户状态
- 检测异常行为
- 强制停止交易
- 锁仓保护

**告警系统 (AlertService)**
- 多渠道通知（钉钉/微信/邮件）
- 告警规则配置
- 告警历史记录
- 告警升级机制

## 3. 模块详细设计

### 3.1 历史回测系统

#### 3.1.1 回测引擎

```python
@dataclass
class BacktestConfig:
    start_date: datetime
    end_date: datetime
    initial_capital: float
    stock_codes: List[str]
    strategy_name: str
    strategy_config: Dict[str, Any]
    commission_rate: float = 0.00025
    slippage_pct: float = 0.001  # 滑点比例
    
@dataclass
class BacktestResult:
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int
    trades: List[Dict]
    equity_curve: List[Dict]
    daily_returns: List[float]

class BacktestEngine:
    """回测引擎"""
    
    def run(self, config: BacktestConfig) -> BacktestResult:
        """运行回测"""
        # 1. 加载历史数据
        data = self._load_data(config.stock_codes, config.start_date, config.end_date)
        
        # 2. 初始化账户
        account = SimulatedAccount(config.initial_capital)
        
        # 3. 创建策略实例
        strategy = self._create_strategy(config.strategy_name, config.strategy_config)
        
        # 4. 逐日模拟
        for date in self._trading_dates(config.start_date, config.end_date):
            # 获取当日数据
            daily_data = self._get_daily_data(data, date)
            
            # 生成信号
            signals = strategy.generate_signals(daily_data)
            
            # 执行交易（考虑滑点）
            for signal in signals:
                slippage = signal.price * config.slippage_pct
                if signal.direction == "BUY":
                    actual_price = signal.price + slippage
                else:
                    actual_price = signal.price - slippage
                
                account.execute_trade(signal, actual_price, config.commission_rate)
            
            # 记录每日权益
            account.record_daily_equity(date)
        
        # 5. 计算性能指标
        return self._calculate_metrics(account)
```

#### 3.1.2 性能指标

```python
def _calculate_metrics(self, account: SimulatedAccount) -> BacktestResult:
    """计算回测性能指标"""
    equity_curve = account.equity_curve
    daily_returns = self._calculate_daily_returns(equity_curve)
    
    return BacktestResult(
        total_return=self._total_return(equity_curve),
        annual_return=self._annual_return(equity_curve),
        max_drawdown=self._max_drawdown(equity_curve),
        sharpe_ratio=self._sharpe_ratio(daily_returns),
        win_rate=self._win_rate(account.trades),
        profit_loss_ratio=self._profit_loss_ratio(account.trades),
        total_trades=len(account.trades),
        trades=account.trades,
        equity_curve=equity_curve,
        daily_returns=daily_returns
    )

def _max_drawdown(self, equity_curve: List[Dict]) -> float:
    """计算最大回撤"""
    peak = equity_curve[0]["equity"]
    max_dd = 0
    
    for point in equity_curve:
        if point["equity"] > peak:
            peak = point["equity"]
        dd = (peak - point["equity"]) / peak
        if dd > max_dd:
            max_dd = dd
    
    return max_dd

def _sharpe_ratio(self, daily_returns: List[float], risk_free_rate: float = 0.03) -> float:
    """计算夏普比率"""
    if not daily_returns:
        return 0.0
    
    avg_return = np.mean(daily_returns)
    std_return = np.std(daily_returns)
    
    if std_return == 0:
        return 0.0
    
    annualized_return = avg_return * 252
    annualized_std = std_return * np.sqrt(252)
    
    return (annualized_return - risk_free_rate) / annualized_std
```

#### 3.1.3 过拟合检测

```python
class OverfittingDetector:
    """过拟合检测器"""
    
    def cscv_test(self, strategy_factory, data: pd.DataFrame, n_splits: int = 10) -> Dict:
        """
        CSCV (Combinatorially Symmetric Cross-Validation) 过拟合检测
        
        Returns:
            过拟合概率和相关指标
        """
        # 将数据分成n_splits份
        splits = np.array_split(data, n_splits)
        
        # 生成所有可能的训练/测试组合
        combinations = list(combinations(range(n_splits), n_splits // 2))
        
        results = []
        for train_idx, test_idx in self._split_combinations(combinations):
            # 训练集
            train_data = pd.concat([splits[i] for i in train_idx])
            # 测试集
            test_data = pd.concat([splits[i] for i in test_idx])
            
            # 在训练集上优化参数
            best_params = self._optimize_params(strategy_factory, train_data)
            
            # 在测试集上验证
            test_performance = self._evaluate(strategy_factory(best_params), test_data)
            
            results.append({
                "train_idx": train_idx,
                "test_idx": test_idx,
                "best_params": best_params,
                "test_performance": test_performance
            })
        
        # 计算过拟合概率
        overfitting_prob = self._calculate_overfitting_probability(results)
        
        return {
            "overfitting_probability": overfitting_prob,
            "n_combinations": len(combinations),
            "results": results
        }
    
    def _calculate_overfitting_probability(self, results: List[Dict]) -> float:
        """计算过拟合概率"""
        # 如果测试集性能明显低于训练集，说明过拟合
        degraded_count = sum(1 for r in results if r["test_performance"] < 0.5)
        return degraded_count / len(results)
```

### 3.2 独立风控熔断

#### 3.2.1 熔断规则

```python
@dataclass
class CircuitBreakerConfig:
    # 最大回撤熔断
    max_drawdown_pct: float = -0.10  # 最大回撤10%触发
    
    # 单日亏损熔断
    max_daily_loss_pct: float = -0.05  # 单日亏损5%触发
    
    # 连续亏损熔断
    max_consecutive_losses: int = 5  # 连续亏损5次触发
    
    # 异常交易熔断
    max_trades_per_minute: int = 10  # 每分钟最多10笔交易
    
    # 仓位熔断
    max_position_pct: float = 0.90  # 仓位超过90%触发
    
    # 净敞口熔断
    max_net_exposure_pct: float = 0.80  # 净敞口超过80%触发

class CircuitBreaker:
    """独立风控熔断器"""
    
    def __init__(self, config: CircuitBreakerConfig, db: Session):
        self.config = config
        self.db = db
        self.is_triggered = False
        self.trigger_reason = None
    
    def check(self, user_id: int) -> Tuple[bool, str]:
        """检查是否需要熔断"""
        checks = [
            self._check_drawdown,
            self._check_daily_loss,
            self._check_consecutive_losses,
            self._check_trade_frequency,
            self._check_position,
            self._check_net_exposure,
        ]
        
        for check in checks:
            triggered, reason = check(user_id)
            if triggered:
                self._trigger_breaker(reason)
                return True, reason
        
        return False, "正常"
    
    def _trigger_breaker(self, reason: str):
        """触发熔断"""
        self.is_triggered = True
        self.trigger_reason = reason
        
        # 1. 停止所有自动交易任务
        self._stop_all_tasks()
        
        # 2. 取消所有未成交订单
        self._cancel_all_orders()
        
        # 3. 记录熔断事件
        self._log_circuit_break(reason)
        
        # 4. 发送紧急告警
        self._send_emergency_alert(reason)
    
    def _check_drawdown(self, user_id: int) -> Tuple[bool, str]:
        """检查最大回撤"""
        # 计算账户历史最高点和当前净值
        # 如果回撤超过阈值，触发熔断
        pass
    
    def _check_daily_loss(self, user_id: int) -> Tuple[bool, str]:
        """检查单日亏损"""
        today = datetime.now().replace(hour=0, minute=0, second=0)
        # 计算今日盈亏
        # 如果亏损超过阈值，触发熔断
        pass
    
    def _check_consecutive_losses(self, user_id: int) -> Tuple[bool, str]:
        """检查连续亏损"""
        # 获取最近N笔交易
        # 如果连续亏损超过阈值，触发熔断
        pass
    
    def _check_trade_frequency(self, user_id: int) -> Tuple[bool, str]:
        """检查交易频率"""
        # 检查最近一分钟的交易次数
        # 如果超过阈值，触发熔断
        pass
    
    def _check_position(self, user_id: int) -> Tuple[bool, str]:
        """检查仓位"""
        # 计算当前仓位占比
        # 如果超过阈值，触发熔断
        pass
    
    def _check_net_exposure(self, user_id: int) -> Tuple[bool, str]:
        """检查净敞口"""
        # 计算多空净敞口
        # 如果超过阈值，触发熔断
        pass
    
    def reset(self):
        """重置熔断器"""
        self.is_triggered = False
        self.trigger_reason = None
    
    def _send_emergency_alert(self, reason: str):
        """发送紧急告警"""
        # 调用告警系统发送紧急通知
        pass
```

### 3.3 告警系统

#### 3.3.1 告警规则

```python
@dataclass
class AlertRule:
    name: str
    condition: str  # 条件表达式
    severity: str   # INFO/WARNING/CRITICAL
    channels: List[str]  # 通知渠道
    cooldown_minutes: int = 5  # 冷却时间

class AlertService:
    """告警服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifiers = {
            "dingtalk": DingTalkNotifier(),
            "wechat": WeChatNotifier(),
            "email": EmailNotifier(),
        }
        self.rules = self._load_rules()
    
    def check_and_alert(self, user_id: int, context: Dict):
        """检查并发送告警"""
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, context):
                if self._can_alert(rule, user_id):
                    self._send_alert(rule, user_id, context)
                    self._record_alert(rule, user_id, context)
    
    def _send_alert(self, rule: AlertRule, user_id: int, context: Dict):
        """发送告警"""
        message = self._format_message(rule, context)
        
        for channel in rule.channels:
            notifier = self.notifiers.get(channel)
            if notifier:
                notifier.send(user_id, message, rule.severity)
    
    def _load_rules(self) -> List[AlertRule]:
        """加载告警规则"""
        return [
            AlertRule(
                name="最大回撤告警",
                condition="max_drawdown > 0.08",
                severity="WARNING",
                channels=["dingtalk", "email"],
                cooldown_minutes=30
            ),
            AlertRule(
                name="单日亏损告警",
                condition="daily_loss > 0.03",
                severity="WARNING",
                channels=["dingtalk"],
                cooldown_minutes=5
            ),
            AlertRule(
                name="连续亏损告警",
                condition="consecutive_losses >= 3",
                severity="CRITICAL",
                channels=["dingtalk", "wechat", "email"],
                cooldown_minutes=0
            ),
            AlertRule(
                name="熔断触发告警",
                condition="circuit_breaker_triggered",
                severity="CRITICAL",
                channels=["dingtalk", "wechat", "email"],
                cooldown_minutes=0
            ),
            AlertRule(
                name="网络异常告警",
                condition="network_error_count > 5",
                severity="WARNING",
                channels=["dingtalk"],
                cooldown_minutes=10
            ),
            AlertRule(
                name="API异常告警",
                condition="api_error_count > 3",
                severity="WARNING",
                channels=["dingtalk"],
                cooldown_minutes=10
            ),
        ]
```

#### 3.3.2 通知渠道

```python
class DingTalkNotifier:
    """钉钉通知"""
    
    def __init__(self):
        self.webhook_url = settings.DINGTALK_WEBHOOK_URL
        self.secret = settings.DINGTALK_SECRET
    
    def send(self, user_id: int, message: str, severity: str):
        """发送钉钉消息"""
        # 构建消息体
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"[{severity}] 股票交易系统告警",
                "text": message
            }
        }
        
        # 签名
        timestamp = str(round(time.time() * 1000))
        sign = self._sign(timestamp)
        
        # 发送请求
        url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
        requests.post(url, json=payload)


class WeChatNotifier:
    """微信通知"""
    
    def send(self, user_id: int, message: str, severity: str):
        """发送微信消息"""
        # 通过企业微信API发送
        pass


class EmailNotifier:
    """邮件通知"""
    
    def send(self, user_id: int, message: str, severity: str):
        """发送邮件"""
        # 通过SMTP发送
        pass
```

### 3.4 纸交易模式

```python
class PaperTradingEngine:
    """纸交易引擎 - 接入实时行情但不实际成交"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.data_service = DataService()
        self.strategy_engine = StrategyEngine(db)
        self.circuit_breaker = CircuitBreaker(db)
        
        # 纸交易账户（虚拟资金）
        self.paper_account = PaperAccount(initial_capital=1000000)
    
    def start(self, stock_codes: List[str]):
        """启动纸交易"""
        self.strategy_engine.load_strategies(self.user_id)
        
        # 订阅实时行情
        for code in stock_codes:
            self.data_service.subscribe_realtime(code, self._on_quote_update)
    
    def _on_quote_update(self, quote: StockQuote):
        """行情更新回调"""
        # 1. 检查熔断
        if self.circuit_breaker.is_triggered:
            return
        
        # 2. 生成信号
        signals = self.strategy_engine.get_all_signals([quote.stock_code])
        
        # 3. 执行纸交易
        for signal in signals:
            self.paper_account.execute_paper_trade(signal, quote.current_price)
        
        # 4. 记录（标记为纸交易）
        self._log_paper_trade(signals)
```

### 3.5 数据模型

#### 3.5.1 回测记录表

```sql
CREATE TABLE backtest_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(50),
    strategy_config JSONB,
    start_date DATE,
    end_date DATE,
    initial_capital FLOAT,
    stock_codes TEXT[],
    
    -- 回测结果
    total_return FLOAT,
    annual_return FLOAT,
    max_drawdown FLOAT,
    sharpe_ratio FLOAT,
    win_rate FLOAT,
    profit_loss_ratio FLOAT,
    total_trades INTEGER,
    
    -- 详细数据
    trades JSONB,
    equity_curve JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.5.2 熔断事件表

```sql
CREATE TABLE circuit_breaker_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    trigger_reason VARCHAR(200),
    trigger_value FLOAT,
    threshold FLOAT,
    action_taken VARCHAR(50),  -- STOP_TASKS/CANCEL_ORDERS/LOCK_POSITIONS
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.5.3 告警记录表

```sql
CREATE TABLE alert_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    rule_name VARCHAR(100),
    severity VARCHAR(20),  -- INFO/WARNING/CRITICAL
    message TEXT,
    channels VARCHAR(50)[],
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6 API设计

#### 3.6.1 回测API

```
POST   /api/backtest/run              # 运行回测
GET    /api/backtest/records          # 获取回测记录
GET    /api/backtest/records/{id}     # 获取回测详情
POST   /api/backtest/overfitting      # 过拟合检测
```

#### 3.6.2 熔断API

```
GET    /api/circuit-breaker/status    # 获取熔断状态
POST   /api/circuit-breaker/reset     # 重置熔断器
GET    /api/circuit-breaker/config    # 获取熔断配置
PUT    /api/circuit-breaker/config    # 更新熔断配置
GET    /api/circuit-breaker/events    # 获取熔断事件
```

#### 3.6.3 告警API

```
GET    /api/alerts/rules              # 获取告警规则
POST   /api/alerts/rules              # 创建告警规则
PUT    /api/alerts/rules/{id}         # 更新告警规则
DELETE /api/alerts/rules/{id}         # 删除告警规则
GET    /api/alerts/records            # 获取告警记录
POST   /api/alerts/test               # 测试告警
```

### 3.7 前端界面设计

#### 3.7.1 回测报告页面

```
┌─────────────────────────────────────────────────────────────┐
│  回测报告                                                    │
├─────────────────────────────────────────────────────────────┤
│  策略: [均线策略 ▼]  时间: [2023-01-01] 至 [2024-01-01]     │
│  [运行回测]                                                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ 总收益: 25.3%   │  │ 年化收益: 18.2% │                  │
│  │ 最大回撤: -8.5% │  │ 夏普比率: 1.52  │                  │
│  │ 胜率: 62%       │  │ 盈亏比: 1.8     │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│  权益曲线                                                    │
│  [图表]                                                      │
├─────────────────────────────────────────────────────────────┤
│  交易记录                                                    │
│  [表格]                                                      │
└─────────────────────────────────────────────────────────────┘
```

#### 3.7.2 风控监控面板

```
┌─────────────────────────────────────────────────────────────┐
│  风控监控                                                    │
├─────────────────────────────────────────────────────────────┤
│  熔断状态: 正常 ✅                                           │
│  当前回撤: -2.3%  阈值: -10%                                 │
│  今日亏损: -1.2%  阈值: -5%                                  │
│  连续亏损: 2次    阈值: 5次                                  │
├─────────────────────────────────────────────────────────────┤
│  最近熔断事件                                                │
│  2024-01-15 10:30  触发原因: 连续亏损5次                      │
│  2024-01-10 14:20  触发原因: 单日亏损超过5%                   │
└─────────────────────────────────────────────────────────────┘
```

## 4. 实现计划

### 4.1 Phase 1: 历史回测系统

- 实现回测引擎
- 实现性能指标计算
- 实现回测报告生成
- 前端回测页面

### 4.2 Phase 2: 独立风控熔断

- 实现熔断规则引擎
- 实现熔断触发和重置
- 实现仓位锁定
- 前端风控监控

### 4.3 Phase 3: 告警系统

- 实现告警规则引擎
- 实现钉钉通知
- 实现微信通知
- 实现邮件通知
- 前端告警中心

### 4.4 Phase 4: 过拟合检测

- 实现CSCV检测
- 实现参数敏感性分析
- 前端过拟合报告

### 4.5 Phase 5: 纸交易模式

- 实现纸交易引擎
- 实时行情接入
- 前端纸交易监控

---

**文档版本**: v1.0  
**创建日期**: 2026-06-01  
**最后更新**: 2026-06-01
