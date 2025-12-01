#!/usr/bin/env python3
"""
测试 DeepSeek-OCR Base64 API
"""

import requests
import base64
import json

# 读取测试图片
image_path = "/var/www/DeepSeek-OCR-Web/demo/paddleocr_vl_demo.png"
with open(image_path, "rb") as f:
    image_data = f.read()

# 转换为 Base64
image_base64 = base64.b64encode(image_data).decode("utf-8")

print("=" * 50)
print("测试 Base64 OCR 接口")
print("=" * 50)
print(f"图片大小: {len(image_data)} bytes")
print(f"Base64 长度: {len(image_base64)} 字符")
print()

# 发送请求
data = {
    "image_base64": image_base64,
    "base_size": "1024",
    "image_size": "640",
    "crop_mode": "true"
}

try:
    print("发送请求到 http://localhost:3030/ocr/base64 ...")
    response = requests.post("http://localhost:3030/ocr/base64", data=data, timeout=120)

    print(f"状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()

        task_id = result.get('task_id', 'N/A')
        status = result.get('status', 'N/A')
        text = result.get('text', '')
        output_files = result.get('output_files', [])
        images = result.get('images', [])
        output_path = result.get('output_path', 'N/A')

        print("响应结构:")
        print(f"  - task_id: {task_id}")
        print(f"  - status: {status}")
        print(f"  - text 长度: {len(text)}")
        print(f"  - output_files: {output_files}")
        print(f"  - images: {images}")
        print(f"  - output_path: {output_path}")
        print()

        # 打印识别文本的前 500 字符
        if text:
            print("识别的文本（前 500 字符）:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            print(f"\n✅ 成功识别到 {len(text)} 字符的文本")
        else:
            print("⚠️ 警告: 没有识别到文本")
    else:
        print(f"❌ 请求失败: {response.text}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 50)
print("测试完成")
print("=" * 50)
