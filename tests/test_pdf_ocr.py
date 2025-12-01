#!/usr/bin/env python3
"""
测试 PDF OCR - 先将 PDF 转换为图片，然后进行 OCR
"""

import requests
import os
from pathlib import Path

# 需要先安装: pip install PyMuPDF (fitz)
try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ 需要安装 PyMuPDF: pip install PyMuPDF")
    exit(1)

# 配置
PDF_FILE = "/var/www/DeepSeek-OCR-Web/DeepSeek_OCR_paper.pdf"
OUTPUT_DIR = "/tmp/pdf_ocr_test"
API_URL = "http://localhost:3030/ocr"

def pdf_to_images(pdf_path, output_dir, max_pages=3):
    """
    将 PDF 转换为图片

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        max_pages: 最多转换的页数（测试用）

    Returns:
        list: 图片文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"打开 PDF: {pdf_path}")
    doc = fitz.open(pdf_path)

    total_pages = len(doc)
    pages_to_convert = min(max_pages, total_pages)

    print(f"PDF 总页数: {total_pages}")
    print(f"转换页数: {pages_to_convert}")
    print()

    image_files = []

    for page_num in range(pages_to_convert):
        print(f"转换第 {page_num + 1} 页...")

        page = doc[page_num]

        # 设置缩放以获得更高质量的图片
        zoom = 2  # 放大倍数
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # 保存为 PNG
        image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(image_path)

        image_files.append(image_path)
        print(f"  ✓ 已保存: {image_path} ({pix.width}x{pix.height})")

    doc.close()
    print()
    return image_files


def ocr_image(image_path):
    """
    对单个图片进行 OCR

    Args:
        image_path: 图片文件路径

    Returns:
        dict: OCR 结果
    """
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'base_size': 1024,
            'image_size': 640,
            'crop_mode': True,
            'save_results': False
        }

        response = requests.post(API_URL, files=files, data=data, timeout=120)

    return response.json() if response.status_code == 200 else None


def main():
    print("=" * 60)
    print("PDF OCR 测试")
    print("=" * 60)
    print()

    # 1. 将 PDF 转换为图片
    print("步骤 1: PDF 转换为图片")
    print("-" * 60)
    image_files = pdf_to_images(PDF_FILE, OUTPUT_DIR, max_pages=2)

    # 2. 对每个图片进行 OCR
    print("步骤 2: OCR 识别")
    print("-" * 60)

    results = []

    for i, image_file in enumerate(image_files, 1):
        print(f"\n处理第 {i} 页...")
        print(f"图片: {image_file}")

        try:
            result = ocr_image(image_file)

            if result and result.get('status') == 'success':
                text = result.get('text', '')
                print(f"✓ 识别成功")
                print(f"  - task_id: {result.get('task_id')}")
                print(f"  - 文本长度: {len(text)} 字符")

                # 显示前 200 字符
                if text:
                    print(f"\n  识别文本（前 200 字符）:")
                    print(f"  {'-' * 56}")
                    print(f"  {text[:200]}")
                    print(f"  {'-' * 56}")

                results.append({
                    'page': i,
                    'success': True,
                    'text_length': len(text),
                    'text': text
                })
            else:
                print(f"✗ 识别失败: {result}")
                results.append({
                    'page': i,
                    'success': False,
                    'error': result
                })

        except Exception as e:
            print(f"✗ 处理失败: {e}")
            results.append({
                'page': i,
                'success': False,
                'error': str(e)
            })

    # 3. 总结
    print()
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    success_count = sum(1 for r in results if r['success'])
    total_chars = sum(r.get('text_length', 0) for r in results if r['success'])

    print(f"总页数: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(results) - success_count}")
    print(f"总字符数: {total_chars}")

    if success_count > 0:
        print("\n✅ PDF OCR 测试成功！")
    else:
        print("\n❌ PDF OCR 测试失败")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
