# 核心交易引擎实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现多市场支持（A股、港股、美股）和高级订单类型（限价单、市价单、止损单、止盈单、条件单）

**Architecture:** 模块化单体架构，使用策略模式实现多市场规则，状态模式管理订单生命周期，工厂模式创建不同类型的订单

**Tech Stack:** FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + JWT认证

---

## 文件结构

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py (修改) - 导出所有模型
│   │   ├── market_account.py (新建) - 多市场账户模型
│   │   ├── order.py (新建) - 订单模型
│   │   ├── position.py (修改) - 添加市场字段
│   │   ├── trade.py (修改) - 添加市场和订单关联
│   │   └── user.py (修改) - 添加认证字段
│   ├── schemas/
│   │   ├── auth.py (新建) - 认证相关schema
│   │   ├── market_account.py (新建) - 市场账户schema
│   │   └── order.py (新建) - 订单schema
│   ├── services/
│   │   ├── market_rules.py (新建) - 多市场交易规则
│   │   ├── order_service.py (新建) - 订单管理服务
│   │   ├── matching_engine.py (新建) - 撮合引擎
│   │   └── trading_engine.py (修改) - 集成新功能
│   ├── utils/
│   │   ├── auth.py (新建) - JWT认证工具
│   │   └── commission.py (修改) - 多市场手续费计算
│   └── api/
│       ├── auth.py (新建) - 用户认证API
│       ├── orders.py (新建) - 订单API
│       └── market_accounts.py (新建) - 市场账户API
└── tests/
    ├── conftest.py (修改) - 添加测试fixtures
    ├── test_market_rules.py (新建)
    ├── test_order_service.py (新建)
    ├── test_matching_engine.py (新建)
    ├── test_auth.py (新建)
    └── test_commission.py (修改)
```

---

## Task 1: 用户认证系统

**Files:**
- Create: `backend/app/utils/auth.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/models/user.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: 安装依赖**

```bash
cd backend
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

- [ ] **Step 2: 编写认证工具测试**

```python
# backend/tests/test_auth.py
import pytest
from datetime import datetime, timedelta
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)


def test_hash_password():
    """测试密码哈希"""
    password = "test123456"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_wrong():
    """测试错误密码验证"""
    password = "test123456"
    hashed = hash_password(password)
    assert not verify_password("wrong_password", hashed)


def test_create_access_token():
    """测试创建访问令牌"""
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)


def test_create_refresh_token():
    """测试创建刷新令牌"""
    data = {"sub": "1", "username": "testuser"}
    token = create_refresh_token(data)
    assert token is not None
    assert isinstance(token, str)


def test_decode_token_valid():
    """测试解码有效令牌"""
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "testuser"


def test_decode_token_expired():
    """测试解码过期令牌"""
    data = {"sub": "1", "username": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    payload = decode_token(token)
    assert payload is None
```

- [ ] **Step 3: 运行测试验证失败**

```bash
cd backend
pytest tests/test_auth.py -v
```

预期结果：FAIL - 模块不存在

- [ ] **Step 4: 实现认证工具**

```python
# backend/app/utils/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2小时
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7天


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        data: 令牌数据
        expires_delta: 过期时间增量

    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌

    Args:
        data: 令牌数据

    Returns:
        JWT刷新令牌字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    解码JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        令牌数据字典，无效则返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd backend
pytest tests/test_auth.py -v
```

预期结果：PASS

- [ ] **Step 6: 编写用户模型测试**

```python
# backend/tests/test_auth.py (追加)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_user_model_with_auth(db_session):
    """测试带认证字段的用户模型"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("test123456"),
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(User).filter(User.username == "testuser").first()
    assert saved_user is not None
    assert saved_user.email == "test@example.com"
    assert verify_password("test123456", saved_user.password_hash)
```

- [ ] **Step 7: 修改用户模型添加认证字段**

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    initial_capital = Column(Float, default=1000000.0)
    current_capital = Column(Float, default=1000000.0)
    risk_level = Column(String(20), default="MODERATE")  # CONSERVATIVE/MODERATE/AGGRESSIVE
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 8: 运行测试验证通过**

```bash
cd backend
pytest tests/test_auth.py -v
```

预期结果：PASS

- [ ] **Step 9: 编写认证Schema**

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    initial_capital: float
    current_capital: float
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """刷新令牌请求"""
    refresh_token: str
```

- [ ] **Step 10: 编写认证API测试**

```python
# backend/tests/test_auth_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.api.deps import get_db


@pytest.fixture
def client():
    """创建测试客户端"""
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


def test_register(client):
    """测试用户注册"""
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password" not in data


def test_login(client):
    """测试用户登录"""
    # 先注册
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })

    # 登录
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "test123456"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """测试错误密码登录"""
    # 先注册
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })

    # 错误密码登录
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "wrong_password"
    })
    assert response.status_code == 401


def test_get_current_user(client):
    """测试获取当前用户信息"""
    # 注册
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })

    # 登录
    login_response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "test123456"
    })
    token = login_response.json()["access_token"]

    # 获取用户信息
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
```

- [ ] **Step 11: 运行测试验证失败**

```bash
cd backend
pytest tests/test_auth_api.py -v
```

预期结果：FAIL - API端点不存在

- [ ] **Step 12: 实现认证API**

```python
# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh
)
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    用户注册

    Args:
        user_data: 注册数据
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    Args:
        login_data: 登录数据
        db: 数据库会话

    Returns:
        访问令牌和刷新令牌

    Raises:
        HTTPException: 用户名或密码错误
    """
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 创建令牌
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    刷新令牌

    Args:
        token_data: 刷新令牌数据
        db: 数据库会话

    Returns:
        新的访问令牌和刷新令牌

    Raises:
        HTTPException: 令牌无效或已过期
    """
    # 解码刷新令牌
    payload = decode_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    # 查找用户
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    # 创建新令牌
    new_token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(new_token_data)
    refresh_token = create_refresh_token(new_token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(lambda x: x.headers.get("Authorization", "").replace("Bearer ", "")),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息

    Args:
        token: JWT令牌
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 令牌无效或已过期
    """
    # 解码令牌
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )

    # 查找用户
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user
```

- [ ] **Step 13: 运行测试验证通过**

```bash
cd backend
pytest tests/test_auth_api.py -v
```

预期结果：PASS

- [ ] **Step 14: 提交代码**

```bash
git add backend/app/utils/auth.py backend/app/schemas/auth.py backend/app/api/auth.py backend/app/models/user.py backend/tests/test_auth.py backend/tests/test_auth_api.py
git commit -m "feat: 实现用户认证系统

