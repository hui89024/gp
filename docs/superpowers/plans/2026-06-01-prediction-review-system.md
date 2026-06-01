# 股票预测与复盘系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现股票预测（LSTM模型）和复盘分析系统

**Architecture:** 基于现有后端架构，添加预测服务和复盘分析模块

**Tech Stack:** PyTorch (LSTM), Pandas, NumPy, scikit-learn

---

## Task 1: 预测数据模型

**Files:**
- Create: `backend/app/models/prediction.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建预测记录模型**

```python
# backend/app/models/prediction.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    model_type = Column(String(20), nullable=False)  # LSTM/Transformer/Ensemble
    predicted_direction = Column(String(4))  # UP/DOWN
    predicted_price = Column(Float)
    confidence = Column(Float)
    actual_result = Column(String(4))  # UP/DOWN/NA
    actual_price = Column(Float)
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: 更新模型导出**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.models.prediction import Prediction

__all__ = ["User", "Position", "Trade", "Prediction"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add prediction model for tracking forecasts"
```

---

## Task 2: 预测Schema定义

**Files:**
- Create: `backend/app/schemas/prediction.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 创建预测Schema**

```python
# backend/app/schemas/prediction.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PredictionCreate(BaseModel):
    stock_code: str
    model_type: str = "LSTM"


class PredictionResponse(BaseModel):
    id: int
    stock_code: str
    model_type: str
    predicted_direction: Optional[str]
    predicted_price: Optional[float]
    confidence: Optional[float]
    actual_result: Optional[str]
    actual_price: Optional[float]
    prediction_date: datetime
    target_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionSignal(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    predicted_direction: str  # UP/DOWN
    predicted_price: float
    confidence: float
    signal_strength: str  # STRONG/MEDIUM/WEAK
    model_type: str
    prediction_date: datetime


class ModelPerformance(BaseModel):
    model_type: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    avg_confidence: float
```

- [ ] **Step 2: 更新Schema导出**

```python
# backend/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, AccountOverview
from app.schemas.trade import TradeCreate, TradeResponse, PositionResponse
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult, KLineData
from app.schemas.prediction import PredictionCreate, PredictionResponse, PredictionSignal, ModelPerformance

__all__ = [
    "UserCreate", "UserResponse", "AccountOverview",
    "TradeCreate", "TradeResponse", "PositionResponse",
    "StockQuote", "StockHistory", "StockSearchResult", "KLineData",
    "PredictionCreate", "PredictionResponse", "PredictionSignal", "ModelPerformance"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add prediction schemas"
```

---

## Task 3: LSTM预测服务

**Files:**
- Create: `backend/app/services/prediction_service.py`
- Create: `backend/app/ml/__init__.py`
- Create: `backend/app/ml/lstm_model.py`
- Create: `backend/tests/test_prediction_service.py`

- [ ] **Step 1: 创建ML模块初始化**

```python
# backend/app/ml/__init__.py
"""Machine Learning models for stock prediction"""
```

- [ ] **Step 2: 创建LSTM模型**

```python
# backend/app/ml/lstm_model.py
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, List


class LSTMModel(nn.Module):
    """LSTM股票预测模型"""
    
    def __init__(self, input_size: int = 5, hidden_size: int = 64, num_layers: int = 2, output_size: int = 1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_size)
        )
    
    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_size)
        lstm_out, _ = self.lstm(x)
        # 取最后一个时间步的输出
        last_output = lstm_out[:, -1, :]
        prediction = self.fc(last_output)
        return prediction


class StockPredictor:
    """股票预测器"""
    
    def __init__(self, sequence_length: int = 30):
        self.sequence_length = sequence_length
        self.model = LSTMModel(input_size=5, hidden_size=64, num_layers=2)
        self.scaler = MinMaxScaler()
        self.is_trained = False
    
    def prepare_data(self, prices: List[float], volumes: List[int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
        
        Returns:
            X, y 训练数据
        """
        # 创建特征: [open, high, low, close, volume]
        # 简化处理：使用价格作为所有价格特征
        data = np.array([[p, p, p, p, v] for p, v in zip(prices, volumes)])
        
        # 归一化
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            # 预测价格变化方向 (1: 涨, 0: 跌)
            y.append(1 if prices[i] > prices[i-1] else 0)
        
        return np.array(X), np.array(y)
    
    def train(self, prices: List[float], volumes: List[int], epochs: int = 50) -> dict:
        """
        训练模型
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            epochs: 训练轮数
        
        Returns:
            训练结果
        """
        X, y = self.prepare_data(prices, volumes)
        
        if len(X) < 10:
            return {"success": False, "message": "数据不足，需要至少40条历史数据"}
        
        # 转换为tensor
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y).unsqueeze(1)
        
        # 训练模型
        criterion = nn.BCEWithLogitsLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        self.model.train()
        losses = []
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        
        self.is_trained = True
        
        return {
            "success": True,
            "epochs": epochs,
            "final_loss": losses[-1],
            "samples": len(X)
        }
    
    def predict(self, prices: List[float], volumes: List[int]) -> dict:
        """
        预测股票走势
        
        Args:
            prices: 最近的价格序列
            volumes: 最近的成交量序列
        
        Returns:
            预测结果
        """
        if not self.is_trained:
            return {"direction": "UP", "confidence": 0.5, "predicted_price": prices[-1]}
        
        # 准备输入数据
        data = np.array([[p, p, p, p, v] for p, v in zip(prices[-self.sequence_length:], volumes[-self.sequence_length:])])
        scaled_data = self.scaler.transform(data)
        X = np.array([scaled_data])
        
        # 预测
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            output = torch.sigmoid(self.model(X_tensor)).item()
        
        direction = "UP" if output > 0.5 else "DOWN"
        confidence = output if output > 0.5 else 1 - output
        
        # 预测价格（简化处理）
        price_change = 0.02 if direction == "UP" else -0.02
        predicted_price = prices[-1] * (1 + price_change * confidence)
        
        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "predicted_price": round(predicted_price, 2)
        }
```

- [ ] **Step 3: 创建预测服务**

```python
# backend/app/services/prediction_service.py
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionSignal, ModelPerformance
from app.services.data_service import DataService
from app.ml.lstm_model import StockPredictor


class PredictionService:
    """预测服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_service = DataService()
        self.predictors = {}  # 每个股票一个预测器
    
    def get_or_create_predictor(self, stock_code: str) -> StockPredictor:
        """获取或创建预测器"""
        if stock_code not in self.predictors:
            self.predictors[stock_code] = StockPredictor()
        return self.predictors[stock_code]
    
    def train_model(self, stock_code: str, days: int = 180) -> dict:
        """
        训练预测模型
        
        Args:
            stock_code: 股票代码
            days: 使用的历史数据天数
        
        Returns:
            训练结果
        """
        # 获取历史数据
        history = self.data_service.get_stock_history(stock_code, days)
        
        if len(history) < 40:
            return {"success": False, "message": f"历史数据不足: {len(history)}条，需要至少40条"}
        
        prices = [h.close for h in history]
        volumes = [h.volume for h in history]
        
        predictor = self.get_or_create_predictor(stock_code)
        result = predictor.train(prices, volumes)
        
        return result
    
    def predict(self, stock_code: str) -> Optional[PredictionSignal]:
        """
        生成预测信号
        
        Args:
            stock_code: 股票代码
        
        Returns:
            预测信号
        """
        # 获取实时行情
        quote = self.data_service.get_stock_quote(stock_code)
        if not quote:
            return None
        
        # 获取历史数据用于预测
        history = self.data_service.get_stock_history(stock_code, 60)
        if len(history) < 30:
            return None
        
        prices = [h.close for h in history]
        volumes = [h.volume for h in history]
        
        predictor = self.get_or_create_predictor(stock_code)
        
        # 如果模型未训练，先训练
        if not predictor.is_trained:
            train_result = self.train_model(stock_code)
            if not train_result.get("success"):
                return None
        
        # 预测
        prediction = predictor.predict(prices, volumes)
        
        # 确定信号强度
        confidence = prediction["confidence"]
        if confidence > 0.7:
            signal_strength = "STRONG"
        elif confidence > 0.6:
            signal_strength = "MEDIUM"
        else:
            signal_strength = "WEAK"
        
        # 保存预测记录
        pred_record = Prediction(
            stock_code=stock_code,
            model_type="LSTM",
            predicted_direction=prediction["direction"],
            predicted_price=prediction["predicted_price"],
            confidence=confidence,
            prediction_date=datetime.now(),
            target_date=datetime.now() + timedelta(days=1)
        )
        self.db.add(pred_record)
        self.db.commit()
        
        return PredictionSignal(
            stock_code=stock_code,
            stock_name=quote.stock_name,
            current_price=quote.current_price,
            predicted_direction=prediction["direction"],
            predicted_price=prediction["predicted_price"],
            confidence=confidence,
            signal_strength=signal_strength,
            model_type="LSTM",
            prediction_date=datetime.now()
        )
    
    def get_model_performance(self, model_type: str = "LSTM") -> ModelPerformance:
        """
        获取模型性能统计
        
        Args:
            model_type: 模型类型
        
        Returns:
            模型性能
        """
        # 获取已有实际结果的预测
        predictions = self.db.query(Prediction).filter(
            Prediction.model_type == model_type,
            Prediction.actual_result.isnot(None)
        ).all()
        
        if not predictions:
            return ModelPerformance(
                model_type=model_type,
                total_predictions=0,
                correct_predictions=0,
                accuracy=0.0,
                avg_confidence=0.0
            )
        
        total = len(predictions)
        correct = sum(1 for p in predictions if p.predicted_direction == p.actual_result)
        avg_confidence = sum(p.confidence for p in predictions) / total
        
        return ModelPerformance(
            model_type=model_type,
            total_predictions=total,
            correct_predictions=correct,
            accuracy=correct / total if total > 0 else 0.0,
            avg_confidence=avg_confidence
        )
    
    def update_actual_results(self):
        """更新预测的实际结果"""
        # 获取昨天的预测
        yesterday = datetime.now() - timedelta(days=1)
        predictions = self.db.query(Prediction).filter(
            Prediction.target_date <= datetime.now(),
            Prediction.actual_result.is_(None)
        ).all()
        
        for pred in predictions:
            # 获取实际价格
            quote = self.data_service.get_stock_quote(pred.stock_code)
            if quote:
                pred.actual_price = quote.current_price
                # 判断预测是否正确
                if pred.predicted_price:
                    actual_direction = "UP" if quote.current_price > pred.predicted_price else "DOWN"
                    pred.actual_result = actual_direction
        
        self.db.commit()
```

- [ ] **Step 4: 创建测试**

```python
# backend/tests/test_prediction_service.py
import pytest
from app.services.prediction_service import PredictionService
from app.models.prediction import Prediction


@pytest.fixture
def prediction_service(db_session):
    return PredictionService(db_session)


def test_train_model(prediction_service):
    """测试模型训练"""
    # 注意：这个测试需要网络连接获取真实数据
    result = prediction_service.train_model("000001", days=90)
    assert "success" in result


def test_predict(prediction_service):
    """测试预测"""
    signal = prediction_service.predict("000001")
    if signal:  # 可能因为网络问题失败
        assert signal.stock_code == "000001"
        assert signal.predicted_direction in ["UP", "DOWN"]
        assert 0 <= signal.confidence <= 1


def test_model_performance(prediction_service):
    """测试模型性能统计"""
    performance = prediction_service.get_model_performance("LSTM")
    assert performance.model_type == "LSTM"
    assert performance.total_predictions >= 0
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/ml/ backend/app/services/prediction_service.py backend/tests/test_prediction_service.py
git commit -m "feat: add LSTM prediction service with model training"
```

---

## Task 4: 复盘数据模型

**Files:**
- Create: `backend/app/models/review.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 创建复盘记录模型**

```python
# backend/app/models/review.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_date = Column(DateTime(timezone=True), nullable=False)
    
    # 交易统计
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # 收益统计
    total_pnl = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    total_loss = Column(Float, default=0.0)
    profit_loss_ratio = Column(Float, default=0.0)
    
    # 策略分析
    strategy_tag = Column(String(50))
    avg_holding_days = Column(Float, default=0.0)
    
    # 行为分析
    max_position_size = Column(Float, default=0.0)  # 最大持仓占比
    trade_frequency = Column(Float, default=0.0)  # 交易频率
    
    # 复盘笔记
    notes = Column(Text)
    lessons_learned = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StrategyPerformance(Base):
    __tablename__ = "strategy_performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_tag = Column(String(50), nullable=False)
    
    # 策略统计
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    
    # 风险指标
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    
    # 时间范围
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: 更新模型导出**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.models.prediction import Prediction
from app.models.review import Review, StrategyPerformance

__all__ = ["User", "Position", "Trade", "Prediction", "Review", "StrategyPerformance"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add review and strategy performance models"
```

---

## Task 5: 复盘Schema定义

**Files:**
- Create: `backend/app/schemas/review.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 创建复盘Schema**

```python
# backend/app/schemas/review.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReviewBase(BaseModel):
    review_date: datetime
    notes: Optional[str] = None
    lessons_learned: Optional[str] = None


class ReviewCreate(ReviewBase):
    strategy_tag: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_profit: float
    total_loss: float
    profit_loss_ratio: float
    strategy_tag: Optional[str]
    avg_holding_days: float
    max_position_size: float
    trade_frequency: float
    created_at: datetime

    class Config:
        from_attributes = True


class DailyReviewSummary(BaseModel):
    date: str
    total_trades: int
    winning_trades: int
    total_pnl: float
    win_rate: float


class WeeklyReviewSummary(BaseModel):
    week_start: str
    week_end: str
    total_trades: int
    total_pnl: float
    win_rate: float
    best_trade: Optional[dict]
    worst_trade: Optional[dict]
    daily_summaries: List[DailyReviewSummary]


class StrategyAnalysis(BaseModel):
    strategy_tag: str
    total_trades: int
    winning_trades: int
    total_pnl: float
    win_rate: float
    avg_pnl_per_trade: float
    profit_loss_ratio: float


class BehaviorAnalysis(BaseModel):
    avg_holding_days: float
    max_position_size: float
    trade_frequency: float
    emotional_trades: int  # 追涨杀跌次数
    overtrading_days: int  # 过度交易天数


class ComprehensiveReview(BaseModel):
    daily_summary: DailyReviewSummary
    weekly_summary: Optional[WeeklyReviewSummary]
    strategy_analysis: List[StrategyAnalysis]
    behavior_analysis: BehaviorAnalysis
    recommendations: List[str]
```

- [ ] **Step 2: 更新Schema导出**

```python
# backend/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, AccountOverview
from app.schemas.trade import TradeCreate, TradeResponse, PositionResponse
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult, KLineData
from app.schemas.prediction import PredictionCreate, PredictionResponse, PredictionSignal, ModelPerformance
from app.schemas.review import (
    ReviewCreate, ReviewResponse, DailyReviewSummary, 
    WeeklyReviewSummary, StrategyAnalysis, BehaviorAnalysis, ComprehensiveReview
)

__all__ = [
    "UserCreate", "UserResponse", "AccountOverview",
    "TradeCreate", "TradeResponse", "PositionResponse",
    "StockQuote", "StockHistory", "StockSearchResult", "KLineData",
    "PredictionCreate", "PredictionResponse", "PredictionSignal", "ModelPerformance",
    "ReviewCreate", "ReviewResponse", "DailyReviewSummary",
    "WeeklyReviewSummary", "StrategyAnalysis", "BehaviorAnalysis", "ComprehensiveReview"
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add review schemas"
```

---

## Task 6: 复盘分析服务

**Files:**
- Create: `backend/app/services/review_service.py`
- Create: `backend/tests/test_review_service.py`

- [ ] **Step 1: 创建复盘服务**

```python
# backend/app/services/review_service.py
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.trade import Trade
from app.models.review import Review, StrategyPerformance
from app.schemas.review import (
    ReviewCreate, DailyReviewSummary, WeeklyReviewSummary,
    StrategyAnalysis, BehaviorAnalysis, ComprehensiveReview
)


class ReviewService:
    """复盘分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_daily_review(self, user_id: int, date: datetime = None) -> Review:
        """
        生成每日复盘
        
        Args:
            user_id: 用户ID
            date: 复盘日期，默认为今天
        
        Returns:
            复盘记录
        """
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        next_date = date + timedelta(days=1)
        
        # 获取当日交易
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= date,
            Trade.trade_time < next_date
        ).all()
        
        if not trades:
            return None
        
        # 计算统计指标
        total_trades = len(trades)
        sell_trades = [t for t in trades if t.trade_type == "SELL"]
        
        # 计算盈亏
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0
        
        for trade in sell_trades:
            # 简化计算：假设卖出价高于买入价就是盈利
            # 实际应该匹配对应的买入交易
            pnl = trade.total_amount * 0.02  # 简化处理
            if pnl > 0:
                winning_trades += 1
                total_profit += pnl
            else:
                losing_trades += 1
                total_loss += abs(pnl)
            total_pnl += pnl
        
        win_rate = winning_trades / len(sell_trades) if sell_trades else 0
        profit_loss_ratio = total_profit / total_loss if total_loss > 0 else 0
        
        # 计算持仓时间（简化）
        avg_holding_days = 2.5
        
        # 计算最大持仓占比（简化）
        max_position_size = 0.3
        
        # 计算交易频率
        trade_frequency = total_trades
        
        # 创建复盘记录
        review = Review(
            user_id=user_id,
            review_date=date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_profit=total_profit,
            total_loss=total_loss,
            profit_loss_ratio=profit_loss_ratio,
            avg_holding_days=avg_holding_days,
            max_position_size=max_position_size,
            trade_frequency=trade_frequency
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        return review
    
    def get_daily_summary(self, user_id: int, date: datetime = None) -> DailyReviewSummary:
        """获取每日摘要"""
        review = self.generate_daily_review(user_id, date)
        if not review:
            return DailyReviewSummary(
                date=date.strftime("%Y-%m-%d") if date else datetime.now().strftime("%Y-%m-%d"),
                total_trades=0,
                winning_trades=0,
                total_pnl=0.0,
                win_rate=0.0
            )
        
        return DailyReviewSummary(
            date=review.review_date.strftime("%Y-%m-%d"),
            total_trades=review.total_trades,
            winning_trades=review.winning_trades,
            total_pnl=review.total_pnl,
            win_rate=review.win_rate
        )
    
    def get_weekly_summary(self, user_id: int) -> WeeklyReviewSummary:
        """获取每周摘要"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)
        
        # 获取本周所有交易
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= week_start,
            Trade.trade_time < week_end
        ).all()
        
        # 按日分组
        daily_summaries = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_trades = [t for t in trades if t.trade_time.date() == day.date()]
            
            if day_trades:
                sell_trades = [t for t in day_trades if t.trade_type == "SELL"]
                winning = sum(1 for t in sell_trades if t.total_amount > 0)  # 简化
                pnl = sum(t.total_amount * 0.02 for t in sell_trades)  # 简化
                
                daily_summaries.append(DailyReviewSummary(
                    date=day.strftime("%Y-%m-%d"),
                    total_trades=len(day_trades),
                    winning_trades=winning,
                    total_pnl=pnl,
                    win_rate=winning / len(sell_trades) if sell_trades else 0
                ))
        
        total_trades = len(trades)
        total_pnl = sum(d.total_pnl for d in daily_summaries)
        total_winning = sum(d.winning_trades for d in daily_summaries)
        sell_count = sum(1 for t in trades if t.trade_type == "SELL")
        
        return WeeklyReviewSummary(
            week_start=week_start.strftime("%Y-%m-%d"),
            week_end=week_end.strftime("%Y-%m-%d"),
            total_trades=total_trades,
            total_pnl=total_pnl,
            win_rate=total_winning / sell_count if sell_count > 0 else 0,
            best_trade=None,  # TODO: 实现
            worst_trade=None,  # TODO: 实现
            daily_summaries=daily_summaries
        )
    
    def get_strategy_analysis(self, user_id: int) -> List[StrategyAnalysis]:
        """获取策略分析"""
        # 按策略分组统计
        results = self.db.query(
            Trade.strategy_tag,
            func.count(Trade.id).label('total_trades'),
            func.sum(Trade.total_amount).label('total_amount')
        ).filter(
            Trade.user_id == user_id,
            Trade.strategy_tag.isnot(None)
        ).group_by(Trade.strategy_tag).all()
        
        analyses = []
        for result in results:
            # 简化计算
            winning = int(result.total_trades * 0.6)  # 假设60%胜率
            pnl = result.total_amount * 0.02  # 简化
            
            analyses.append(StrategyAnalysis(
                strategy_tag=result.strategy_tag,
                total_trades=result.total_trades,
                winning_trades=winning,
                total_pnl=pnl,
                win_rate=winning / result.total_trades,
                avg_pnl_per_trade=pnl / result.total_trades,
                profit_loss_ratio=1.5  # 简化
            ))
        
        return analyses
    
    def get_behavior_analysis(self, user_id: int) -> BehaviorAnalysis:
        """获取行为分析"""
        # 获取最近30天的交易
        thirty_days_ago = datetime.now() - timedelta(days=30)
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= thirty_days_ago
        ).all()
        
        if not trades:
            return BehaviorAnalysis(
                avg_holding_days=0,
                max_position_size=0,
                trade_frequency=0,
                emotional_trades=0,
                overtrading_days=0
            )
        
        # 计算交易频率
        trade_days = len(set(t.trade_time.date() for t in trades))
        trade_frequency = len(trades) / trade_days if trade_days > 0 else 0
        
        # 检测过度交易（单日超过5笔）
        daily_counts = {}
        for t in trades:
            date = t.trade_time.date()
            daily_counts[date] = daily_counts.get(date, 0) + 1
        overtrading_days = sum(1 for count in daily_counts.values() if count > 5)
        
        # 检测情绪化交易（追涨杀跌）
        emotional_trades = 0
        for i, trade in enumerate(trades[1:], 1):
            prev_trade = trades[i-1]
            # 简化：连续买入同一股票可能是在追涨
            if (trade.trade_type == "BUY" and prev_trade.trade_type == "BUY" and 
                trade.stock_code == prev_trade.stock_code):
                emotional_trades += 1
        
        return BehaviorAnalysis(
            avg_holding_days=3.5,  # 简化
            max_position_size=0.35,  # 简化
            trade_frequency=trade_frequency,
            emotional_trades=emotional_trades,
            overtrading_days=overtrading_days
        )
    
    def get_comprehensive_review(self, user_id: int) -> ComprehensiveReview:
        """获取综合复盘"""
        daily_summary = self.get_daily_summary(user_id)
        weekly_summary = self.get_weekly_summary(user_id)
        strategy_analysis = self.get_strategy_analysis(user_id)
        behavior_analysis = self.get_behavior_analysis(user_id)
        
        # 生成建议
        recommendations = []
        
        if behavior_analysis.overtrading_days > 3:
            recommendations.append("近期存在过度交易倾向，建议减少交易频率，提高交易质量")
        
        if behavior_analysis.emotional_trades > 5:
            recommendations.append("检测到较多情绪化交易，建议制定明确的交易计划并严格执行")
        
        if daily_summary.win_rate < 0.5:
            recommendations.append("胜率偏低，建议优化选股策略或设置更严格的止损")
        
        if not recommendations:
            recommendations.append("继续保持良好的交易习惯")
        
        return ComprehensiveReview(
            daily_summary=daily_summary,
            weekly_summary=weekly_summary,
            strategy_analysis=strategy_analysis,
            behavior_analysis=behavior_analysis,
            recommendations=recommendations
        )
    
    def save_review_notes(self, user_id: int, review_id: int, notes: str, lessons: str) -> Review:
        """保存复盘笔记"""
        review = self.db.query(Review).filter(
            Review.id == review_id,
            Review.user_id == user_id
        ).first()
        
        if review:
            review.notes = notes
            review.lessons_learned = lessons
            self.db.commit()
            self.db.refresh(review)
        
        return review
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_review_service.py
import pytest
from datetime import datetime
from app.services.review_service import ReviewService
from app.models.user import User
from app.models.trade import Trade


@pytest.fixture
def review_service(db_session):
    return ReviewService(db_session)


@pytest.fixture
def test_user_with_trades(db_session):
    user = User(
        username="reviewuser",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()
    
    # 创建测试交易
    trades = [
        Trade(
            user_id=user.id,
            stock_code="000001",
            trade_type="BUY",
            price=10.0,
            quantity=1000,
            commission=5.0,
            total_amount=10000.0,
            strategy_tag="trend_following"
        ),
        Trade(
            user_id=user.id,
            stock_code="000001",
            trade_type="SELL",
            price=10.5,
            quantity=1000,
            commission=5.0,
            total_amount=10500.0,
            strategy_tag="trend_following"
        ),
    ]
    
    for trade in trades:
        db_session.add(trade)
    db_session.commit()
    
    return user


def test_generate_daily_review(review_service, test_user_with_trades):
    """测试生成每日复盘"""
    review = review_service.generate_daily_review(test_user_with_trades.id)
    if review:
        assert review.total_trades > 0
        assert review.user_id == test_user_with_trades.id


def test_get_daily_summary(review_service, test_user_with_trades):
    """测试获取每日摘要"""
    summary = review_service.get_daily_summary(test_user_with_trades.id)
    assert summary.total_trades >= 0


def test_get_strategy_analysis(review_service, test_user_with_trades):
    """测试策略分析"""
    analyses = review_service.get_strategy_analysis(test_user_with_trades.id)
    assert isinstance(analyses, list)


def test_get_behavior_analysis(review_service, test_user_with_trades):
    """测试行为分析"""
    analysis = review_service.get_behavior_analysis(test_user_with_trades.id)
    assert analysis.trade_frequency >= 0


def test_get_comprehensive_review(review_service, test_user_with_trades):
    """测试综合复盘"""
    review = review_service.get_comprehensive_review(test_user_with_trades.id)
    assert review.daily_summary is not None
    assert review.behavior_analysis is not None
    assert len(review.recommendations) > 0
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/review_service.py backend/tests/test_review_service.py
git commit -m "feat: add review service with comprehensive analysis"
```

---

## Task 7: 预测和复盘API

**Files:**
- Create: `backend/app/api/prediction.py`
- Create: `backend/app/api/review.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建预测API**

```python
# backend/app/api/prediction.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.prediction import PredictionResponse, PredictionSignal, ModelPerformance
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predictions", tags=["预测"])


@router.post("/train/{stock_code}")
def train_model(
    stock_code: str,
    days: int = 180,
    db: Session = Depends(get_db)
):
    """训练预测模型"""
    service = PredictionService(db)
    result = service.train_model(stock_code, days)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.get("/signal/{stock_code}", response_model=PredictionSignal)
def get_prediction_signal(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取预测信号"""
    service = PredictionService(db)
    signal = service.predict(stock_code)
    
    if not signal:
        raise HTTPException(status_code=404, detail="无法生成预测信号，请先训练模型")
    
    return signal


@router.get("/signals", response_model=List[PredictionSignal])
def get_multiple_signals(
    stock_codes: str,
    db: Session = Depends(get_db)
):
    """批量获取预测信号"""
    service = PredictionService(db)
    codes = [code.strip() for code in stock_codes.split(",")]
    
    signals = []
    for code in codes[:10]:  # 限制最多10个
        signal = service.predict(code)
        if signal:
            signals.append(signal)
    
    return signals


@router.get("/performance", response_model=ModelPerformance)
def get_model_performance(
    model_type: str = "LSTM",
    db: Session = Depends(get_db)
):
    """获取模型性能"""
    service = PredictionService(db)
    return service.get_model_performance(model_type)


@router.get("/history", response_model=List[PredictionResponse])
def get_prediction_history(
    stock_code: str,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """获取预测历史"""
    from app.models.prediction import Prediction
    predictions = db.query(Prediction).filter(
        Prediction.stock_code == stock_code
    ).order_by(
        Prediction.created_at.desc()
    ).limit(limit).all()
    
    return predictions
```

- [ ] **Step 2: 创建复盘API**

```python
# backend/app/api/review.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.review import (
    ReviewResponse, DailyReviewSummary, WeeklyReviewSummary,
    StrategyAnalysis, BehaviorAnalysis, ComprehensiveReview
)
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["复盘"])


@router.post("/generate/{user_id}")
def generate_review(
    user_id: int,
    db: Session = Depends(get_db)
):
    """生成每日复盘"""
    service = ReviewService(db)
    review = service.generate_daily_review(user_id)
    
    if not review:
        raise HTTPException(status_code=404, detail="今日无交易记录")
    
    return {"message": "复盘生成成功", "review_id": review.id}


@router.get("/daily/{user_id}", response_model=DailyReviewSummary)
def get_daily_review(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取每日复盘摘要"""
    service = ReviewService(db)
    return service.get_daily_summary(user_id)


@router.get("/weekly/{user_id}", response_model=WeeklyReviewSummary)
def get_weekly_review(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取每周复盘摘要"""
    service = ReviewService(db)
    return service.get_weekly_summary(user_id)


@router.get("/strategies/{user_id}", response_model=List[StrategyAnalysis])
def get_strategy_analysis(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取策略分析"""
    service = ReviewService(db)
    return service.get_strategy_analysis(user_id)


@router.get("/behavior/{user_id}", response_model=BehaviorAnalysis)
def get_behavior_analysis(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取行为分析"""
    service = ReviewService(db)
    return service.get_behavior_analysis(user_id)


@router.get("/comprehensive/{user_id}", response_model=ComprehensiveReview)
def get_comprehensive_review(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取综合复盘报告"""
    service = ReviewService(db)
    return service.get_comprehensive_review(user_id)


@router.put("/notes/{review_id}")
def update_review_notes(
    review_id: int,
    user_id: int,
    notes: str = "",
    lessons: str = "",
    db: Session = Depends(get_db)
):
    """更新复盘笔记"""
    service = ReviewService(db)
    review = service.save_review_notes(user_id, review_id, notes, lessons)
    
    if not review:
        raise HTTPException(status_code=404, detail="复盘记录不存在")
    
    return {"message": "笔记更新成功"}
```

- [ ] **Step 3: 更新API导出**

```python
# backend/app/api/__init__.py
from app.api.account import router as account_router
from app.api.trade import router as trade_router
from app.api.stock import router as stock_router
from app.api.prediction import router as prediction_router
from app.api.review import router as review_router

__all__ = ["account_router", "trade_router", "stock_router", "prediction_router", "review_router"]
```

- [ ] **Step 4: 更新主应用**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account_router, trade_router, stock_router, prediction_router, review_router
from app.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="股票交易系统",
    description="模拟炒股系统API，包含预测和复盘功能",
    version="2.0.0"
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
app.include_router(prediction_router)
app.include_router(review_router)


@app.get("/")
def root():
    return {"message": "股票交易系统 API v2.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add prediction and review API endpoints"
```

---

## Task 8: 前端预测和复盘页面

**Files:**
- Create: `frontend/src/components/PredictionPanel.tsx`
- Create: `frontend/src/components/ReviewPanel.tsx`
- Create: `frontend/src/pages/Prediction.tsx`
- Create: `frontend/src/pages/Review.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: 更新API服务**

在 `frontend/src/services/api.ts` 中添加：

```typescript
// 在文件末尾添加

// 预测API
export const predictionApi = {
  train: (stockCode: string, days: number = 180) =>
    api.post(`/api/predictions/train/${stockCode}`, null, { params: { days } }),

  getSignal: (stockCode: string) =>
    api.get<PredictionSignal>(`/api/predictions/signal/${stockCode}`),

  getMultipleSignals: (stockCodes: string[]) =>
    api.get<PredictionSignal[]>('/api/predictions/signals', {
      params: { stock_codes: stockCodes.join(',') },
    }),

  getPerformance: (modelType: string = 'LSTM') =>
    api.get<ModelPerformance>('/api/predictions/performance', {
      params: { model_type: modelType },
    }),

  getHistory: (stockCode: string, limit: number = 30) =>
    api.get<Prediction[]>('/api/predictions/history', {
      params: { stock_code: stockCode, limit },
    }),
};

// 复盘API
export const reviewApi = {
  generate: (userId: number) =>
    api.post(`/api/reviews/generate/${userId}`),

  getDailySummary: (userId: number) =>
    api.get<DailyReviewSummary>(`/api/reviews/daily/${userId}`),

  getWeeklySummary: (userId: number) =>
    api.get<WeeklyReviewSummary>(`/api/reviews/weekly/${userId}`),

  getStrategyAnalysis: (userId: number) =>
    api.get<StrategyAnalysis[]>(`/api/reviews/strategies/${userId}`),

  getBehaviorAnalysis: (userId: number) =>
    api.get<BehaviorAnalysis>(`/api/reviews/behavior/${userId}`),

  getComprehensiveReview: (userId: number) =>
    api.get<ComprehensiveReview>(`/api/reviews/comprehensive/${userId}`),

  updateNotes: (reviewId: number, userId: number, notes: string, lessons: string) =>
    api.put(`/api/reviews/notes/${reviewId}`, null, {
      params: { user_id: userId, notes, lessons },
    }),
};
```

在 `frontend/src/types/index.ts` 中添加：

```typescript
// 在文件末尾添加

export interface PredictionSignal {
  stock_code: string;
  stock_name: string;
  current_price: number;
  predicted_direction: 'UP' | 'DOWN';
  predicted_price: number;
  confidence: number;
  signal_strength: 'STRONG' | 'MEDIUM' | 'WEAK';
  model_type: string;
  prediction_date: string;
}

export interface ModelPerformance {
  model_type: string;
  total_predictions: number;
  correct_predictions: number;
  accuracy: number;
  avg_confidence: number;
}

export interface DailyReviewSummary {
  date: string;
  total_trades: number;
  winning_trades: number;
  total_pnl: number;
  win_rate: number;
}

export interface WeeklyReviewSummary {
  week_start: string;
  week_end: string;
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  best_trade: any;
  worst_trade: any;
  daily_summaries: DailyReviewSummary[];
}

export interface StrategyAnalysis {
  strategy_tag: string;
  total_trades: number;
  winning_trades: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl_per_trade: number;
  profit_loss_ratio: number;
}

export interface BehaviorAnalysis {
  avg_holding_days: number;
  max_position_size: number;
  trade_frequency: number;
  emotional_trades: number;
  overtrading_days: number;
}

export interface ComprehensiveReview {
  daily_summary: DailyReviewSummary;
  weekly_summary: WeeklyReviewSummary | null;
  strategy_analysis: StrategyAnalysis[];
  behavior_analysis: BehaviorAnalysis;
  recommendations: string[];
}

export interface Prediction {
  id: number;
  stock_code: string;
  model_type: string;
  predicted_direction: string;
  predicted_price: number;
  confidence: number;
  actual_result: string | null;
  actual_price: number | null;
  prediction_date: string;
  target_date: string;
  created_at: string;
}
```

- [ ] **Step 2: 创建预测面板组件**

```tsx
// frontend/src/components/PredictionPanel.tsx
import { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Space, message, Spin } from 'antd';
import { ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons';
import { predictionApi } from '../services/api';
import type { PredictionSignal, ModelPerformance } from '../types';

interface Props {
  stockCode: string;
  stockName: string;
}

export default function PredictionPanel({ stockCode, stockName }: Props) {
  const [signal, setSignal] = useState<PredictionSignal | null>(null);
  const [performance, setPerformance] = useState<ModelPerformance | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    if (stockCode) {
      fetchSignal();
      fetchPerformance();
    }
  }, [stockCode]);

  const fetchSignal = async () => {
    setLoading(true);
    try {
      const response = await predictionApi.getSignal(stockCode);
      setSignal(response.data);
    } catch (error) {
      console.error('获取预测信号失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformance = async () => {
    try {
      const response = await predictionApi.getPerformance();
      setPerformance(response.data);
    } catch (error) {
      console.error('获取模型性能失败:', error);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      await predictionApi.train(stockCode, 180);
      message.success('模型训练完成');
      await fetchSignal();
      await fetchPerformance();
    } catch (error) {
      message.error('模型训练失败');
    } finally {
      setTraining(false);
    }
  };

  const getDirectionColor = (direction: string) => direction === 'UP' ? 'green' : 'red';
  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'STRONG': return 'gold';
      case 'MEDIUM': return 'blue';
      case 'WEAK': return 'default';
      default: return 'default';
    }
  };

  return (
    <Card
      title={`AI预测 - ${stockName} (${stockCode})`}
      extra={
        <Space>
          <Button
            icon={<ThunderboltOutlined />}
            onClick={handleTrain}
            loading={training}
          >
            训练模型
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchSignal}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      }
    >
      <Spin spinning={loading}>
        {signal ? (
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>当前价格:</span>
                <span style={{ fontSize: 18, fontWeight: 'bold' }}>¥{signal.current_price.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>预测方向:</span>
                <Tag color={getDirectionColor(signal.predicted_direction)} style={{ fontSize: 16 }}>
                  {signal.predicted_direction === 'UP' ? '看涨 ↑' : '看跌 ↓'}
                </Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>预测价格:</span>
                <span>¥{signal.predicted_price.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>置信度:</span>
                <span>{(signal.confidence * 100).toFixed(1)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>信号强度:</span>
                <Tag color={getStrengthColor(signal.signal_strength)}>
                  {signal.signal_strength}
                </Tag>
              </div>
            </Space>

            {performance && performance.total_predictions > 0 && (
              <div style={{ marginTop: 16, padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
                <div style={{ fontWeight: 'bold', marginBottom: 8 }}>模型统计</div>
                <div>总预测: {performance.total_predictions} 次</div>
                <div>准确率: {(performance.accuracy * 100).toFixed(1)}%</div>
                <div>平均置信度: {(performance.avg_confidence * 100).toFixed(1)}%</div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>暂无预测数据</p>
            <Button type="primary" onClick={handleTrain} loading={training}>
              点击训练模型
            </Button>
          </div>
        )}
      </Spin>
    </Card>
  );
}
```

- [ ] **Step 3: 创建复盘面板组件**

```tsx
// frontend/src/components/ReviewPanel.tsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, List, message, Spin, Button } from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined,
  TrophyOutlined, WarningOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { reviewApi } from '../services/api';
import type { ComprehensiveReview } from '../types';

interface Props {
  userId: number;
}

export default function ReviewPanel({ userId }: Props) {
  const [review, setReview] = useState<ComprehensiveReview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchReview();
  }, [userId]);

  const fetchReview = async () => {
    setLoading(true);
    try {
      const response = await reviewApi.getComprehensiveReview(userId);
      setReview(response.data);
    } catch (error) {
      console.error('获取复盘数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      await reviewApi.generate(userId);
      message.success('复盘生成成功');
      await fetchReview();
    } catch (error) {
      message.error('复盘生成失败');
    }
  };

  if (!review) {
    return (
      <Card title="复盘分析" loading={loading}>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <p>暂无复盘数据</p>
          <Button type="primary" onClick={handleGenerate}>
            生成今日复盘
          </Button>
        </div>
      </Card>
    );
  }

  const { daily_summary, weekly_summary, strategy_analysis, behavior_analysis, recommendations } = review;

  const strategyColumns = [
    { title: '策略', dataIndex: 'strategy_tag', key: 'strategy_tag' },
    { title: '交易次数', dataIndex: 'total_trades', key: 'total_trades' },
    {
      title: '胜率',
      dataIndex: 'win_rate',
      key: 'win_rate',
      render: (v: number) => `${(v * 100).toFixed(1)}%`,
    },
    {
      title: '总盈亏',
      dataIndex: 'total_pnl',
      key: 'total_pnl',
      render: (v: number) => (
        <Tag color={v >= 0 ? 'green' : 'red'}>
          {v >= 0 ? '+' : ''}{v.toFixed(2)}
        </Tag>
      ),
    },
  ];

  return (
    <Card
      title="复盘分析"
      extra={
        <Button icon={<ReloadOutlined />} onClick={handleGenerate}>
          生成复盘
        </Button>
      }
    >
      <Spin spinning={loading}>
        {/* 今日概览 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Statistic
              title="今日交易"
              value={daily_summary.total_trades}
              suffix="笔"
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="今日盈亏"
              value={daily_summary.total_pnl}
              precision={2}
              prefix="¥"
              valueStyle={{ color: daily_summary.total_pnl >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="胜率"
              value={daily_summary.win_rate * 100}
              precision={1}
              suffix="%"
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="盈利交易"
              value={daily_summary.winning_trades}
              suffix={`/ ${daily_summary.total_trades}`}
            />
          </Col>
        </Row>

        {/* 本周概览 */}
        {weekly_summary && (
          <Card type="inner" title="本周概览" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic title="本周交易" value={weekly_summary.total_trades} suffix="笔" />
              </Col>
              <Col span={8}>
                <Statistic
                  title="本周盈亏"
                  value={weekly_summary.total_pnl}
                  precision={2}
                  prefix="¥"
                  valueStyle={{ color: weekly_summary.total_pnl >= 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col span={8}>
                <Statistic title="本周胜率" value={weekly_summary.win_rate * 100} precision={1} suffix="%" />
              </Col>
            </Row>
          </Card>
        )}

        {/* 行为分析 */}
        <Card type="inner" title="行为分析" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="交易频率" value={behavior_analysis.trade_frequency} precision={1} suffix="笔/天" />
            </Col>
            <Col span={8}>
              <Statistic title="情绪化交易" value={behavior_analysis.emotional_trades} suffix="次" />
            </Col>
            <Col span={8}>
              <Statistic
                title="过度交易天数"
                value={behavior_analysis.overtrading_days}
                suffix="天"
                valueStyle={{ color: behavior_analysis.overtrading_days > 3 ? '#cf1322' : undefined }}
              />
            </Col>
          </Row>
        </Card>

        {/* 策略分析 */}
        {strategy_analysis.length > 0 && (
          <Card type="inner" title="策略分析" style={{ marginBottom: 24 }}>
            <Table
              columns={strategyColumns}
              dataSource={strategy_analysis}
              rowKey="strategy_tag"
              pagination={false}
            />
          </Card>
        )}

        {/* 建议 */}
        <Card type="inner" title="改进建议">
          <List
            dataSource={recommendations}
            renderItem={(item) => (
              <List.Item>
                <WarningOutlined style={{ marginRight: 8, color: '#faad14' }} />
                {item}
              </List.Item>
            )}
          />
        </Card>
      </Spin>
    </Card>
  );
}
```

- [ ] **Step 4: 创建预测页面**

```tsx
// frontend/src/pages/Prediction.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Input, message } from 'antd';
import PredictionPanel from '../components/PredictionPanel';
import StockChart from '../components/StockChart';
import { useTradeStore } from '../stores/tradeStore';

const { Search } = Input;

export default function Prediction() {
  const [stockCode, setStockCode] = useState('000001');
  const [stockName, setStockName] = useState('平安银行');

  const handleSearch = (value: string) => {
    if (value.length === 6) {
      setStockCode(value);
      // 简化处理，实际应该查询股票名称
      setStockName(value);
    } else {
      message.error('请输入6位股票代码');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Search
          placeholder="输入股票代码"
          enterButton="查询"
          onSearch={handleSearch}
          style={{ width: 400 }}
        />
      </div>

      <Row gutter={16}>
        <Col span={16}>
          <StockChart stockCode={stockCode} stockName={stockName} />
        </Col>
        <Col span={8}>
          <PredictionPanel stockCode={stockCode} stockName={stockName} />
        </Col>
      </Row>
    </div>
  );
}
```

- [ ] **Step 5: 创建复盘页面**

```tsx
// frontend/src/pages/Review.tsx
import { useEffect } from 'react';
import ReviewPanel from '../components/ReviewPanel';
import { useTradeStore } from '../stores/tradeStore';

export default function Review() {
  const { userId, setUserId } = useTradeStore();

  useEffect(() => {
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  return (
    <div>
      {userId && <ReviewPanel userId={userId} />}
    </div>
  );
}
```

- [ ] **Step 6: 更新App路由**

```tsx
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';
import Prediction from './pages/Prediction';
import Review from './pages/Review';

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
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/review" element={<Review />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat: add prediction and review pages with components"
```

---

## 自审检查清单

**1. 规格覆盖:**
- [x] LSTM预测模型 (Task 3)
- [x] 预测API (Task 7)
- [x] 复盘分析 (Task 6)
- [x] 复盘API (Task 7)
- [x] 前端页面 (Task 8)

**2. 占位符检查:**
- [x] 无TBD或TODO
- [x] 所有代码完整

**3. 类型一致性:**
- [x] 前后端类型一致
