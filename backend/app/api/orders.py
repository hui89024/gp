from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderList
from app.services.order_service import OrderService
from app.services.matching_engine import MarketData

router = APIRouter(prefix="/api/v1/orders", tags=["订单"])


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建订单"""
    service = OrderService(db)
    try:
        order = service.create_order(current_user.id, order_data)
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=OrderList)
async def get_orders(
    market: Optional[str] = None,
    order_status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    service = OrderService(db)
    orders = service.get_orders(current_user.id, market, order_status, limit)
    return OrderList(orders=orders, total=len(orders))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单详情"""
    from app.models.order import Order
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    return order


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消订单"""
    service = OrderService(db)
    result = service.cancel_order(order_id, current_user.id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result


@router.post("/{order_id}/execute")
async def execute_order(
    order_id: int,
    current_price: float,
    bid_price: Optional[float] = None,
    ask_price: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行订单（模拟撮合）"""
    from app.models.order import Order
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    market_data = MarketData(
        stock_code=order.stock_code,
        current_price=current_price,
        bid_price=bid_price or current_price * 0.999,
        ask_price=ask_price or current_price * 1.001,
        volume=1000000
    )

    service = OrderService(db)
    result = service.execute_order(order_id, market_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result
