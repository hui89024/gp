# 股票交易自动化系统

一个功能完整的模拟炒股系统，支持实时行情、模拟交易、K线图展示。

## 功能特性

- 实时股票行情查看
- 模拟买卖交易
- 持仓管理
- K线图展示
- 交易记录查询
- 账户概览

## 技术栈

**后端:**
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- AKShare

**前端:**
- React 18
- TypeScript
- Ant Design
- ECharts
- Zustand

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

- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/docs

## 项目结构

```
gp/
├── backend/          # 后端服务
│   ├── app/          # 应用代码
│   ├── tests/        # 测试文件
│   └── alembic/      # 数据库迁移
├── frontend/         # 前端应用
│   ├── src/          # 源代码
│   └── public/       # 静态资源
├── docker-compose.yml
└── README.md
```

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

- 股票预测功能
- 自动交易策略
- 复盘分析系统
- 移动端适配