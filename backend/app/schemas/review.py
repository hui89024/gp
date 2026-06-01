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
    emotional_trades: int
    overtrading_days: int


class ComprehensiveReview(BaseModel):
    daily_summary: DailyReviewSummary
    weekly_summary: Optional[WeeklyReviewSummary]
    strategy_analysis: List[StrategyAnalysis]
    behavior_analysis: BehaviorAnalysis
    recommendations: List[str]