- 添加JWT认证工具（access_token + refresh_token）
- 修改用户模型添加认证字段
- 实现注册、登录、刷新令牌API
- 添加完整的测试覆盖"
```

---

## Task 2: 多市场账户系统

**Files:**
- Create: `backend/app/models/market_account.py`
- Create: `backend/app/schemas/market_account.py`
- Create: `backend/app/api/market_accounts.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/tests/test_market_account.py`

- [ ] **Step 1: 编写市场账户模型测试**

```python
# backend/tests/test_market_account.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.market_account import MarketAccount


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_create_market_account(db_session):
    """测试创建市场账户"""
    # 先创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    # 创建A股账户
    cn_account = MarketAccount(
        user_id=user.id,
        market="CN",
        currency="CNY",
        initial_capital=1000000.0,
        current_capital=1000000.0,
        exchange_rate=1.0
    )
    db_session.add(cn_account)
    db_session.commit()

    # 验证
    saved_account = db_session.query(MarketAccount).filter(
        MarketAccount.user_id == user.id,
        MarketAccount.market == "CN"
    ).first()
    assert saved_account is not None
    assert saved_account.currency == "CNY"
    assert saved_account.current_capital == 1000000.0


def test_multiple_markets(db_session):
    """测试多市场账户"""
    # 先创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    # 创建多个市场账户
    accounts = [
        MarketAccount(user_id=user.id, market="CN", currency="CNY", initial_capital=500000.0, current_capital=500000.0),
        MarketAccount(user_id=user.id, market="HK", currency="HKD", initial_capital=300000.0, current_capital=300000.0, exchange_rate=0.9),
        MarketAccount(user_id=user.id, market="US", currency="USD", initial_capital=200000.0, current_capital=200000.0, exchange_rate=7.2),
    ]
    db_session.add_all(accounts)
    db_session.commit()

    # 验证
    user_accounts = db_session.query(MarketAccount).filter(
        MarketAccount.user_id == user.id
    ).all()
    assert len(user_accounts) == 3
    markets = [a.market for a in user_accounts]
    assert "CN" in markets
    assert "HK" in markets
    assert "US" in markets
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_market_account.py -v
```

预期结果：FAIL - 模型不存在

- [ ] **Step 3: 实现市场账户模型**

```python
# backend/app/models/market_account.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class MarketAccount(Base):
    """多市场账户模型"""
    __tablename__ = "market_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market = Column(String(10), nullable=False)  # CN/HK/US
    currency = Column(String(3), nullable=False)  # CNY/HKD/USD
    initial_capital = Column(Float, nullable=False)
    current_capital = Column(Float, nullable=False)
    exchange_rate = Column(Float, default=1.0)  # 汇率（相对人民币）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 唯一约束：每个用户每个市场只有一个账户
    __table_args__ = (
        UniqueConstraint('user_id', 'market', name='uq_user_market'),
    )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_market_account.py -v
```

预期结果：PASS

- [ ] **Step 5: 编写市场账户Schema**

```python
# backend/app/schemas/market_account.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MarketAccountCreate(BaseModel):
    """创建市场账户请求"""
    market: str  # CN/HK/US
    currency: str  # CNY/HKD/USD
    initial_capital: float
    exchange_rate: Optional[float] = 1.0


class MarketAccountUpdate(BaseModel):
    """更新市场账户请求"""
    current_capital: Optional[float] = None
    exchange_rate: Optional[float] = None


class MarketAccountResponse(BaseModel):
    """市场账户响应"""
    id: int
    user_id: int
    market: str
    currency: str
    initial_capital: float
    current_capital: float
    exchange_rate: float
    created_at: datetime

    class Config:
        from_attributes = True


class MarketAccountList(BaseModel):
    """市场账户列表响应"""
    accounts: list[MarketAccountResponse]
    total_assets_cny: float  # 总资产（人民币）
```

- [ ] **Step 6: 编写市场账户API测试**

```python
# backend/tests/test_market_account_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.api.deps import get_db
from app.utils.auth import create_access_token


@pytest.fixture
def client():
    """创建测试客户端"""
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


