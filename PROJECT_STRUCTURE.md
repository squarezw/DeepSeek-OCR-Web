# DeepSeek-OCR Web API - 项目结构

> 最终的项目文件结构（2025-11-30）

## 📁 目录结构

```
DeepSeek-OCR-Web/
├── app.py                    # ✅ FastAPI 主应用（核心服务）
├── test_api.py               # ✅ API 文件上传测试
├── test_base64_ocr.py        # ✅ Base64 OCR 测试
│
├── Dockerfile                # Docker 镜像构建文件
├── docker-compose.yml        # Docker Compose 配置
├── requirements.txt          # Python 依赖（完整的 API 服务依赖）
├── .env.example             # 环境变量模板
├── .gitignore               # Git 忽略配置
│
├── README.md                # 主文档
├── CHANGES.md               # 修复说明
├── DEPLOYMENT.md            # 部署指南
├── README_ORIGINAL.md       # 原始文档
│
├── scripts/                 # 工具脚本
│   └── fix_cuda_device.py  # CUDA 修复脚本（已执行）
│
├── models/                  # 模型目录
│   └── DeepSeek-OCR/       # DeepSeek-OCR 模型
│       └── modeling_deepseekocr.py  # 已修复 CUDA
│
├── demo/                    # 测试图片
├── uploads/                 # 上传目录
├── outputs/                 # 输出目录
└── assets/                  # 资源文件
```

## 📝 核心文件

### Python 文件（3个）
- `app.py` - FastAPI 主应用
- `test_api.py` - 文件上传测试
- `test_base64_ocr.py` - Base64 测试

### 配置文件（5个）
- `Dockerfile` - Docker 镜像构建
- `docker-compose.yml` - 服务编排
- `requirements.txt` - **Python 依赖（标准命名）**
- `.env.example` - 环境变量模板
- `.gitignore` - Git 忽略

### 文档文件（4个）
- `README.md` - 主文档
- `CHANGES.md` - 修复说明
- `DEPLOYMENT.md` - 部署指南
- `README_ORIGINAL.md` - 原始文档

## 🗑️ 已删除的文件

- ✅ 45+ 个调试/修复脚本
- ✅ 所有备份文件 (*.backup, *.orig, .swp)
- ✅ 所有补丁文件 (*.patch)
- ✅ requirements-api.txt（已重命名为 requirements.txt）
- ✅ 无用的部署脚本

## 🚀 部署状态

**路径**: `/var/www/DeepSeek-OCR-Web`
**容器**: `deepseek-ocr-api`
**端口**: 3030
**状态**: ✅ 运行中

## 📊 API 端点

- `GET /` - 服务信息
- `GET /health` - 健康检查
- `POST /ocr` - 文件上传 OCR ✅
- `POST /ocr/base64` - Base64 OCR ✅

---

**最后更新**: 2025-11-30
**清理完成**: 只保留必要文件
