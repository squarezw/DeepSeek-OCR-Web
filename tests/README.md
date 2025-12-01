# DeepSeek-OCR API 测试文件

此目录包含用于测试 DeepSeek-OCR API 的各种脚本。

## 测试文件

### 1. test_api.py
基础 API 测试脚本，测试文件上传 OCR 功能。

**使用方法**:
```bash
python tests/test_api.py
```

### 2. test_base64_ocr.py
Base64 编码图片的 OCR 测试。

**使用方法**:
```bash
python tests/test_base64_ocr.py
```

### 3. test_pdf_ocr.py
PDF 多页文档的 OCR 测试。

**使用方法**:
```bash
python tests/test_pdf_ocr.py
```

### 4. test_pdf_simple.py
简化的 PDF 单页测试。

**使用方法**:
```bash
python tests/test_pdf_simple.py
```

### 5. test_new_api.py
新版 API（文件下载版本）的测试脚本。

**使用方法**:
```bash
python tests/test_new_api.py
```

**配置**:
- 修改脚本中的 `API_URL` 为你的服务器地址
- 确保测试图片/PDF 文件路径正确

### 6. test_download_api.sh
Shell 脚本，完整测试下载 API 功能。

**使用方法**:
```bash
bash tests/test_download_api.sh
```

## 配置说明

所有测试脚本默认连接到 `http://localhost:3030`。

如果您的服务部署在其他地址，请修改脚本中的 API 地址：

```python
# Python 脚本
API_BASE = "http://your-server:3030"
```

```bash
# Shell 脚本
API_BASE="http://your-server:3030"
```

## 测试数据

测试脚本使用以下测试数据（需要存在于服务器上）：
- `/var/www/DeepSeek-OCR-Web/demo/paddleocr_vl_demo.png` - 测试图片
- `/var/www/DeepSeek-OCR-Web/DeepSeek_OCR_paper.pdf` - 测试 PDF

如果在本地运行，请确保相应的测试文件存在。

## 常见问题

### 连接超时
PDF 处理可能需要较长时间，建议设置更长的超时：
```python
response = requests.post(..., timeout=600)  # 10 minutes
```

### 模型加载中
如果收到 503 错误，说明模型正在加载，请等待片刻后重试。

### 文件路径错误
确保测试数据文件路径与脚本中的路径一致。
