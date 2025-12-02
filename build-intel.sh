#!/bin/bash
# DeepSeek-OCR Intel GPU Build Script

set -e

echo "========================================="
echo "  DeepSeek-OCR Intel GPU Build Script"
echo "========================================="
echo ""

# 检查模型是否存在
if [ ! -f "./models/DeepSeek-OCR/model-00001-of-000001.safetensors" ]; then
    echo "❌ Error: Model not found in ./models/DeepSeek-OCR/"
    echo "Please download the model first."
    exit 1
fi

echo "✅ Model found"
echo ""

# 构建镜像
echo "🔨 Building Docker image for Intel GPU..."
docker build -f Dockerfile.intel -t deepseek-ocr-api-intel:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Start the service: docker-compose -f docker-compose.intel.yml up -d"
    echo "  2. Check logs: docker-compose -f docker-compose.intel.yml logs -f"
    echo "  3. Test API: curl http://localhost:3030/health"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
