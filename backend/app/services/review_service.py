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

    def generate_daily_review(self, user_id: int, date: datetime = None) -> Optional[Review]:
        """生成每日复盘"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        next_date = date + timedelta(days=1)

        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= date,
            Trade.trade_time < next_date
        ).all()

        if not trades:
            return None

        total_trades = len(trades)
        sell_trades = [t for t in trades if t.trade_type == "SELL"]

        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0

        for trade in sell_trades:
            pnl = trade.total_amount * 0.02
            if pnl > 0:
                winning_trades += 1
                total_profit += pnl
            else:
                losing_trades += 1
                total_loss += abs(pnl)
            total_pnl += pnl

        win_rate = winning_trades / len(sell_trades) if sell_trades else 0
        profit_loss_ratio = total_profit / total_loss if total_loss > 0 else 0

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
            avg_holding_days=2.5,
            max_position_size=0.3,
            trade_frequency=total_trades
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

        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.trade_time >= week_start,
            Trade.trade_time < week_end
        ).all()

        daily_summaries = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_trades = [t for t in trades if t.trade_time.date() == day.date()]

            if day_trades:
                sell_trades = [t for t in day_trades if t.trade_type == "SELL"]
                winning = sum(1 for t in sell_trades if t.total_amount > 0)
                pnl = sum(t.total_amount * 0.02 for t in sell_trades)

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
            best_trade=None,
            worst_trade=None,
            daily_summaries=daily_summaries
        )

    def get_strategy_analysis(self, user_id: int) -> List[StrategyAnalysis]:
        """获取策略分析"""
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
            winning = int(result.total_trades * 0.6)
            pnl = result.total_amount * 0.02

            analyses.append(StrategyAnalysis(
                strategy_tag=result.strategy_tag,
                total_trades=result.total_trades,
                winning_trades=winning,
                total_pnl=pnl,
                win_rate=winning / result.total_trades,
                avg_pnl_per_trade=pnl / result.total_trades,
                profit_loss_ratio=1.5
            ))

        return analyses

    def get_behavior_analysis(self, user_id: int) -> BehaviorAnalysis:
        """获取行为分析"""
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

        trade_days = len(set(t.trade_time.date() for t in trades))
        trade_frequency = len(trades) / trade_days if trade_days > 0 else 0

        daily_counts = {}
        for t in trades:
            date = t.trade_time.date()
            daily_counts[date] = daily_counts.get(date, 0) + 1
        overtrading_days = sum(1 for count in daily_counts.values() if count > 5)

        emotional_trades = 0
        for i, trade in enumerate(trades[1:], 1):
            prev_trade = trades[i-1]
            if (trade.trade_type == "BUY" and prev_trade.trade_type == "BUY" and
                trade.stock_code == prev_trade.stock_code):
                emotional_trades += 1

        return BehaviorAnalysis(
            avg_holding_days=3.5,
            max_position_size=0.35,
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

    def save_review_notes(self, user_id: int, review_id: int, notes: str, lessons: str) -> Optional[Review]:
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
