#!/usr/bin/env python3
"""
测试新的 OCR API（文件下载版本）
"""

import requests
import json

API_URL = "http://localhost:3030/ocr"

def test_image_ocr():
    """测试图片 OCR"""
    print("=" * 60)
    print("测试图片 OCR")
    print("=" * 60)

    with open("/var/www/DeepSeek-OCR-Web/demo/paddleocr_vl_demo.png", 'rb') as f:
        files = {'file': f}
        data = {
            'base_size': 1024,
            'image_size': 640,
            'crop_mode': True,
            'save_results': True
        }

        print("发送请求...")
        response = requests.post(API_URL, files=files, data=data, timeout=120)

    if response.status_code == 200:
        result = response.json()
        print("\n✅ 请求成功!")
        print(f"\n响应 JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 下载文本文件
        if result.get('files', {}).get('text'):
            text_url = result['files']['text']
            print(f"\n正在下载文本文件: {text_url}")

            text_response = requests.get(text_url)
            if text_response.status_code == 200:
                text_content = text_response.text
                print(f"\n文本内容（前 500 字符）:")
                print("-" * 60)
                print(text_content[:500])
                print("-" * 60)
                print(f"\n总字符数: {len(text_content)}")
            else:
                print(f"❌ 下载失败: {text_response.status_code}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)


def test_pdf_ocr():
    """测试 PDF OCR"""
    print("\n\n")
    print("=" * 60)
    print("测试 PDF OCR（多页）")
    print("=" * 60)

    with open("/var/www/DeepSeek-OCR-Web/DeepSeek_OCR_paper.pdf", 'rb') as f:
        files = {'file': f}
        data = {
            'base_size': 1024,
            'image_size': 640,
            'crop_mode': True,
            'save_results': True
        }

        print("发送请求...（这可能需要几分钟）")
        response = requests.post(API_URL, files=files, data=data, timeout=600)

    if response.status_code == 200:
        result = response.json()
        print("\n✅ 请求成功!")
        print(f"\n响应 JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 下载文本文件
        if result.get('files', {}).get('text'):
            text_url = result['files']['text']
            print(f"\n正在下载文本文件: {text_url}")

            text_response = requests.get(text_url)
            if text_response.status_code == 200:
                text_content = text_response.text
                print(f"\n文本内容（前 500 字符）:")
                print("-" * 60)
                print(text_content[:500])
                print("-" * 60)
                print(f"\n总字符数: {len(text_content)}")
                print(f"总页数: {result.get('total_pages')}")
            else:
                print(f"❌ 下载失败: {text_response.status_code}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    # 测试图片 OCR
    test_image_ocr()

    # 测试 PDF OCR（可选）
    # test_pdf_ocr()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
