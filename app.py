"""
DeepSeek-OCR Web API Service
基于 FastAPI 的 OCR 服务
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoModel, AutoTokenizer
import torch
import os
import uuid
from pathlib import Path
import logging
from typing import Optional
import base64
import sys
from io import StringIO
import contextlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DeepSeek-OCR API",
    description="DeepSeek-OCR 文档识别服务",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
model = None
tokenizer = None
MODEL_LOADED = False

# 配置
CUDA_DEVICE = os.getenv("CUDA_VISIBLE_DEVICES", "0")
MODEL_PATH = os.getenv("MODEL_PATH", "/models/DeepSeek-OCR")
UPLOAD_DIR = Path("./uploads")
OUTPUT_DIR = Path("./outputs")

# 创建必要的目录
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@contextlib.contextmanager
def capture_stdout():
    """捕获标准输出"""
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    try:
        yield captured_output
    finally:
        sys.stdout = old_stdout


def extract_ocr_result(output_path: str, captured_stdout: str = None):
    """
    从输出目录或捕获的 stdout 中提取 OCR 结果

    Args:
        output_path: 输出目录路径
        captured_stdout: 捕获的标准输出

    Returns:
        dict: 包含 text 和 files 的字典
    """
    result = {
        "text": "",
        "output_files": [],
        "images": []
    }

    output_dir = Path(output_path)

    # 1. 尝试从输出文件中读取结果
    if output_dir.exists():
        # 查找文本文件（.txt, .md）
        text_files = list(output_dir.glob("*.txt")) + list(output_dir.glob("*.md"))
        for text_file in text_files:
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        result["text"] = content
                        result["output_files"].append(str(text_file.name))
                        logger.info(f"从文件 {text_file.name} 读取到 {len(content)} 字符")
                        break
            except Exception as e:
                logger.warning(f"读取文件 {text_file} 失败: {e}")

        # 查找图片文件
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
        for ext in image_extensions:
            image_files = list(output_dir.glob(f"*{ext}"))
            for img_file in image_files:
                result["images"].append(str(img_file.relative_to(output_dir)))

    # 2. 如果文件中没有找到，尝试从捕获的 stdout 中提取
    if not result["text"] and captured_stdout:
        # 从 stdout 中提取实际的 OCR 输出
        # 通常 OCR 输出在压缩率信息之后
        lines = captured_stdout.split('\n')

        # 寻找实际的文本输出（跳过调试信息）
        text_lines = []
        skip_patterns = ['=', 'image size:', 'valid image tokens:', 'output texts tokens', 'compression ratio:']

        for line in lines:
            # 跳过调试信息行
            if any(pattern in line for pattern in skip_patterns):
                continue
            # 跳过空行
            if not line.strip():
                continue
            text_lines.append(line)

        if text_lines:
            result["text"] = '\n'.join(text_lines).strip()
            logger.info(f"从 stdout 提取到 {len(result['text'])} 字符")

    return result


def load_model():
    """加载模型"""
    global model, tokenizer, MODEL_LOADED

    if MODEL_LOADED:
        logger.info("模型已加载")
        return

    try:
        logger.info(f"开始加载模型: {MODEL_PATH}")
        logger.info(f"使用 CUDA 设备: {CUDA_DEVICE}")

        # 设置 CUDA 设备
        os.environ["CUDA_VISIBLE_DEVICES"] = CUDA_DEVICE

        # 加载 tokenizer
        logger.info("加载 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True
        )

        # 加载模型
        logger.info("加载模型...")
        model = AutoModel.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True,
            use_safetensors=True,
            attn_implementation="eager"  # 禁用 FlashAttention，使用标准attention实现
        )

        # 移动到 GPU 并设置为 eval 模式
        logger.info("将模型移动到 GPU...")
        model = model.eval().cuda().to(torch.bfloat16)

        MODEL_LOADED = True
        logger.info("✅ 模型加载成功！")

    except Exception as e:
        logger.error(f"❌ 模型加载失败: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    logger.info("=" * 50)
    logger.info("DeepSeek-OCR API 服务启动中...")
    logger.info("=" * 50)
    load_model()


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "DeepSeek-OCR API",
        "version": "1.0.0",
        "status": "running" if MODEL_LOADED else "initializing",
        "model_path": MODEL_PATH
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy" if MODEL_LOADED else "loading",
        "model_loaded": MODEL_LOADED
    }


@app.post("/ocr")
async def ocr_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    base_size: int = Form(1024),
    image_size: int = Form(640),
    crop_mode: bool = Form(True),
    save_results: bool = Form(False)
):
    """
    OCR 图片识别

    参数:
    - file: 上传的图片文件
    - prompt: 自定义提示词（可选）
    - base_size: 基础尺寸 (512/640/1024/1280)
    - image_size: 图像尺寸 (512/640/1024/1280)
    - crop_mode: 是否使用裁剪模式
    - save_results: 是否保存结果文件

    支持的模式:
    - Tiny: base_size=512, image_size=512, crop_mode=False
    - Small: base_size=640, image_size=640, crop_mode=False
    - Base: base_size=1024, image_size=1024, crop_mode=False
    - Large: base_size=1280, image_size=1280, crop_mode=False
    - Gundam (推荐): base_size=1024, image_size=640, crop_mode=True
    """

    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="模型正在加载中，请稍后再试")

    # 生成唯一ID
    task_id = str(uuid.uuid4())

    try:
        # 保存上传的文件
        file_ext = Path(file.filename).suffix
        upload_path = UPLOAD_DIR / f"{task_id}{file_ext}"

        logger.info(f"开始处理任务: {task_id}")
        logger.info(f"文件名: {file.filename}")

        # 保存文件
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"文件已保存: {upload_path}")

        # 设置提示词
        if prompt is None:
            prompt = "<image>\n<|grounding|>Convert the document to markdown."

        # 设置输出路径
        output_path = str(OUTPUT_DIR / task_id)
        os.makedirs(output_path, exist_ok=True)

        logger.info(f"开始 OCR 识别...")
        logger.info(f"  - prompt: {prompt}")
        logger.info(f"  - base_size: {base_size}")
        logger.info(f"  - image_size: {image_size}")
        logger.info(f"  - crop_mode: {crop_mode}")

        # 执行 OCR - 捕获 stdout 输出
        with capture_stdout() as captured:
            infer_result = model.infer(
                tokenizer,
                prompt=prompt,
                image_file=str(upload_path),
                output_path=output_path,
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
                save_results=True,  # 强制保存结果以便提取
                test_compress=True
            )

        # 获取捕获的输出
        stdout_content = captured.getvalue()
        logger.info(f"捕获的 stdout 长度: {len(stdout_content)}")

        logger.info(f"✅ OCR 识别完成: {task_id}")

        # 从输出目录或 stdout 中提取结果
        ocr_result = extract_ocr_result(output_path, stdout_content)

        # 准备响应
        response_data = {
            "task_id": task_id,
            "status": "success",
            "text": ocr_result["text"],  # OCR 识别的文本
            "output_files": ocr_result["output_files"],  # 输出的文本文件
            "images": ocr_result["images"],  # 输出的图片文件
            "output_path": output_path if save_results else None,  # 输出目录
            "settings": {
                "prompt": prompt,
                "base_size": base_size,
                "image_size": image_size,
                "crop_mode": crop_mode
            }
        }

        # 清理上传的文件（可选）
        if not save_results:
            upload_path.unlink()

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"❌ OCR 处理失败: {str(e)}")

        # 清理文件
        if upload_path.exists():
            upload_path.unlink()

        raise HTTPException(status_code=500, detail=f"OCR 处理失败: {str(e)}")


@app.post("/ocr/base64")
async def ocr_base64(
    image_base64: str = Form(...),
    prompt: Optional[str] = Form(None),
    base_size: int = Form(1024),
    image_size: int = Form(640),
    crop_mode: bool = Form(True)
):
    """
    OCR 图片识别（Base64 输入）

    参数:
    - image_base64: Base64 编码的图片
    - prompt: 自定义提示词
    - base_size: 基础尺寸
    - image_size: 图像尺寸
    - crop_mode: 是否使用裁剪模式
    """

    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="模型正在加载中，请稍后再试")

    task_id = str(uuid.uuid4())

    try:
        # 解码 base64 图片
        image_data = base64.b64decode(image_base64)
        upload_path = UPLOAD_DIR / f"{task_id}.jpg"

        with open(upload_path, "wb") as f:
            f.write(image_data)

        logger.info(f"处理 Base64 图片: {task_id}")

        # 设置提示词
        if prompt is None:
            prompt = "<image>\n<|grounding|>Convert the document to markdown."

        # 设置输出路径
        output_path = str(OUTPUT_DIR / task_id)
        os.makedirs(output_path, exist_ok=True)

        # 执行 OCR - 捕获 stdout 输出
        with capture_stdout() as captured:
            infer_result = model.infer(
                tokenizer,
                prompt=prompt,
                image_file=str(upload_path),
                output_path=output_path,
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
                save_results=True,  # 强制保存结果以便提取
                test_compress=True
            )

        # 获取捕获的输出
        stdout_content = captured.getvalue()
        logger.info(f"捕获的 stdout 长度: {len(stdout_content)}")

        logger.info(f"✅ OCR 识别完成: {task_id}")

        # 从输出目录或 stdout 中提取结果
        ocr_result = extract_ocr_result(output_path, stdout_content)

        # 清理文件
        upload_path.unlink()

        return JSONResponse(content={
            "task_id": task_id,
            "status": "success",
            "text": ocr_result["text"],
            "output_files": ocr_result["output_files"],
            "images": ocr_result["images"],
            "output_path": output_path
        })

    except Exception as e:
        logger.error(f"❌ OCR 处理失败: {str(e)}")
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"OCR 处理失败: {str(e)}")


@app.get("/models/info")
async def model_info():
    """获取模型信息"""
    return {
        "model_path": MODEL_PATH,
        "model_loaded": MODEL_LOADED,
        "cuda_device": CUDA_DEVICE,
        "supported_modes": {
            "Tiny": {"base_size": 512, "image_size": 512, "crop_mode": False, "tokens": 64},
            "Small": {"base_size": 640, "image_size": 640, "crop_mode": False, "tokens": 100},
            "Base": {"base_size": 1024, "image_size": 1024, "crop_mode": False, "tokens": 256},
            "Large": {"base_size": 1280, "image_size": 1280, "crop_mode": False, "tokens": 400},
            "Gundam (推荐)": {"base_size": 1024, "image_size": 640, "crop_mode": True, "tokens": "dynamic"}
        }
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "3030"))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
