#!/bin/bash

#############################################
# DeepSeek-OCR Web API 一键部署脚本
# 在 AI 服务器上执行
#############################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 显示标题
clear
echo "================================================"
echo "  DeepSeek-OCR Web API 部署脚本"
echo "================================================"
echo ""

# 配置
MODEL_DIR="/var/www/DeepSeek-OCR/models/DeepSeek-OCR"
PROJECT_DIR="/var/www/DeepSeek-OCR-Web"
MODEL_NAME="deepseek-ai/DeepSeek-OCR"

# 步骤 1: 检查模型是否已下载
log_info "步骤 1: 检查模型..."
if [ -d "$MODEL_DIR" ] && [ "$(ls -A $MODEL_DIR)" ]; then
    log_success "模型已存在: $MODEL_DIR"
else
    log_warning "模型不存在，开始下载..."

    # 创建模型目录
    mkdir -p "$MODEL_DIR"

    # 设置 Hugging Face 镜像
    export HF_ENDPOINT=https://hf-mirror.com

    # 检查 huggingface-cli
    if ! command -v huggingface-cli &> /dev/null; then
        log_info "安装 huggingface_hub..."
        pip install -U huggingface_hub
    fi

    # 下载模型
    log_info "开始下载模型（约 10GB，请耐心等待）..."
    huggingface-cli download $MODEL_NAME \
        --local-dir "$MODEL_DIR" \
        --local-dir-use-symlinks False

    if [ $? -eq 0 ]; then
        log_success "模型下载完成！"
    else
        log_error "模型下载失败"
        exit 1
    fi
fi

# 步骤 2: 检查项目代码
log_info "步骤 2: 检查项目代码..."
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "项目目录不存在: $PROJECT_DIR"
    log_info "请先将代码推送到服务器"
    exit 1
fi

cd "$PROJECT_DIR"
log_success "项目目录: $PROJECT_DIR"

# 步骤 3: 检查 Docker
log_info "步骤 3: 检查 Docker..."
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose 未安装"
    exit 1
fi

log_success "Docker 已安装"

# 步骤 4: 检查 GPU
log_info "步骤 4: 检查 GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi
    log_success "GPU 可用"
else
    log_warning "nvidia-smi 不可用，请确认 GPU 驱动已安装"
fi

# 步骤 5: 构建 Docker 镜像
log_info "步骤 5: 构建 Docker 镜像..."
docker build -t deepseek-ocr-api:latest .

if [ $? -eq 0 ]; then
    log_success "镜像构建成功"
else
    log_error "镜像构建失败"
    exit 1
fi

# 步骤 6: 停止旧容器
log_info "步骤 6: 停止旧容器..."
if docker ps -a | grep -q deepseek-ocr-api; then
    log_info "停止并删除旧容器..."
    docker-compose down
fi

# 步骤 7: 启动服务
log_info "步骤 7: 启动服务..."
docker-compose up -d

if [ $? -eq 0 ]; then
    log_success "服务启动成功！"
else
    log_error "服务启动失败"
    exit 1
fi

# 步骤 8: 等待服务就绪
log_info "步骤 8: 等待服务就绪..."
log_warning "模型加载需要 1-2 分钟，请耐心等待..."

sleep 10

# 检查容器状态
log_info "容器状态:"
docker ps | grep deepseek-ocr-api

# 步骤 9: 健康检查
log_info "步骤 9: 健康检查..."

max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:3030/health | grep -q "healthy"; then
        log_success "服务健康检查通过！"
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -eq $max_retries ]; then
            log_error "健康检查失败，请查看日志"
            docker-compose logs --tail 50
            exit 1
        fi
        echo -n "."
        sleep 2
    fi
done

echo ""

# 步骤 10: 测试 API
log_info "步骤 10: 测试 API..."

# 获取模型信息
log_info "获取模型信息..."
curl -s http://localhost:3030/models/info | python -m json.tool

# 显示部署信息
echo ""
echo "================================================"
log_success "部署完成！"
echo "================================================"
echo ""
log_info "服务信息:"
echo "  端口: 3030"
echo "  健康检查: http://localhost:3030/health"
echo "  模型信息: http://localhost:3030/models/info"
echo "  API 文档: http://localhost:3030/docs"
echo ""
log_info "查看日志:"
echo "  docker-compose logs -f"
echo ""
log_info "停止服务:"
echo "  docker-compose down"
echo ""
log_info "重启服务:"
echo "  docker-compose restart"
echo ""

# 提示配置 Nginx
log_warning "别忘了配置 Nginx 反向代理！"
echo "  请参考 DEPLOYMENT.md 中的 Nginx 配置示例"
echo ""
