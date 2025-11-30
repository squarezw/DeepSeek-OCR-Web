# DeepSeek-OCR Web API

基于 FastAPI 的 DeepSeek-OCR 文档识别 Web 服务

## 快速开始

### 在 AI 服务器上部署

```bash
# 1. 克隆或上传代码到服务器
cd /var/www
# git clone <your-repo>

# 2. 执行一键部署脚本
cd /var/www/DeepSeek-OCR-Web
chmod +x deploy.sh
./deploy.sh
```

部署脚本会自动：
- ✅ 检查并下载模型（如果不存在）
- ✅ 构建 Docker 镜像
- ✅ 启动服务
- ✅ 健康检查

### 手动部署步骤

详见 [DEPLOYMENT.md](DEPLOYMENT.md)

## API 文档

启动服务后访问: http://localhost:3030/docs

### 端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/ocr` | POST | OCR 识别（文件上传） |
| `/ocr/base64` | POST | OCR 识别（Base64） |
| `/models/info` | GET | 模型信息 |

## 使用示例

### 1. Python 客户端

```python
import requests

# 上传文件进行 OCR
with open("document.jpg", "rb") as f:
    files = {"file": f}
    data = {
        "prompt": "<image>\n<|grounding|>Convert the document to markdown.",
        "base_size": 1024,
        "image_size": 640,
        "crop_mode": True
    }
    response = requests.post("http://localhost:3030/ocr", files=files, data=data)
    result = response.json()
    print(result["result"])
```

### 2. cURL 命令

```bash
curl -X POST http://localhost:3030/ocr \
  -F "file=@document.jpg" \
  -F "prompt=<image>\n<|grounding|>Convert the document to markdown." \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true"
```

### 3. JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('document.jpg'));
form.append('prompt', '<image>\n<|grounding|>Convert the document to markdown.');
form.append('base_size', '1024');
form.append('image_size', '640');
form.append('crop_mode', 'true');

axios.post('http://localhost:3030/ocr', form, {
    headers: form.getHeaders()
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 3030 | 服务端口 |
| MODEL_PATH | /models/DeepSeek-OCR | 模型路径 |
| CUDA_VISIBLE_DEVICES | 0 | GPU 设备 |

### 支持的模式

| 模式 | base_size | image_size | crop_mode | 说明 |
|------|-----------|------------|-----------|------|
| Tiny | 512 | 512 | false | 64 vision tokens |
| Small | 640 | 640 | false | 100 vision tokens |
| Base | 1024 | 1024 | false | 256 vision tokens |
| Large | 1280 | 1280 | false | 400 vision tokens |
| Gundam | 1024 | 640 | true | 动态 tokens (推荐) |

## 性能建议

- **推荐模式**: Gundam (base_size=1024, image_size=640, crop_mode=true)
- **并发请求**: 单 GPU 建议 2-4 个并发
- **图片大小**: 建议不超过 10MB
- **超时设置**: OCR 处理时间 2-10 秒

## 故障排查

### 查看日志

```bash
docker-compose logs -f deepseek-ocr-api
```

### 重启服务

```bash
docker-compose restart
```

### 检查 GPU

```bash
docker exec deepseek-ocr-api nvidia-smi
```

## 项目结构

```
DeepSeek-OCR-Web/
├── app.py                    # FastAPI 应用
├── Dockerfile                # Docker 镜像定义
├── docker-compose.yml        # Docker Compose 配置
├── requirements-api.txt      # Python 依赖
├── deploy.sh                 # 一键部署脚本
├── download_model.sh         # 模型下载脚本
├── DEPLOYMENT.md             # 详细部署文档
└── README_API.md             # 本文档
```

## 相关链接

- [DeepSeek-OCR 官方仓库](https://github.com/deepseek-ai/DeepSeek-OCR)
- [DeepSeek-OCR 论文](https://arxiv.org/abs/2510.18234)
- [模型下载](https://huggingface.co/deepseek-ai/DeepSeek-OCR)

## 许可证

本项目遵循原 DeepSeek-OCR 项目的许可证。

---

**最后更新**: 2025-11-30
**版本**: 1.0.0
