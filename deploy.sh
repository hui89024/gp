#!/bin/bash
set -e

# ============================================================
# 股票交易系统 - 自动化部署脚本
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# ============================================================
# 主函数
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  🚀 股票交易系统 - 自动化部署脚本"
    echo "============================================================"
    echo ""

    # 1. 检查 Docker
    print_info "检查 Docker 是否安装..."
    if ! check_command docker; then
        print_error "Docker 未安装"
        print_info "正在安装 Docker..."

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            print_success "Docker 安装完成"
            print_warning "请重新登录以使 Docker 用户组生效"
            print_info "运行: newgrp docker 或重新登录"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            print_error "请手动安装 Docker Desktop for Mac"
            print_info "下载地址: https://www.docker.com/products/docker-desktop"
            exit 1
        else
            print_error "不支持的操作系统，请手动安装 Docker"
            exit 1
        fi
    else
        print_success "Docker 已安装: $(docker --version)"
    fi

    # 2. 检查 Docker Compose
    print_info "检查 Docker Compose 是否安装..."
    if ! check_command docker-compose; then
        print_error "Docker Compose 未安装"
        print_info "正在安装 Docker Compose..."

        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose

        print_success "Docker Compose 安装完成"
    else
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    fi

    # 3. 检查 Git
    print_info "检查 Git 是否安装..."
    if ! check_command git; then
        print_error "Git 未安装"
        print_info "正在安装 Git..."

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update
            sudo apt-get install -y git
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            print_error "请手动安装 Git"
            print_info "运行: brew install git"
            exit 1
        fi

        print_success "Git 安装完成"
    else
        print_success "Git 已安装: $(git --version)"
    fi

    # 4. 克隆项目（如果不是在项目目录中）
    print_info "检查项目目录..."
    if [ ! -f "docker-compose.yml" ]; then
        print_warning "当前目录不是项目根目录"
        print_info "请输入项目 Git 仓库地址（留空跳过）:"
        read -r repo_url

        if [ -n "$repo_url" ]; then
            print_info "克隆项目..."
            git clone "$repo_url" stock-trading-system
            cd stock-trading-system
            print_success "项目克隆完成"
        else
            print_error "请在项目根目录中运行此脚本"
            exit 1
        fi
    else
        print_success "已找到项目配置文件"
    fi

    # 5. 配置环境变量
    print_info "配置环境变量..."
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，正在创建..."

        cat > .env << EOF
# 数据库配置
DB_USER=postgres
DB_PASSWORD=$(openssl rand -base64 32 | tr -d '=/+' | head -c 32)

# Redis 配置
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '=/+' | head -c 32)

# 应用配置
SECRET_KEY=$(openssl rand -base64 64 | tr -d '=/+' | head -c 64)
DEBUG=false

# 服务器配置
SERVER_IP=$(hostname -I | awk '{print $1}')
ALLOWED_ORIGINS=*
EOF

        print_success ".env 文件已创建"
        print_warning "请检查并修改 .env 文件中的配置"
    else
        print_success ".env 文件已存在"
    fi

    # 6. 停止现有服务
    print_info "停止现有服务..."
    docker-compose down 2>/dev/null || true
    print_success "现有服务已停止"

    # 7. 清理旧镜像（可选）
    print_info "是否清理旧的 Docker 镜像？(y/N)"
    read -r cleanup_choice
    if [[ "$cleanup_choice" =~ ^[Yy]$ ]]; then
        print_info "清理旧镜像..."
        docker system prune -f
        print_success "旧镜像已清理"
    fi

    # 8. 构建并启动服务
    print_info "构建并启动服务..."
    docker-compose up -d --build

    # 9. 等待服务启动
    print_info "等待服务启动..."
    sleep 30

    # 10. 检查服务状态
    print_info "检查服务状态..."
    docker-compose ps

    # 11. 检查服务健康状态
    print_info "检查服务健康状态..."

    # 检查 PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL 服务正常"
    else
        print_error "PostgreSQL 服务异常"
    fi

    # 检查 Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis 服务正常"
    else
        print_error "Redis 服务异常"
    fi

    # 检查后端 API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "后端 API 服务正常"
    else
        print_warning "后端 API 服务可能还在启动中..."
        print_info "请稍等片刻后访问: http://localhost:8000/docs"
    fi

    # 12. 显示访问信息
    echo ""
    echo "============================================================"
    echo "  🎉 部署完成！"
    echo "============================================================"
    echo ""
    echo "  📱 前端访问地址:"
    echo "     http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "  🔧 后端 API 地址:"
    echo "     http://$(hostname -I | awk '{print $1}'):8000"
    echo ""
    echo "  📚 API 文档地址:"
    echo "     http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    echo "  📊 查看日志:"
    echo "     docker-compose logs -f"
    echo ""
    echo "  🛑 停止服务:"
    echo "     docker-compose down"
    echo ""
    echo "  🔄 重启服务:"
    echo "     docker-compose restart"
    echo ""
    echo "============================================================"
    echo ""

    # 13. 显示数据库信息
    print_info "数据库连接信息:"
    echo "  数据库: stock_trading"
    echo "  用户: postgres"
    echo "  密码: $(grep DB_PASSWORD .env | cut -d'=' -f2)"
    echo "  端口: 5432"
    echo ""

    # 14. 显示常用命令
    print_info "常用命令:"
    echo "  查看所有服务状态: docker-compose ps"
    echo "  查看实时日志: docker-compose logs -f"
    echo "  重启后端服务: docker-compose restart backend"
    echo "  进入后端容器: docker-compose exec backend bash"
    echo "  进入数据库: docker-compose exec postgres psql -U postgres -d stock_trading"
    echo "  备份数据库: docker-compose exec postgres pg_dump -U postgres stock_trading > backup.sql"
    echo ""

    # 15. 安全建议
    print_info "安全建议:"
    echo "  1. 修改默认密码（数据库、Redis）"
    echo "  2. 配置防火墙（仅开放 80、443、22 端口）"
    echo "  3. 配置 SSL 证书（使用 Let's Encrypt）"
    echo "  4. 定期备份数据库"
    echo "  5. 监控服务器资源使用情况"
    echo ""

    print_success "部署脚本执行完成！"
}

# 运行主函数
main "$@"
