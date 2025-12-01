# DeepSeek-OCR Web API 文档

## 基本信息

**Base URL**: `http://your-server:3030`

**版本**: 1.0.0

## API 端点

### 1. 健康检查

```
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

---

### 2. OCR 识别（文件上传）

```
POST /ocr
```

**支持格式**: 图片（PNG, JPG, JPEG 等）、PDF

**自动功能**:
- 自动检测文件类型（图片/PDF）
- PDF 自动转换为图片
- 多页 PDF 批量处理

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file | File | ✅ | - | 上传的图片或 PDF 文件 |
| prompt | String | ❌ | 默认提示词 | 自定义提示词 |
| base_size | Integer | ❌ | 1024 | 基础尺寸 (512/640/1024/1280) |
| image_size | Integer | ❌ | 640 | 图像尺寸 (512/640/1024/1280) |
| crop_mode | Boolean | ❌ | true | 是否使用裁剪模式 |
| save_results | Boolean | ❌ | false | 是否保存结果文件 |

**响应示例（图片）**:
```json
{
  "task_id": "044b3b96-51e7-4641-b5ba-6df4bb195b60",
  "status": "success",
  "file_type": "image",
  "total_pages": 1,
  "total_characters": 4392,
  "pages": [
    {
      "page": 1,
      "text_length": 4392
    }
  ],
  "files": {
    "text": "/download/044b3b96-51e7-4641-b5ba-6df4bb195b60/result.txt",
    "markdown": "/download/044b3b96-51e7-4641-b5ba-6df4bb195b60/result.mmd",
    "image_with_boxes": "/download/044b3b96-51e7-4641-b5ba-6df4bb195b60/result_with_boxes.jpg"
  },
  "output_path": "outputs/044b3b96-51e7-4641-b5ba-6df4bb195b60",
  "settings": {
    "prompt": "<image>\n<|grounding|>Convert the document to markdown.",
    "base_size": 1024,
    "image_size": 640,
    "crop_mode": true
  }
}
```

**响应示例（PDF）**:
```json
{
  "task_id": "1cf2f083-0844-4095-886e-c96955068d19",
  "status": "success",
  "file_type": "pdf",
  "total_pages": 22,
  "total_characters": 58734,
  "pages": [
    {"page": 1, "text_length": 2155},
    {"page": 2, "text_length": 1942},
    {"page": 3, "text_length": 1901},
    ...
  ],
  "files": {
    "text": "/download/1cf2f083-0844-4095-886e-c96955068d19/result.txt",
    "markdown": "/download/1cf2f083-0844-4095-886e-c96955068d19/result.mmd",
    "image_with_boxes": "/download/1cf2f083-0844-4095-886e-c96955068d19/result_with_boxes.jpg"
  },
  "output_path": "outputs/1cf2f083-0844-4095-886e-c96955068d19",
  "settings": {
    "prompt": "<image>\n<|grounding|>Convert the document to markdown.",
    "base_size": 1024,
    "image_size": 640,
    "crop_mode": true
  }
}
```

**cURL 示例**:
```bash
# 图片 OCR
curl -X POST http://localhost:3030/ocr \
  -F "file=@image.png" \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true" \
  -F "save_results=true"

# PDF OCR（多页）
curl -X POST http://localhost:3030/ocr \
  -F "file=@document.pdf" \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true" \
  -F "save_results=true"
```

**Python 示例**:
```python
import requests

# OCR 识别
with open("document.pdf", 'rb') as f:
    files = {'file': f}
    data = {
        'base_size': 1024,
        'image_size': 640,
        'crop_mode': True,
        'save_results': True
    }
    response = requests.post("http://localhost:3030/ocr", files=files, data=data)
    result = response.json()

# 下载文本结果
text_url = result['files']['text']
text_response = requests.get(text_url)
text_content = text_response.text
print(text_content)
```

---

### 3. OCR 识别（Base64）

```
POST /ocr/base64
```

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image_base64 | String | ✅ | - | Base64 编码的图片 |
| prompt | String | ❌ | 默认提示词 | 自定义提示词 |
| base_size | Integer | ❌ | 1024 | 基础尺寸 |
| image_size | Integer | ❌ | 640 | 图像尺寸 |
| crop_mode | Boolean | ❌ | true | 是否使用裁剪模式 |

**响应格式**: 与 `/ocr` 相同

**cURL 示例**:
```bash
# Base64 编码图片
IMAGE_BASE64=$(base64 -w 0 image.png)

curl -X POST http://localhost:3030/ocr/base64 \
  -F "image_base64=$IMAGE_BASE64" \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true"
```

---

### 4. 下载结果文件

```
GET /download/{task_id}/{filename}
```

**路径参数**:
- `task_id`: 任务 ID（从 OCR 响应中获取）
- `filename`: 文件名

**可下载的文件**:
- `result.txt` - 纯文本结果（所有页面合并）
- `result.mmd` - Markdown 格式结果
- `result_with_boxes.jpg` - 带边界框的图片

**示例**:
```bash
# 下载文本文件
curl http://your-server:3030/download/044b3b96-51e7-4641-b5ba-6df4bb195b60/result.txt -o result.txt

# 下载 Markdown 文件
curl http://your-server:3030/download/044b3b96-51e7-4641-b5ba-6df4bb195b60/result.mmd -o result.mmd

# 下载可视化图片
curl http://your-server:3030/download/044b3b96-51e7-4641-b5ba-6df4bb195b60/result_with_boxes.jpg -o result_with_boxes.jpg
```

**Python 示例**:
```python
import requests

