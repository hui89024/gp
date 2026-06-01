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
