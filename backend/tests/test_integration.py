import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.api.deps import get_db


@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_full_trading_flow(client):
    """测试完整交易流程"""
    # 1. 注册用户
    response = client.post("/api/v1/auth/register", json={
        "username": "trader",
        "email": "trader@example.com",
        "password": "password123"
    })
    assert response.status_code == 200

    # 2. 登录
    response = client.post("/api/v1/auth/login", json={
        "username": "trader",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. 创建A股账户
    response = client.post("/api/v1/accounts", json={
        "market": "CN",
        "currency": "CNY",
        "initial_capital": 500000.0
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["market"] == "CN"

    # 4. 创建美股账户
    response = client.post("/api/v1/accounts", json={
        "market": "US",
        "currency": "USD",
        "initial_capital": 100000.0,
        "exchange_rate": 7.2
    }, headers=headers)
    assert response.status_code == 200

    # 5. 获取账户列表
    response = client.get("/api/v1/accounts", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["accounts"]) == 2
    assert data["total_assets_cny"] > 0

    # 6. 创建限价买入订单
    response = client.post("/api/v1/orders", json={
        "market": "CN",
        "stock_code": "000001",
        "stock_name": "平安银行",
        "order_type": "LIMIT",
        "direction": "BUY",
        "price": 10.0,
        "quantity": 1000
    }, headers=headers)
    assert response.status_code == 200
    order_id = response.json()["id"]

    # 7. 获取订单列表
    response = client.get("/api/v1/orders", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["orders"]) > 0

    # 8. 取消订单
    response = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert response.status_code == 200
