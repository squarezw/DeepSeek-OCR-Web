#!/usr/bin/env python3
"""
简单测试 PDF OCR
使用 fitz 将 PDF 第一页转为图片，然后调用 OCR API
"""

import fitz  # PyMuPDF
import requests
import io
from PIL import Image

# 配置
PDF_FILE = "/var/www/DeepSeek-OCR-Web/DeepSeek_OCR_paper.pdf"
OUTPUT_IMAGE = "/tmp/pdf_page_1.png"
API_URL = "http://localhost:3030/ocr"

print("=" * 60)
print("PDF OCR 测试（单页）")
print("=" * 60)
print()

# 步骤 1: 将 PDF 第一页转为图片
print("步骤 1: 提取 PDF 第一页为图片")
print("-" * 60)

pdf_doc = fitz.open(PDF_FILE)
page = pdf_doc[0]  # 第一页

# 设置高 DPI 以获得更好的质量
zoom = 2  # 2x 缩放
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)

# 转换为 PIL Image
img_data = pix.tobytes("png")
img = Image.open(io.BytesIO(img_data))

# 保存图片
img.save(OUTPUT_IMAGE)
pdf_doc.close()

print(f"✓ 已提取第一页")
print(f"  - 尺寸: {img.width}x{img.height}")
print(f"  - 保存到: {OUTPUT_IMAGE}")
print()

# 步骤 2: 调用 OCR API
print("步骤 2: 调用 OCR API")
print("-" * 60)

with open(OUTPUT_IMAGE, 'rb') as f:
    files = {'file': f}
    data = {
        'base_size': 1024,
        'image_size': 640,
        'crop_mode': True,
        'save_results': True
    }

    print("发送请求...")
    response = requests.post(API_URL, files=files, data=data, timeout=120)

print(f"状态码: {response.status_code}")
print()

if response.status_code == 200:
    result = response.json()

    task_id = result.get('task_id')
    status = result.get('status')
    text = result.get('text', '')
    output_files = result.get('output_files', [])
    images = result.get('images', [])

    print("响应结果:")
    print(f"  - task_id: {task_id}")
    print(f"  - status: {status}")
    print(f"  - 识别文本长度: {len(text)} 字符")
    print(f"  - 输出文件: {output_files}")
    print(f"  - 输出图片: {images}")
    print()

    if text:
        print("识别的文本（前 800 字符）:")
        print("-" * 60)
        print(text[:800])
        print("-" * 60)
        print()
        print(f"✅ 成功识别 PDF 第一页，共 {len(text)} 字符")
    else:
        print("⚠️  警告: 未识别到文本")
else:
    print(f"❌ 请求失败:")
    print(response.text)

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
