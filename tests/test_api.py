#!/usr/bin/env python3
"""
测试 DeepSeek-OCR API 服务
"""

import requests
import json
import sys
from pathlib import Path

# API 配置
API_BASE_URL = "http://localhost:3030"
TEST_IMAGE = "demo/paddleocr_vl_demo.png"  # 修改为你的测试图片路径


def test_health():
    """测试健康检查"""
    print("\n" + "=" * 50)
    print("测试 1: 健康检查")
    print("=" * 50)

    response = requests.get(f"{API_BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200


def test_ocr_upload():
    """测试文件上传 OCR"""
    print("\n" + "=" * 50)
    print("测试 2: 文件上传 OCR")
    print("=" * 50)

    # 检查测试图片是否存在
    if not Path(TEST_IMAGE).exists():
        print(f"❌ 测试图片不存在: {TEST_IMAGE}")
        return False

    # 准备文件和参数
    with open(TEST_IMAGE, 'rb') as f:
        files = {'file': f}
        data = {
            'prompt': '<image>\n<|grounding|>Convert the document to markdown.',
            'base_size': 1024,
            'image_size': 640,
            'crop_mode': True,
            'save_results': True
        }

        print(f"上传文件: {TEST_IMAGE}")
        print(f"参数: {data}")

        response = requests.post(f"{API_BASE_URL}/ocr", files=files, data=data)

    print(f"\n状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n响应结构:")
        print(f"  - task_id: {result.get('task_id')}")
        print(f"  - status: {result.get('status')}")
        print(f"  - text 长度: {len(result.get('text', ''))}")
        print(f"  - output_files: {result.get('output_files')}")
        print(f"  - images: {result.get('images')}")
        print(f"  - output_path: {result.get('output_path')}")

        # 打印识别的文本（前 500 字符）
        text = result.get('text', '')
        if text:
            print(f"\n识别的文本（前 500 字符）:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            print(f"\n✅ 成功识别到 {len(text)} 字符的文本")
        else:
            print("\n⚠️  警告: 没有识别到文本")

        return True
    else:
        print(f"❌ 请求失败: {response.text}")
        return False


def test_model_info():
    """测试模型信息"""
    print("\n" + "=" * 50)
    print("测试 3: 模型信息")
    print("=" * 50)

    response = requests.get(f"{API_BASE_URL}/models/info")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200


def main():
    """主测试函数"""
    print("=" * 50)
    print("DeepSeek-OCR API 测试")
    print("=" * 50)
    print(f"API 地址: {API_BASE_URL}")

    results = []

    # 运行测试
    try:
        results.append(("健康检查", test_health()))
        results.append(("模型信息", test_model_info()))
        results.append(("文件上传 OCR", test_ocr_upload()))
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到 API 服务: {API_BASE_URL}")
        print("请确保服务正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 打印测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    # 检查是否所有测试都通过
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
