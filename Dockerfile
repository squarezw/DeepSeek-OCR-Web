# 使用 Docker Hub 官方镜像（通过镜像加速器）
FROM pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime

LABEL maintainer="squarezw"
LABEL description="DeepSeek-OCR Web API Service"

# 配置 apt 使用国内镜像源
RUN sed -i 's@archive.ubuntu.com@mirrors.aliyun.com@g' /etc/apt/sources.list && \
    sed -i 's@security.ubuntu.com@mirrors.aliyun.com@g' /etc/apt/sources.list

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY app.py /app/

# 创建必要的目录
RUN mkdir -p /app/uploads /app/outputs

# 设置环境变量
ENV PORT=3030
ENV CUDA_VISIBLE_DEVICES=0
ENV MODEL_PATH=/models/DeepSeek-OCR
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 3030

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD curl -f http://localhost:3030/health || exit 1

# 启动命令
CMD ["python", "app.py"]