# 配置 API 地址
API_BASE = "http://your-server:3030"

# 从 OCR 响应获取文件路径
result = {...}  # OCR 响应
text_path = result['files']['text']  # 例如: "/download/xxx/result.txt"

# 下载文本文件
response = requests.get(f"{API_BASE}{text_path}")
with open('result.txt', 'w', encoding='utf-8') as f:
    f.write(response.text)

# 下载图片文件
image_path = result['files']['image_with_boxes']
response = requests.get(f"{API_BASE}{image_path}")
with open('result_with_boxes.jpg', 'wb') as f:
    f.write(response.content)
```

---

### 5. 模型信息

```
GET /models/info
```

**响应示例**:
```json
{
  "model_path": "/models/DeepSeek-OCR",
  "model_loaded": true,
  "cuda_device": "0",
  "supported_modes": {
    "Tiny": {"base_size": 512, "image_size": 512, "crop_mode": false, "tokens": 64},
    "Small": {"base_size": 640, "image_size": 640, "crop_mode": false, "tokens": 100},
    "Base": {"base_size": 1024, "image_size": 1024, "crop_mode": false, "tokens": 256},
    "Large": {"base_size": 1280, "image_size": 1280, "crop_mode": false, "tokens": 400},
    "Gundam (推荐)": {"base_size": 1024, "image_size": 640, "crop_mode": true, "tokens": "dynamic"}
  }
}
```

---

## 推荐模式

**Gundam 模式（推荐）**:
```json
{
  "base_size": 1024,
  "image_size": 640,
  "crop_mode": true
}
```

这是性能和准确度的最佳平衡。

---

## PDF 处理说明

### 自动 PDF 处理
API 会自动检测 PDF 文件并：
1. 将每一页转换为高质量图片（144 DPI）
2. 逐页进行 OCR 识别
3. 合并所有页面的结果
4. 页面间用 `<--- Page Split --->` 分隔

### PDF 响应特点
- `file_type`: "pdf"
- `total_pages`: PDF 总页数
- `pages`: 数组，包含每页的字符数统计
- `files.text`: 包含所有页面合并后的文本

---

## 错误处理

### 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 文件不存在 |
| 500 | 服务器内部错误 |
| 503 | 模型加载中 |

### 错误响应示例
```json
{
  "detail": "PDF 转换失败: 文件格式不支持"
}
```

---

## 性能建议

1. **图片处理**: 单张图片通常在 5-15 秒
2. **PDF 处理**: 每页约 5-15 秒，22 页 PDF 约需 2-5 分钟
3. **超时设置**: 建议设置 600 秒（10 分钟）超时
4. **并发请求**: 根据 GPU 显存调整，建议单请求处理

---

## 安全说明

1. **路径遍历保护**: 下载接口防止 `..` 路径遍历攻击
2. **文件类型检查**: 自动检测 PDF 文件头 (`%PDF-`)
3. **临时文件清理**: 处理完成后自动清理临时文件

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| MODEL_PATH | /models/DeepSeek-OCR | 模型路径 |
| CUDA_VISIBLE_DEVICES | 0 | GPU 设备 ID |
| PORT | 3030 | 服务端口 |

---

## 完整示例

```python
#!/usr/bin/env python3
import requests

# 配置
API_BASE = "http://your-server:3030"

# 1. OCR 识别（PDF 文件）
print("上传 PDF 进行 OCR...")
with open("document.pdf", 'rb') as f:
    response = requests.post(
        f"{API_BASE}/ocr",
        files={'file': f},
        data={
            'base_size': 1024,
            'image_size': 640,
            'crop_mode': True,
            'save_results': True
        },
        timeout=600
    )

result = response.json()
print(f"任务 ID: {result['task_id']}")
print(f"文件类型: {result['file_type']}")
print(f"总页数: {result['total_pages']}")
print(f"总字符数: {result['total_characters']}")

# 2. 下载文本结果
print("\n下载文本结果...")
text_path = result['files']['text']  # 例如: "/download/xxx/result.txt"
text_response = requests.get(f"{API_BASE}{text_path}")
text_content = text_response.text

# 3. 保存到本地
with open('ocr_result.txt', 'w', encoding='utf-8') as f:
    f.write(text_content)

print(f"\n✅ 完成! 结果已保存到 ocr_result.txt")
print(f"文本长度: {len(text_content)} 字符")

# 4. 下载 Markdown 结果（如果存在）
if result['files']['markdown']:
    print("\n下载 Markdown 结果...")
    md_path = result['files']['markdown']
    md_response = requests.get(f"{API_BASE}{md_path}")
    with open('ocr_result.md', 'w', encoding='utf-8') as f:
        f.write(md_response.text)
    print("✅ Markdown 已保存到 ocr_result.md")

# 5. 下载可视化图片（如果存在）
if result['files']['image_with_boxes']:
    print("\n下载可视化图片...")
    img_path = result['files']['image_with_boxes']
    img_response = requests.get(f"{API_BASE}{img_path}")
    with open('result_with_boxes.jpg', 'wb') as f:
        f.write(img_response.content)
    print("✅ 图片已保存到 result_with_boxes.jpg")
```

---

## 更新日志

### v1.0.0 (2025-11-30)
- ✅ 实现文件下载接口
- ✅ 优化 JSON 响应（不包含大量文本）
- ✅ 支持 PDF 自动检测和多页处理
- ✅ 添加安全检查（路径遍历防护）
- ✅ 自动保存结果到文件
