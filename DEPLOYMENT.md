# DeepSeek-OCR Web API 部署文档

## 问题诊断与解决

### 问题：无法连接到 huggingface.co

**错误信息**:
```
Max retries exceeded with url: /deepseek-ai/DeepSeek-OCR/resolve/main/tokenizer_config.json
Network is unreachable
```

**原因**: AI 服务器无法直接访问 Hugging Face

**解决方案**: 使用 Hugging Face 镜像站下载模型到本地

---

## 部署步骤

### 步骤 1: 下载模型到本地

在 AI 服务器上执行：

```bash
# 进入项目目录
cd /var/www/DeepSeek-OCR-Web

# 设置 Hugging Face 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 安装 huggingface-cli
pip install -U huggingface_hub

# 下载模型
mkdir -p /var/www/DeepSeek-OCR/models
huggingface-cli download deepseek-ai/DeepSeek-OCR \
    --local-dir /var/www/DeepSeek-OCR/models/DeepSeek-OCR \
    --local-dir-use-symlinks False
```

**注意**: 模型约 10GB，下载需要一些时间。

### 步骤 2: 克隆 Web 服务代码到 AI 服务器

```bash
# 在 AI 服务器上
cd /var/www
git clone <your-repo-url> DeepSeek-OCR-Web

# 或者从本地推送
# 在本地:
cd /Users/zhaowei/Documents/AI/DeepSeek-OCR-Web
git add .
git commit -m "Add DeepSeek-OCR Web API service"
git push origin main

# 在 AI 服务器:
cd /var/www
git clone <your-repo-url> DeepSeek-OCR-Web
```

### 步骤 3: 构建 Docker 镜像

```bash
cd /var/www/DeepSeek-OCR-Web

# 构建镜像
docker build -t deepseek-ocr-api:latest .
```

### 步骤 4: 启动服务

```bash
# 使用 docker-compose 启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 步骤 5: 验证服务

```bash
# 检查容器状态
docker ps | grep deepseek-ocr-api

# 健康检查
curl http://localhost:3030/health

# 获取模型信息
curl http://localhost:3030/models/info
```

---

## API 使用说明

### 1. 健康检查

```bash
curl http://localhost:3030/health
```

### 2. OCR 识别（文件上传）

```bash
curl -X POST http://localhost:3030/ocr \
  -F "file=@/path/to/image.jpg" \
  -F "prompt=<image>\n<|grounding|>Convert the document to markdown." \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true"
```

### 3. OCR 识别（Base64）

```python
import requests
import base64

# 读取图片并转为 base64
with open("image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# 发送请求
response = requests.post(
    "http://localhost:3030/ocr/base64",
    data={
        "image_base64": image_base64,
        "prompt": "<image>\n<|grounding|>Convert the document to markdown.",
        "base_size": 1024,
        "image_size": 640,
        "crop_mode": True
    }
)

print(response.json())
```

### 4. 获取模型信息

```bash
curl http://localhost:3030/models/info
```

---

## 支持的模式

| 模式 | base_size | image_size | crop_mode | vision tokens |
|------|-----------|------------|-----------|---------------|
| Tiny | 512 | 512 | False | 64 |
| Small | 640 | 640 | False | 100 |
| Base | 1024 | 1024 | False | 256 |
| Large | 1280 | 1280 | False | 400 |
| Gundam (推荐) | 1024 | 640 | True | 动态 |

---

## 配置 Nginx 反向代理

在 AI 服务器的 Nginx 配置中添加：

```nginx
# DeepSeek-OCR API 服务
location /api/ocr/ {
    proxy_pass http://127.0.0.1:3030/;

    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # 大文件上传支持
    client_max_body_size 20M;
    proxy_request_buffering off;

    # 超时设置（OCR 处理可能需要较长时间）
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```

重载 Nginx:

```bash
nginx -t
nginx -s reload
```

---

## 故障排查

### 1. 模型加载失败

**检查模型文件**:
```bash
ls -lh /var/www/DeepSeek-OCR/models/DeepSeek-OCR
```

**查看容器日志**:
```bash
docker-compose logs -f deepseek-ocr-api
```

### 2. CUDA 不可用

**检查 CUDA**:
```bash
docker run --rm --gpus all pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime nvidia-smi
```

### 3. 内存不足

**调整 Docker 内存限制**（在 docker-compose.yml 中）:
```yaml
deploy:
  resources:
    limits:
      memory: 16G
```

### 4. 端口冲突

**检查端口占用**:
```bash
netstat -tlnp | grep 3030
```

**修改端口**（在 docker-compose.yml 中）:
```yaml
ports:
  - "3031:3030"  # 使用其他端口
```

---

## 性能优化

### 1. 使用 GPU 加速

确保 Docker 可以访问 GPU:

```bash
# 安装 nvidia-container-toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. 模型量化（可选）

使用 bfloat16 或 int8 量化减少内存使用。

### 3. 批处理

如果需要处理大量图片，考虑实现批处理接口。

---

## 监控和日志

### 查看实时日志

```bash
docker-compose logs -f deepseek-ocr-api
```

### 查看容器资源使用

```bash
docker stats deepseek-ocr-api
```

### 日志文件位置

- 应用日志: `docker-compose logs`
- 上传文件: `./uploads/`
- 输出文件: `./outputs/`

---

## 更新和维护

### 更新代码

```bash
cd /var/www/DeepSeek-OCR-Web
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

### 备份

```bash
# 备份模型（如果重新下载）
tar -czf deepseek-ocr-model-backup.tar.gz /var/www/DeepSeek-OCR/models/

# 备份配置
cp docker-compose.yml docker-compose.yml.backup
```

### 清理旧文件

```bash
# 清理上传文件（7天前）
find ./uploads -type f -mtime +7 -delete

# 清理输出文件（7天前）
find ./outputs -type f -mtime +7 -delete
```

---

## 安全建议

1. **限制访问**: 使用 Nginx 限制 API 访问来源
2. **文件大小限制**: 限制上传文件大小（已设置 20MB）
3. **定期清理**: 自动清理临时文件
4. **日志监控**: 监控异常请求和错误日志

---

## 常见问题

### Q: 模型加载需要多长时间？

A: 首次加载约 1-2 分钟，具体取决于硬件配置。

### Q: 支持哪些图片格式？

A: 支持常见格式：JPG, PNG, BMP, TIFF 等。

### Q: 单个请求处理需要多长时间？

A: 根据图片大小和模式，通常 2-10 秒。

### Q: 可以并发处理请求吗？

A: 可以，但受 GPU 内存限制。建议单 GPU 并发 2-4 个请求。

---

## 联系和支持

如有问题，请查看：
- DeepSeek-OCR 官方文档
- 项目 GitHub Issues
- 服务器日志

---

**最后更新**: 2025-11-30
**版本**: 1.0.0