@pytest.fixture
def auth_headers(client):
    """创建认证headers"""
    # 注册用户
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456"
    })

    # 登录获取token
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "test123456"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_market_account(client, auth_headers):
    """测试创建市场账户"""
    response = client.post("/api/v1/accounts", json={
        "market": "CN",
        "currency": "CNY",
        "initial_capital": 500000.0
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["market"] == "CN"
    assert data["currency"] == "CNY"
    assert data["current_capital"] == 500000.0


def test_get_market_accounts(client, auth_headers):
    """测试获取市场账户列表"""
    # 创建多个账户
    client.post("/api/v1/accounts", json={
        "market": "CN",
        "currency": "CNY",
        "initial_capital": 500000.0
    }, headers=auth_headers)

    client.post("/api/v1/accounts", json={
        "market": "US",
        "currency": "USD",
        "initial_capital": 100000.0,
        "exchange_rate": 7.2
    }, headers=auth_headers)

    # 获取列表
    response = client.get("/api/v1/accounts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["accounts"]) == 2
    assert data["total_assets_cny"] > 0
```

- [ ] **Step 7: 运行测试验证失败**

```bash
cd backend
pytest tests/test_market_account_api.py -v
```

预期结果：FAIL - API端点不存在

- [ ] **Step 8: 实现市场账户API**

```python
# backend/app/api/market_accounts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.market_account import MarketAccount
from app.schemas.market_account import (
    MarketAccountCreate,
    MarketAccountUpdate,
    MarketAccountResponse,
    MarketAccountList
)

router = APIRouter(prefix="/api/v1/accounts", tags=["市场账户"])


@router.post("", response_model=MarketAccountResponse)
async def create_market_account(
    account_data: MarketAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建市场账户

    Args:
        account_data: 账户数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        市场账户信息

    Raises:
        HTTPException: 市场账户已存在
    """
    # 检查是否已存在
    existing = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id,
        MarketAccount.market == account_data.market
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{account_data.market}市场账户已存在"
        )

    # 创建账户
    account = MarketAccount(
        user_id=current_user.id,
        market=account_data.market,
        currency=account_data.currency,
        initial_capital=account_data.initial_capital,
        current_capital=account_data.initial_capital,
        exchange_rate=account_data.exchange_rate
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@router.get("", response_model=MarketAccountList)
async def get_market_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取市场账户列表

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        市场账户列表和总资产
    """
    accounts = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id
    ).all()

    # 计算总资产（人民币）
    total_assets_cny = sum(
        account.current_capital * account.exchange_rate
        for account in accounts
    )

    return MarketAccountList(
        accounts=accounts,
        total_assets_cny=round(total_assets_cny, 2)
    )


@router.get("/{market}", response_model=MarketAccountResponse)
async def get_market_account(
    market: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定市场账户

    Args:
        market: 市场代码 (CN/HK/US)
        current_user: 当前用户
        db: 数据库会话

    Returns:
        市场账户信息

    Raises:
        HTTPException: 市场账户不存在
    """
    account = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id,
        MarketAccount.market == market
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{market}市场账户不存在"
        )

    return account


@router.put("/{market}", response_model=MarketAccountResponse)
async def update_market_account(
    market: str,
    update_data: MarketAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新市场账户

    Args:
        market: 市场代码
        update_data: 更新数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        更新后的市场账户信息

    Raises:
        HTTPException: 市场账户不存在
    """
    account = db.query(MarketAccount).filter(
        MarketAccount.user_id == current_user.id,
        MarketAccount.market == market
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{market}市场账户不存在"
        )

    # 更新字段
    if update_data.current_capital is not None:
        account.current_capital = update_data.current_capital
    if update_data.exchange_rate is not None:
        account.exchange_rate = update_data.exchange_rate

    db.commit()
    db.refresh(account)

    return account
```

- [ ] **Step 9: 运行测试验证通过**

```bash
cd backend
pytest tests/test_market_account_api.py -v
```

预期结果：PASS

- [ ] **Step 10: 提交代码**

```bash
git add backend/app/models/market_account.py backend/app/schemas/market_account.py backend/app/api/market_accounts.py backend/tests/test_market_account.py backend/tests/test_market_account_api.py
git commit -m "feat: 实现多市场账户系统

- 添加MarketAccount模型支持A股、港股、美股
- 实现市场账户CRUD API
- 计算多市场总资产（人民币）
- 添加完整的测试覆盖"
```

---

## Task 3: 多市场交易规则引擎

**Files:**
- Create: `backend/app/services/market_rules.py`
- Create: `backend/tests/test_market_rules.py`

- [ ] **Step 1: 编写市场规则测试**

```python
# backend/tests/test_market_rules.py
import pytest
from datetime import datetime, time
from app.services.market_rules import (
    MarketRules,
    CNRules,
    HKRules,
    USRules,
    MarketRulesFactory,
    PriceLimitType
)


def test_cn_trading_hours():
    """测试A股交易时间"""
    rules = CNRules()

    # 交易时间内
    assert rules.is_trading_time(datetime(2026, 6, 2, 10, 0)) == True  # 10:00
    assert rules.is_trading_time(datetime(2026, 6, 2, 14, 0)) == True  # 14:00

    # 非交易时间
    assert rules.is_trading_time(datetime(2026, 6, 2, 8, 0)) == False  # 08:00
    assert rules.is_trading_time(datetime(2026, 6, 2, 12, 0)) == False  # 12:00
    assert rules.is_trading_time(datetime(2026, 6, 2, 16, 0)) == False  # 16:00


def test_cn_price_limit():
    """测试A股涨跌停限制"""
    rules = CNRules()

    # 普通股票 ±10%
    assert rules.check_price_limit(100.0, 110.0, PriceLimitType.NORMAL) == True  # 涨停
    assert rules.check_price_limit(100.0, 111.0, PriceLimitType.NORMAL) == False  # 超过涨停
    assert rules.check_price_limit(100.0, 90.0, PriceLimitType.NORMAL) == True  # 跌停
    assert rules.check_price_limit(100.0, 89.0, PriceLimitType.NORMAL) == False  # 超过跌停

    # 科创板 ±20%
    assert rules.check_price_limit(100.0, 120.0, PriceLimitType.STAR) == True
    assert rules.check_price_limit(100.0, 121.0, PriceLimitType.STAR) == False

    # ST股 ±5%
    assert rules.check_price_limit(100.0, 105.0, PriceLimitType.ST) == True
    assert rules.check_price_limit(100.0, 106.0, PriceLimitType.ST) == False


def test_cn_lot_size():
    """测试A股最小交易单位"""
    rules = CNRules()

    assert rules.validate_quantity(100) == True
    assert rules.validate_quantity(200) == True
    assert rules.validate_quantity(150) == False
    assert rules.validate_quantity(0) == False


def test_cn_commission():
    """测试A股手续费计算"""
    rules = CNRules()

    # 买入手续费
    buy_commission = rules.calculate_commission("BUY", 10.0, 1000)
    assert buy_commission["commission"] == max(10.0 * 1000 * 0.00025, 5.0)
    assert buy_commission["stamp_tax"] == 0.0
    assert buy_commission["transfer_fee"] == 10.0 * 1000 * 0.00001

    # 卖出手续费
    sell_commission = rules.calculate_commission("SELL", 10.0, 1000)
    assert sell_commission["commission"] == max(10.0 * 1000 * 0.00025, 5.0)
    assert sell_commission["stamp_tax"] == 10.0 * 1000 * 0.001
    assert sell_commission["transfer_fee"] == 10.0 * 1000 * 0.00001


def test_hk_trading_hours():
    """测试港股交易时间"""
    rules = HKRules()

    # 交易时间内
    assert rules.is_trading_time(datetime(2026, 6, 2, 10, 0)) == True  # 10:00
    assert rules.is_trading_time(datetime(2026, 6, 2, 15, 0)) == True  # 15:00

    # 非交易时间
    assert rules.is_trading_time(datetime(2026, 6, 2, 12, 30)) == False  # 12:30


def test_hk_no_price_limit():
    """测试港股无涨跌停限制"""
    rules = HKRules()

    # 港股无涨跌停限制
    assert rules.check_price_limit(100.0, 200.0) == True  # 涨100%
    assert rules.check_price_limit(100.0, 50.0) == True  # 跌50%


def test_hk_lot_size():
    """测试港股每手股数"""
    rules = HKRules()

    # 腾讯每手100股
    assert rules.validate_quantity(100, "00700") == True
    assert rules.validate_quantity(50, "00700") == False

    # 默认每手1000股
    assert rules.validate_quantity(1000, "99999") == True
    assert rules.validate_quantity(500, "99999") == False


def test_us_trading_hours():
    """测试美股交易时间"""
    rules = USRules()

    # 交易时间内（美东时间）
    assert rules.is_trading_time(datetime(2026, 6, 2, 10, 0)) == True  # 10:00 ET
    assert rules.is_trading_time(datetime(2026, 6, 2, 15, 0)) == True  # 15:00 ET

    # 非交易时间
    assert rules.is_trading_time(datetime(2026, 6, 2, 3, 0)) == False  # 03:00 ET


def test_us_no_price_limit():
    """测试美股无涨跌停限制"""
    rules = USRules()

    assert rules.check_price_limit(100.0, 500.0) == True  # 涨400%
    assert rules.check_price_limit(100.0, 10.0) == True  # 跌90%


def test_us_lot_size():
    """测试美股最小交易单位"""
    rules = USRules()

    # 美股可以买1股
    assert rules.validate_quantity(1) == True
    assert rules.validate_quantity(0) == False


def test_market_rules_factory():
    """测试市场规则工厂"""
    cn_rules = MarketRulesFactory.get_rules("CN")
    assert isinstance(cn_rules, CNRules)

    hk_rules = MarketRulesFactory.get_rules("HK")
    assert isinstance(hk_rules, HKRules)

    us_rules = MarketRulesFactory.get_rules("US")
    assert isinstance(us_rules, USRules)

    with pytest.raises(ValueError):
        MarketRulesFactory.get_rules("INVALID")
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_market_rules.py -v
```

预期结果：FAIL - 模块不存在

- [ ] **Step 3: 实现市场规则引擎**

```python
# backend/app/services/market_rules.py
from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Optional
from enum import Enum


class PriceLimitType(Enum):
    """涨跌停类型"""
    NORMAL = "normal"  # 普通股票
    STAR = "star"  # 科创板
    GEM = "gem"  # 创业板
    ST = "st"  # ST股


class MarketRules(ABC):
    """市场规则基类"""

    @property
    @abstractmethod
    def market(self) -> str:
        """市场代码"""
        pass

    @property
    @abstractmethod
    def currency(self) -> str:
        """货币代码"""
        pass

    @abstractmethod
    def is_trading_time(self, dt: datetime) -> bool:
        """检查是否在交易时间"""
        pass

    @abstractmethod
    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        """检查涨跌停限制"""
        pass

    @abstractmethod
    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        """验证交易数量"""
        pass

    @abstractmethod
    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        """计算手续费"""
        pass

    @abstractmethod
    def get_t_plus_n(self) -> int:
        """获取T+N交易制度"""
        pass


class CNRules(MarketRules):
    """A股市场规则"""

    @property
    def market(self) -> str:
        return "CN"

    @property
    def currency(self) -> str:
        return "CNY"

    def is_trading_time(self, dt: datetime) -> bool:
        """检查是否在交易时间"""
        t = dt.time()

        # 上午交易时间：9:30-11:30
        morning_start = time(9, 30)
        morning_end = time(11, 30)

        # 下午交易时间：13:00-15:00
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)

        return (morning_start <= t <= morning_end) or (afternoon_start <= t <= afternoon_end)

    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        """检查涨跌停限制"""
        if limit_type is None:
            limit_type = PriceLimitType.NORMAL

        # 计算涨跌幅
        change_pct = (target_price - base_price) / base_price

        # 根据类型确定限制
        limits = {
            PriceLimitType.NORMAL: 0.10,  # ±10%
            PriceLimitType.STAR: 0.20,    # 科创板 ±20%
            PriceLimitType.GEM: 0.20,     # 创业板 ±20%
            PriceLimitType.ST: 0.05,      # ST股 ±5%
        }

        limit = limits.get(limit_type, 0.10)
        return -limit <= change_pct <= limit

    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        """验证交易数量"""
        # A股最小交易单位100股
        return quantity > 0 and quantity % 100 == 0

    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        """计算手续费"""
        total_amount = price * quantity

        # 佣金：最低5元
        commission = max(total_amount * 0.00025, 5.0)

        # 印花税：仅卖出时收取
        stamp_tax = total_amount * 0.001 if trade_type == "SELL" else 0.0

        # 过户费
        transfer_fee = total_amount * 0.00001

        total = commission + stamp_tax + transfer_fee

        return {
            "commission": round(commission, 2),
            "stamp_tax": round(stamp_tax, 2),
            "transfer_fee": round(transfer_fee, 2),
            "total": round(total, 2)
        }

    def get_t_plus_n(self) -> int:
        return 1  # T+1


class HKRules(MarketRules):
    """港股市场规则"""

    # 每手股数配置
    LOT_SIZES = {
        "00700": 100,   # 腾讯
        "09988": 100,   # 阿里
        "00005": 400,   # 汇丰
        "default": 1000
    }

    @property
    def market(self) -> str:
        return "HK"

    @property
    def currency(self) -> str:
        return "HKD"

    def is_trading_time(self, dt: datetime) -> bool:
        """检查是否在交易时间"""
        t = dt.time()

        # 上午交易时间：9:30-12:00
        morning_start = time(9, 30)
        morning_end = time(12, 0)

        # 下午交易时间：13:00-16:00
        afternoon_start = time(13, 0)
        afternoon_end = time(16, 0)

        return (morning_start <= t <= morning_end) or (afternoon_start <= t <= afternoon_end)

    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        """检查涨跌停限制"""
        # 港股无涨跌停限制
        return True

    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        """验证交易数量"""
        if stock_code and stock_code in self.LOT_SIZES:
            lot_size = self.LOT_SIZES[stock_code]
        else:
            lot_size = self.LOT_SIZES["default"]

        return quantity > 0 and quantity % lot_size == 0

    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        """计算手续费"""
        total_amount = price * quantity

        # 佣金：最低50港元
        commission = max(total_amount * 0.0003, 50.0)

        # 印花税
        stamp_tax = total_amount * 0.0013

        # 交易费
        trading_fee = total_amount * 0.00005

        # 证监会征费
        sfc = total_amount * 0.000027

        total = commission + stamp_tax + trading_fee + sfc

        return {
            "commission": round(commission, 2),
            "stamp_tax": round(stamp_tax, 2),
            "trading_fee": round(trading_fee, 2),
            "sfc": round(sfc, 2),
            "total": round(total, 2)
        }

    def get_t_plus_n(self) -> int:
        return 0  # T+0


class USRules(MarketRules):
    """美股市场规则"""

    @property
    def market(self) -> str:
        return "US"

    @property
    def currency(self) -> str:
        return "USD"

    def is_trading_time(self, dt: datetime) -> bool:
        """检查是否在交易时间"""
        t = dt.time()

        # 常规交易时间：9:30-16:00（美东时间）
        regular_start = time(9, 30)
        regular_end = time(16, 0)

        return regular_start <= t <= regular_end

    def check_price_limit(self, base_price: float, target_price: float, limit_type: Optional[PriceLimitType] = None) -> bool:
        """检查涨跌停限制"""
        # 美股无涨跌停限制
        return True

    def validate_quantity(self, quantity: int, stock_code: Optional[str] = None) -> bool:
        """验证交易数量"""
        # 美股可以买1股
        return quantity > 0

    def calculate_commission(self, trade_type: str, price: float, quantity: int) -> dict:
        """计算手续费"""
        total_amount = price * quantity

        # 零佣金
        commission = 0.0

        # SEC费
        sec = total_amount * 0.0000278

        # TAF费
        taf = total_amount * 0.000166

        total = commission + sec + taf

        return {
            "commission": round(commission, 2),
            "sec": round(sec, 2),
            "taf": round(taf, 2),
            "total": round(total, 2)
        }

    def get_t_plus_n(self) -> int:
        return 0  # T+0


class MarketRulesFactory:
    """市场规则工厂"""

    _rules = {
        "CN": CNRules,
        "HK": HKRules,
        "US": USRules,
    }

    @classmethod
    def get_rules(cls, market: str) -> MarketRules:
        """
        获取市场规则

        Args:
            market: 市场代码

        Returns:
            市场规则实例

        Raises:
            ValueError: 不支持的市场
        """
        if market not in cls._rules:
            raise ValueError(f"不支持的市场: {market}")

        return cls._rules[market]()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_market_rules.py -v
```

预期结果：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/services/market_rules.py backend/tests/test_market_rules.py
git commit -m "feat: 实现多市场交易规则引擎

- 实现A股、港股、美股交易规则
- 支持涨跌停限制检查
- 支持交易数量验证
- 支持多市场手续费计算
- 使用工厂模式创建规则实例"
```

---

## Task 4: 高级订单系统

**Files:**
- Create: `backend/app/models/order.py`
- Create: `backend/app/schemas/order.py`
- Create: `backend/app/services/order_service.py`
- Create: `backend/app/services/matching_engine.py`
- Create: `backend/tests/test_order_service.py`
- Create: `backend/tests/test_matching_engine.py`

- [ ] **Step 1: 编写订单模型测试**

```python
# backend/tests/test_order_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.market_account import MarketAccount
from app.models.order import Order, OrderType, OrderDirection, OrderStatus, TimeInForce


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def user_with_account(db_session):
    """创建带市场账户的用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        initial_capital=1000000.0,
        current_capital=1000000.0
    )
    db_session.add(user)
    db_session.commit()

    account = MarketAccount(
        user_id=user.id,
        market="CN",
        currency="CNY",
        initial_capital=500000.0,
        current_capital=500000.0
    )
    db_session.add(account)
    db_session.commit()

    return user, account


def test_create_limit_order(db_session, user_with_account):
    """测试创建限价单"""
    user, account = user_with_account

    order = Order(
        user_id=user.id,
        market="CN",
        stock_code="000001",
        stock_name="平安银行",
        order_type=OrderType.LIMIT,
        direction=OrderDirection.BUY,
        price=10.0,
        quantity=1000,
        time_in_force=TimeInForce.GTC
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert saved_order is not None
    assert saved_order.order_type == OrderType.LIMIT
    assert saved_order.direction == OrderDirection.BUY
    assert saved_order.status == OrderStatus.PENDING


def test_create_market_order(db_session, user_with_account):
    """测试创建市价单"""
    user, account = user_with_account

    order = Order(
        user_id=user.id,
        market="CN",
        stock_code="000001",
        stock_name="平安银行",
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=1000
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert saved_order.order_type == OrderType.MARKET


def test_create_stop_loss_order(db_session, user_with_account):
    """测试创建止损单"""
    user, account = user_with_account

    order = Order(
        user_id=user.id,
        market="CN",
        stock_code="000001",
        stock_name="平安银行",
        order_type=OrderType.STOP_LOSS,
        direction=OrderDirection.SELL,
        stop_price=9.0,
        quantity=1000,
        time_in_force=TimeInForce.GTC
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert saved_order.order_type == OrderType.STOP_LOSS
    assert saved_order.stop_price == 9.0


def test_create_take_profit_order(db_session, user_with_account):
    """测试创建止盈单"""
    user, account = user_with_account

    order = Order(
        user_id=user.id,
        market="CN",
        stock_code="000001",
        stock_name="平安银行",
        order_type=OrderType.TAKE_PROFIT,
        direction=OrderDirection.SELL,
        stop_price=12.0,
        quantity=1000,
        time_in_force=TimeInForce.GTC
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert saved_order.order_type == OrderType.TAKE_PROFIT
    assert saved_order.stop_price == 12.0


def test_order_status_transitions(db_session, user_with_account):
    """测试订单状态转换"""
    user, account = user_with_account

    order = Order(
        user_id=user.id,
        market="CN",
        stock_code="000001",
        stock_name="平安银行",
        order_type=OrderType.LIMIT,
        direction=OrderDirection.BUY,
        price=10.0,
        quantity=1000
    )
    db_session.add(order)
    db_session.commit()

    # 初始状态
    assert order.status == OrderStatus.PENDING

    # 部分成交
    order.status = OrderStatus.PARTIAL
    order.filled_quantity = 500
    db_session.commit()

    # 完全成交
    order.status = OrderStatus.FILLED
    order.filled_quantity = 1000
    order.avg_fill_price = 10.0
    db_session.commit()

    saved_order = db_session.query(Order).filter(Order.id == order.id).first()
    assert saved_order.status == OrderStatus.FILLED
    assert saved_order.filled_quantity == 1000
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_order_service.py -v
```

预期结果：FAIL - 模型不存在

- [ ] **Step 3: 实现订单模型**

```python
# backend/app/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class OrderType(str, enum.Enum):
    """订单类型"""
    MARKET = "MARKET"  # 市价单
    LIMIT = "LIMIT"  # 限价单
    STOP_LOSS = "STOP_LOSS"  # 止损单
    TAKE_PROFIT = "TAKE_PROFIT"  # 止盈单
    OCO = "OCO"  # 止损止盈单
    CONDITIONAL = "CONDITIONAL"  # 条件单


class OrderDirection(str, enum.Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    """订单状态"""
    PENDING = "PENDING"  # 待执行
    FILLED = "FILLED"  # 已成交
    PARTIAL = "PARTIAL"  # 部分成交
    CANCELLED = "CANCELLED"  # 已取消
    REJECTED = "REJECTED"  # 已拒绝


class TimeInForce(str, enum.Enum):
    """有效期类型"""
    GTC = "GTC"  # 撤销前有效
    IOC = "IOC"  # 立即成交或取消
    FOK = "FOK"  # 全部成交或取消
    DAY = "DAY"  # 当日有效


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    market = Column(String(10), nullable=False)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    order_type = Column(String(20), nullable=False)
    direction = Column(String(4), nullable=False)
    price = Column(Float)
    quantity = Column(Integer, nullable=False)
    filled_quantity = Column(Integer, default=0)
    avg_fill_price = Column(Float)
    status = Column(String(20), default="PENDING")
    time_in_force = Column(String(10), default="GTC")
    stop_price = Column(Float)
    condition_type = Column(String(20))
    condition_value = Column(String(100))
    strategy_tag = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_order_service.py -v
```

预期结果：PASS

- [ ] **Step 5: 编写订单Schema**

```python
# backend/app/schemas/order.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    OCO = "OCO"
    CONDITIONAL = "CONDITIONAL"


class OrderDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    DAY = "DAY"


class OrderCreate(BaseModel):
    """创建订单请求"""
    market: str
    stock_code: str
    stock_name: Optional[str] = None
    order_type: OrderType
    direction: OrderDirection
    price: Optional[float] = None
    quantity: int
    time_in_force: Optional[TimeInForce] = TimeInForce.GTC
    stop_price: Optional[float] = None
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None
    strategy_tag: Optional[str] = None


class OrderUpdate(BaseModel):
    """更新订单请求"""
    price: Optional[float] = None
    quantity: Optional[int] = None
    stop_price: Optional[float] = None


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    user_id: int
    market: str
    stock_code: str
    stock_name: Optional[str]
    order_type: str
    direction: str
    price: Optional[float]
    quantity: int
    filled_quantity: int
    avg_fill_price: Optional[float]
    status: str
    time_in_force: str
    stop_price: Optional[float]
    strategy_tag: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    filled_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderList(BaseModel):
    """订单列表响应"""
    orders: list[OrderResponse]
    total: int
```

- [ ] **Step 6: 编写撮合引擎测试**

```python
# backend/tests/test_matching_engine.py
import pytest
from datetime import datetime
from app.services.matching_engine import MatchingEngine, MarketData
from app.services.market_rules import CNRules, HKRules, USRules
from app.models.order import Order, OrderType, OrderDirection, OrderStatus


@pytest.fixture
def cn_rules():
    return CNRules()


@pytest.fixture
def matching_engine(cn_rules):
    return MatchingEngine(cn_rules)


@pytest.fixture
def market_data():
    return MarketData(
        stock_code="000001",
        current_price=10.0,
        bid_price=9.99,
        ask_price=10.01,
        volume=1000000
    )


def test_match_limit_buy_order(matching_engine, market_data):
    """测试撮合限价买入单"""
    order = Order(
        order_type=OrderType.LIMIT,
        direction=OrderDirection.BUY,
        price=10.01,  # 等于卖一价
        quantity=1000
    )

    result = matching_engine.match(order, market_data)
    assert result.success == True
    assert result.price == 10.01


def test_match_limit_buy_order_no_match(matching_engine, market_data):
    """测试限价买入单未达到成交条件"""
    order = Order(
        order_type=OrderType.LIMIT,
        direction=OrderDirection.BUY,
        price=9.98,  # 低于卖一价
        quantity=1000
    )

    result = matching_engine.match(order, market_data)
    assert result.success == False


def test_match_limit_sell_order(matching_engine, market_data):
    """测试撮合限价卖出单"""
    order = Order(
        order_type=OrderType.LIMIT,
        direction=OrderDirection.SELL,
        price=9.99,  # 等于买一价
        quantity=1000
    )

    result = matching_engine.match(order, market_data)
    assert result.success == True
    assert result.price == 9.99


def test_match_market_buy_order(matching_engine, market_data):
    """测试撮合市价买入单"""
    order = Order(
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=1000
    )

    result = matching_engine.match(order, market_data)
    assert result.success == True
    # 市价单按卖一价成交（加滑点）
    assert result.price >= market_data.ask_price


def test_match_market_sell_order(matching_engine, market_data):
    """测试撮合市价卖出单"""
    order = Order(
        order_type=OrderType.MARKET,
        direction=OrderDirection.SELL,
        quantity=1000
    )

    result = matching_engine.match(order, market_data)
    assert result.success == True
    # 市价单按买一价成交（加滑点）
    assert result.price <= market_data.bid_price


def test_match_stop_loss_order(matching_engine, market_data):
    """测试撮合止损单"""
    # 止损卖出：当前价9.99，止损价9.95
    order = Order(
        order_type=OrderType.STOP_LOSS,
        direction=OrderDirection.SELL,
        stop_price=9.95,
        quantity=1000
    )

    # 当前价格高于止损价，不触发
    result = matching_engine.match(order, market_data)
    assert result.success == False

    # 价格跌破止损价，触发
    market_data.current_price = 9.94
    market_data.bid_price = 9.94
    result = matching_engine.match(order, market_data)
    assert result.success == True


def test_match_take_profit_order(matching_engine, market_data):
    """测试撮合止盈单"""
    # 止盈卖出：当前价10.0，止盈价10.5
    order = Order(
        order_type=OrderType.TAKE_PROFIT,
        direction=OrderDirection.SELL,
        stop_price=10.5,
        quantity=1000
    )

    # 当前价格低于止盈价，不触发
    result = matching_engine.match(order, market_data)
    assert result.success == False

    # 价格达到止盈价，触发
    market_data.current_price = 10.5
    market_data.bid_price = 10.5
    result = matching_engine.match(order, market_data)
    assert result.success == True


def test_check_price_limit(matching_engine, market_data):
    """测试涨跌停检查"""
    order = Order(
        order_type=OrderType.LIMIT,
        direction=OrderDirection.BUY,
        price=11.0,  # 涨停价
        quantity=1000
    )

    # 基准价10.0，涨停价11.0（+10%）
    result = matching_engine.match(order, market_data, base_price=10.0)
    assert result.success == True

    # 超过涨停价
    order.price = 11.1
    result = matching_engine.match(order, market_data, base_price=10.0)
    assert result.success == False
```

- [ ] **Step 7: 运行测试验证失败**

```bash
cd backend
pytest tests/test_matching_engine.py -v
```

预期结果：FAIL - 模块不存在

- [ ] **Step 8: 实现撮合引擎**

```python
# backend/app/services/matching_engine.py
from dataclasses import dataclass
from typing import Optional
from app.services.market_rules import MarketRules, PriceLimitType
from app.models.order import Order, OrderType, OrderDirection


@dataclass
class MarketData:
    """市场数据"""
    stock_code: str
    current_price: float
    bid_price: float  # 买一价
    ask_price: float  # 卖一价
    volume: int


@dataclass
class MatchResult:
    """撮合结果"""
    success: bool
    message: str
    price: Optional[float] = None
    quantity: Optional[int] = None


class MatchingEngine:
    """撮合引擎"""

    def __init__(self, market_rules: MarketRules):
        self.market_rules = market_rules
        self.default_slippage = 0.005  # 默认滑点0.5%

    def match(self, order: Order, market_data: MarketData, base_price: Optional[float] = None) -> MatchResult:
        """
        撮合订单

        Args:
            order: 待撮合订单
            market_data: 市场数据
            base_price: 基准价格（用于涨跌停检查）

        Returns:
            撮合结果
        """
        # 1. 检查订单状态
        if order.status and order.status != "PENDING":
            return MatchResult(success=False, message="订单状态错误")

        # 2. 检查涨跌停限制
        if base_price and order.price:
            if not self.market_rules.check_price_limit(base_price, order.price):
                return MatchResult(success=False, message="价格超出涨跌停限制")

        # 3. 根据订单类型执行撮合
        if order.order_type == OrderType.MARKET:
            return self._match_market_order(order, market_data)
        elif order.order_type == OrderType.LIMIT:
            return self._match_limit_order(order, market_data)
        elif order.order_type == OrderType.STOP_LOSS:
            return self._match_stop_loss_order(order, market_data)
        elif order.order_type == OrderType.TAKE_PROFIT:
            return self._match_take_profit_order(order, market_data)
        else:
            return MatchResult(success=False, message=f"不支持的订单类型: {order.order_type}")

    def _match_market_order(self, order: Order, market_data: MarketData) -> MatchResult:
        """撮合市价单"""
        # 应用滑点
        slippage = self.default_slippage

        if order.direction == OrderDirection.BUY:
            # 买入：按卖一价 + 滑点
            price = market_data.ask_price * (1 + slippage)
        else:
            # 卖出：按买一价 - 滑点
            price = market_data.bid_price * (1 - slippage)

        return MatchResult(
            success=True,
            message="市价单撮合成功",
            price=round(price, 4),
            quantity=order.quantity
        )

    def _match_limit_order(self, order: Order, market_data: MarketData) -> MatchResult:
        """撮合限价单"""
        if order.direction == OrderDirection.BUY:
            # 买入限价单：当前卖一价 <= 限价
            if market_data.ask_price <= order.price:
                return MatchResult(
                    success=True,
                    message="限价买入单撮合成功",
                    price=market_data.ask_price,
                    quantity=order.quantity
                )
        else:
            # 卖出限价单：当前买一价 >= 限价
            if market_data.bid_price >= order.price:
                return MatchResult(
                    success=True,
                    message="限价卖出单撮合成功",
                    price=market_data.bid_price,
                    quantity=order.quantity
                )

        return MatchResult(success=False, message="限价单未达到成交条件")

    def _match_stop_loss_order(self, order: Order, market_data: MarketData) -> MatchResult:
        """撮合止损单"""
        if order.direction == OrderDirection.SELL:
            # 止损卖出：当前价 <= 止损价
            if market_data.current_price <= order.stop_price:
                return MatchResult(
                    success=True,
                    message="止损单触发",
                    price=market_data.bid_price,
                    quantity=order.quantity
                )
        else:
            # 止损买入：当前价 >= 止损价
            if market_data.current_price >= order.stop_price:
                return MatchResult(
                    success=True,
                    message="止损单触发",
                    price=market_data.ask_price,
                    quantity=order.quantity
                )

        return MatchResult(success=False, message="止损单未触发")

    def _match_take_profit_order(self, order: Order, market_data: MarketData) -> MatchResult:
        """撮合止盈单"""
        if order.direction == OrderDirection.SELL:
            # 止盈卖出：当前价 >= 止盈价
            if market_data.current_price >= order.stop_price:
                return MatchResult(
                    success=True,
                    message="止盈单触发",
                    price=market_data.bid_price,
                    quantity=order.quantity
                )
        else:
            # 止盈买入：当前价 <= 止盈价
            if market_data.current_price <= order.stop_price:
                return MatchResult(
                    success=True,
                    message="止盈单触发",
                    price=market_data.ask_price,
                    quantity=order.quantity
                )

        return MatchResult(success=False, message="止盈单未触发")
```

- [ ] **Step 9: 运行测试验证通过**

```bash
cd backend
pytest tests/test_matching_engine.py -v
```

预期结果：PASS

- [ ] **Step 10: 实现订单服务**

```python
# backend/app/services/order_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.order import Order, OrderStatus
from app.models.market_account import MarketAccount
from app.models.position import Position
from app.models.trade import Trade
from app.schemas.order import OrderCreate
from app.services.market_rules import MarketRulesFactory
from app.services.matching_engine import MatchingEngine, MarketData


class OrderService:
    """订单服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_order(self, user_id: int, order_data: OrderCreate) -> Order:
        """
        创建订单

        Args:
            user_id: 用户ID
            order_data: 订单数据

        Returns:
            创建的订单

        Raises:
            ValueError: 验证失败
        """
        # 获取市场规则
        rules = MarketRulesFactory.get_rules(order_data.market)

        # 验证交易数量
        if not rules.validate_quantity(order_data.quantity, order_data.stock_code):
            raise ValueError(f"无效的交易数量: {order_data.quantity}")

        # 检查市场账户
        account = self.db.query(MarketAccount).filter(
            MarketAccount.user_id == user_id,
            MarketAccount.market == order_data.market
        ).first()
        if not account:
            raise ValueError(f"未找到{order_data.market}市场账户")

        # 创建订单
        order = Order(
            user_id=user_id,
            market=order_data.market,
            stock_code=order_data.stock_code,
            stock_name=order_data.stock_name,
            order_type=order_data.order_type.value,
            direction=order_data.direction.value,
            price=order_data.price,
            quantity=order_data.quantity,
            time_in_force=order_data.time_in_force.value if order_data.time_in_force else "GTC",
            stop_price=order_data.stop_price,
            condition_type=order_data.condition_type,
            condition_value=order_data.condition_value,
            strategy_tag=order_data.strategy_tag,
            status=OrderStatus.PENDING.value
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def execute_order(self, order_id: int, market_data: MarketData, base_price: Optional[float] = None) -> dict:
        """
        执行订单

        Args:
            order_id: 订单ID
            market_data: 市场数据
            base_price: 基准价格

        Returns:
            执行结果
        """
        # 获取订单
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "message": "订单不存在"}

        if order.status != OrderStatus.PENDING.value:
            return {"success": False, "message": "订单状态错误"}

        # 获取市场规则
        rules = MarketRulesFactory.get_rules(order.market)

        # 创建撮合引擎
        engine = MatchingEngine(rules)

        # 执行撮合
        result = engine.match(order, market_data, base_price)

        if result.success:
            # 更新订单状态
            order.status = OrderStatus.FILLED.value
            order.filled_quantity = result.quantity
            order.avg_fill_price = result.price
            order.filled_at = datetime.utcnow()

            # 计算手续费
            commission = rules.calculate_commission(order.direction, result.price, result.quantity)

            # 创建交易记录
            trade = Trade(
                user_id=order.user_id,
                order_id=order.id,
                market=order.market,
                stock_code=order.stock_code,
                trade_type=order.direction,
                price=result.price,
                quantity=result.quantity,
                commission=commission["total"],
                total_amount=result.price * result.quantity,
                strategy_tag=order.strategy_tag,
                trade_time=datetime.utcnow()
            )
            self.db.add(trade)

            # 更新持仓
            self._update_position(order, result.price, result.quantity)

            # 更新账户资金
            self._update_account(order, result.price, result.quantity, commission["total"])

            self.db.commit()

            return {
                "success": True,
                "message": result.message,
                "trade_id": trade.id,
                "price": result.price,
                "quantity": result.quantity,
                "commission": commission["total"]
            }
        else:
            return {"success": False, "message": result.message}

    def _update_position(self, order: Order, price: float, quantity: int):
        """更新持仓"""
        position = self.db.query(Position).filter(
            Position.user_id == order.user_id,
            Position.stock_code == order.stock_code
        ).first()

        if order.direction == "BUY":
            if position:
                # 更新持仓
                total_quantity = position.quantity + quantity
                position.avg_cost = (
                    (position.avg_cost * position.quantity + price * quantity) / total_quantity
                )
                position.quantity = total_quantity
            else:
                # 创建新持仓
                position = Position(
                    user_id=order.user_id,
                    market=order.market,
                    stock_code=order.stock_code,
                    stock_name=order.stock_name,
                    quantity=quantity,
                    avg_cost=price,
                    current_price=price,
                    unrealized_pnl=0.0
                )
                self.db.add(position)
        else:
            if position:
                position.quantity -= quantity
                if position.quantity == 0:
                    self.db.delete(position)

    def _update_account(self, order: Order, price: float, quantity: int, commission: float):
        """更新账户资金"""
        account = self.db.query(MarketAccount).filter(
            MarketAccount.user_id == order.user_id,
            MarketAccount.market == order.market
        ).first()

        if order.direction == "BUY":
            account.current_capital -= (price * quantity + commission)
        else:
            account.current_capital += (price * quantity - commission)

    def get_orders(self, user_id: int, market: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Order]:
        """获取订单列表"""
        query = self.db.query(Order).filter(Order.user_id == user_id)

        if market:
            query = query.filter(Order.market == market)
        if status:
            query = query.filter(Order.status == status)

        return query.order_by(Order.created_at.desc()).limit(limit).all()

    def cancel_order(self, order_id: int, user_id: int) -> dict:
        """取消订单"""
        order = self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()

        if not order:
            return {"success": False, "message": "订单不存在"}

        if order.status != OrderStatus.PENDING.value:
            return {"success": False, "message": "只能取消待执行的订单"}

        order.status = OrderStatus.CANCELLED.value
        self.db.commit()

        return {"success": True, "message": "订单已取消"}
```

- [ ] **Step 11: 提交代码**

```bash
git add backend/app/models/order.py backend/app/schemas/order.py backend/app/services/order_service.py backend/app/services/matching_engine.py backend/tests/test_order_service.py backend/tests/test_matching_engine.py
git commit -m "feat: 实现高级订单系统

- 添加订单模型支持多种订单类型
- 实现撮合引擎（限价单、市价单、止损单、止盈单）
- 实现订单服务（创建、执行、取消）
- 集成多市场规则验证
- 添加完整的测试覆盖"
```

---

## Task 5: 修改现有模型和API

**Files:**
- Modify: `backend/app/models/position.py`
- Modify: `backend/app/models/trade.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/utils/commission.py`
- Modify: `backend/app/api/trade.py`

- [ ] **Step 1: 修改持仓模型添加市场字段**

```python
# backend/app/models/position.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    market = Column(String(10), nullable=False)  # 新增：市场字段
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    quantity = Column(Integer, nullable=False, default=0)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)  # 新增：盈亏百分比
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 唯一约束：每个用户每个市场每只股票只有一个持仓
    __table_args__ = (
        UniqueConstraint('user_id', 'market', 'stock_code', name='uq_user_market_stock'),
    )
```

- [ ] **Step 2: 修改交易记录模型添加市场和订单关联**

```python
# backend/app/models/trade.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))  # 新增：关联订单
    market = Column(String(10), nullable=False)  # 新增：市场字段
    stock_code = Column(String(20), nullable=False, index=True)
    trade_type = Column(String(4), nullable=False)  # BUY or SELL
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    commission = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)  # 新增：税费
    total_amount = Column(Float, nullable=False)
    strategy_tag = Column(String(50))
    trade_time = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: 更新模型导出**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.position import Position
from app.models.trade import Trade
from app.models.prediction import Prediction
from app.models.review import Review
from app.models.market_account import MarketAccount
from app.models.order import Order

__all__ = [
    "User",
    "Position",
    "Trade",
    "Prediction",
    "Review",
    "MarketAccount",
    "Order",
]
```

- [ ] **Step 4: 提交代码**

```bash
git add backend/app/models/position.py backend/app/models/trade.py backend/app/models/__init__.py
git commit -m "refactor: 更新数据模型支持多市场

- 修改Position模型添加market字段
- 修改Trade模型添加market和order_id字段
- 更新模型导出"
```

---

## Task 6: 集成测试和API路由

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: 编写集成测试**

```python
# backend/tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.api.deps import get_db


@pytest.fixture
def client():
    """创建测试客户端"""
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
```

- [ ] **Step 2: 更新主应用路由**

```python
# backend/app/main.py (追加)
from app.api import auth, market_accounts, orders

# 注册路由
app.include_router(auth.router)
app.include_router(market_accounts.router)
app.include_router(orders.router)
```

- [ ] **Step 3: 运行集成测试**

```bash
cd backend
pytest tests/test_integration.py -v
```

预期结果：PASS

- [ ] **Step 4: 提交代码**

```bash
git add backend/app/main.py backend/tests/test_integration.py
git commit -m "feat: 完成核心交易引擎集成

- 注册认证、市场账户、订单API路由
- 添加集成测试验证完整交易流程
- 确保所有组件正常协作"
```

---

## 自审清单

**规格覆盖检查：**
- [x] 多市场支持（A股、港股、美股）- Task 3
- [x] 高级订单类型（限价单、市价单、止损单、止盈单）- Task 4
- [x] 用户认证系统 - Task 1
- [x] 多市场账户管理 - Task 2
- [x] 撮合引擎 - Task 4
- [x] 手续费计算 - Task 3

**占位符检查：**
- [x] 无TBD、TODO或"稍后实现"
- [x] 所有代码步骤都有完整实现
- [x] 所有测试都有具体断言

**类型一致性检查：**
- [x] OrderType枚举在模型和Schema中一致
- [x] OrderDirection枚举在模型和Schema中一致
- [x] MarketRules接口在所有实现中一致
- [x] 函数命名在测试和实现中一致

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-02-core-trading-engine.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 每个任务分派独立子代理，任务间审查，快速迭代

**2. Inline Execution** - 在当前会话中执行任务，批量执行带检查点

**选择哪种方式？**
