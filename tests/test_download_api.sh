#!/bin/bash
# 测试新的下载 API

echo "======================================================"
echo "DeepSeek-OCR API v1.0 测试"
echo "======================================================"
echo ""

# 1. 健康检查
echo "1. 健康检查"
echo "------------------------------------------------------"
curl -s http://localhost:3030/health
echo ""
echo ""

# 2. 上传图片进行 OCR
echo "2. 上传图片进行 OCR"
echo "------------------------------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:3030/ocr \
  -F "file=@/var/www/DeepSeek-OCR-Web/demo/paddleocr_vl_demo.png" \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true" \
  -F "save_results=true")

echo "响应 JSON:"
echo "$RESPONSE" | python3 -m json.tool
echo ""

# 提取 task_id 和文件 URL
TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])")
TEXT_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['files']['text'])")

echo "Task ID: $TASK_ID"
echo "Text URL: $TEXT_URL"
echo ""

# 3. 下载文本文件
echo "3. 下载文本结果（前 500 字符）"
echo "------------------------------------------------------"
curl -s "http://localhost:3030/download/$TASK_ID/result.txt" | head -c 500
echo ""
echo "..."
echo ""

# 4. 检查文件是否存在
echo "4. 检查输出文件"
echo "------------------------------------------------------"
ls -lh "/var/www/DeepSeek-OCR-Web/outputs/$TASK_ID/"
echo ""

echo "======================================================"
echo "测试完成!"
echo "======================================================"
