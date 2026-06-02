#!/bin/bash
set -e

# ============================================================
# 股票交易系统 - 服务器自动部署脚本
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 兼容 docker-compose / docker compose
if command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE="docker compose"
else
    print_error "未找到 docker-compose 或 docker compose"
    exit 1
fi

echo ""
echo "============================================================"
echo "  股票交易系统 - 服务器自动部署"
echo "============================================================"
echo ""

# 1. 检查是否为 git 仓库
print_info "检查 Git 仓库..."
if [ ! -d ".git" ]; then
    print_error "当前目录不是 Git 仓库"
    exit 1
fi
print_success "Git 仓库检查通过"

# 2. 拉取最新代码（网络不通时跳过）
print_info "检查代码更新..."
if git fetch origin 2>/dev/null; then
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" = "$REMOTE" ]; then
        print_success "代码已是最新版本"
    else
        print_info "发现新版本，正在更新..."
        git pull origin master
        print_success "代码更新完成"
    fi
else
    print_warning "无法连接远程仓库，使用本地代码继续部署"
fi

# 3. 检查 docker-compose.yml 是否存在
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml 文件不存在"
    exit 1
fi

# 4. 停止现有服务
print_info "停止现有服务..."
$COMPOSE down
print_success "服务已停止"

# 5. 重新构建并启动服务
print_info "重新构建并启动服务..."
$COMPOSE up -d --build
print_success "服务构建完成"

# 6. 等待服务启动
print_info "等待服务启动..."
sleep 10

# 7. 检查服务状态
print_info "检查服务状态..."
$COMPOSE ps

# 8. 检查服务健康状态
echo ""
print_info "检查服务健康状态..."

# 检查 PostgreSQL
if $COMPOSE exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL 服务正常"
else
    print_warning "PostgreSQL 服务可能还在启动中..."
fi

# 检查 Redis
if $COMPOSE exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis 服务正常"
else
    print_warning "Redis 服务可能还在启动中..."
fi

# 检查后端 API
print_info "等待后端 API 启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "后端 API 服务正常"
        break
    fi
    if [ $i -eq 30 ]; then
        print_warning "后端 API 服务可能还在启动中，请稍后检查"
    fi
    sleep 2
done

# 检查前端
if curl -s http://localhost > /dev/null 2>&1; then
    print_success "前端服务正常"
else
    print_warning "前端服务可能还在启动中"
fi

# 9. 显示访问信息
echo ""
echo "============================================================"
echo "  部署完成！"
echo "============================================================"
echo ""
echo "  前端访问地址:"
echo "     http://$(hostname -I | awk '{print $1}')"
echo ""
echo "  后端 API 地址:"
echo "     http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "  API 文档地址:"
echo "     http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "  查看日志:"
echo "     $COMPOSE logs -f"
echo ""
echo "============================================================"
echo ""

print_success "部署脚本执行完成！"
