#!/bin/bash

# DeepSeek-OCR 模型下载脚本
# 使用 Hugging Face 镜像站下载模型

echo "开始下载 DeepSeek-OCR 模型..."

# 设置模型保存路径
MODEL_DIR="/var/www/DeepSeek-OCR/models/DeepSeek-OCR"

# 创建目录
mkdir -p "$MODEL_DIR"

# 使用 Hugging Face 镜像站
export HF_ENDPOINT=https://hf-mirror.com

# 使用 huggingface-cli 下载模型
pip install -U huggingface_hub

# 下载模型
huggingface-cli download deepseek-ai/DeepSeek-OCR \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False

echo "模型下载完成！"
echo "模型路径: $MODEL_DIR"
