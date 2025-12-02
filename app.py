"""
DeepSeek-OCR Web API Service
基于 FastAPI 的 OCR 服务
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoModel, AutoTokenizer
import torch
import os
import uuid
from pathlib import Path
import logging
from typing import Optional, List
import base64
import sys
from io import StringIO, BytesIO
import contextlib
import fitz  # PyMuPDF
from PIL import Image

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


def is_pdf(file_path: str) -> bool:
    """检查文件是否为 PDF"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            return header == b'%PDF-'
    except:
        return False


def pdf_to_images(pdf_path: str, dpi: int = 144) -> List[str]:
    """
    将 PDF 转换为图片

    Args:
        pdf_path: PDF 文件路径
        dpi: 图片 DPI（默认 144，即 2x 缩放）

    Returns:
        List[str]: 生成的图片路径列表
    """
    image_paths = []
    pdf_doc = fitz.open(pdf_path)

    # 计算缩放比例
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    # 为每一页创建图片
    for page_num in range(pdf_doc.page_count):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # 转换为 PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(BytesIO(img_data))

        # 保存图片
        base_name = Path(pdf_path).stem
        image_path = str(Path(pdf_path).parent / f"{base_name}_page_{page_num + 1}.png")
        img.save(image_path)
        image_paths.append(image_path)

        logger.info(f"PDF 第 {page_num + 1}/{pdf_doc.page_count} 页已转换: {img.width}x{img.height}")

    pdf_doc.close()
    return image_paths


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

        # 检查 CUDA 是否可用
        use_cuda = torch.cuda.is_available()
        device = torch.device("cuda" if use_cuda else "cpu")

        if use_cuda:
            logger.info(f"使用 CUDA 设备: {CUDA_DEVICE}")
            os.environ["CUDA_VISIBLE_DEVICES"] = CUDA_DEVICE
        else:
            logger.info("CUDA 不可用，使用 CPU 模式")

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

        # 移动到设备并设置为 eval 模式
        logger.info(f"将模型移动到 {device}...")
        model = model.eval().to(device)

        # 如果使用 CUDA，转换为 bfloat16 以节省显存
        if use_cuda:
            model = model.to(torch.bfloat16)

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

        # 检查是否为 PDF，如果是则转换为图片
        image_files = []
        if is_pdf(str(upload_path)):
            logger.info(f"检测到 PDF 文件，开始转换...")
            try:
                image_files = pdf_to_images(str(upload_path))
                logger.info(f"PDF 转换完成，共 {len(image_files)} 页")
            except Exception as e:
                logger.error(f"PDF 转换失败: {e}")
                raise HTTPException(status_code=400, detail=f"PDF 转换失败: {str(e)}")
        else:
            # 普通图片文件
            image_files = [str(upload_path)]

        # 设置提示词
        if prompt is None:
            prompt = "<image>\n<|grounding|>Convert the document to markdown."

        # 设置输出路径
        output_path = str(OUTPUT_DIR / task_id)
        os.makedirs(output_path, exist_ok=True)

        logger.info(f"开始 OCR 识别...")
        logger.info(f"  - 文件数: {len(image_files)}")
        logger.info(f"  - prompt: {prompt}")
        logger.info(f"  - base_size: {base_size}")
        logger.info(f"  - image_size: {image_size}")
        logger.info(f"  - crop_mode: {crop_mode}")

        # 处理所有图片（单图片或 PDF 的多页）
        all_results = []
        for idx, image_file in enumerate(image_files, 1):
            logger.info(f"处理第 {idx}/{len(image_files)} 页...")

            # 执行 OCR - 捕获 stdout 输出
            with capture_stdout() as captured:
                infer_result = model.infer(
                    tokenizer,
                    prompt=prompt,
                    image_file=str(image_file),
                    output_path=output_path,
                    base_size=base_size,
                    image_size=image_size,
                    crop_mode=crop_mode,
                    save_results=True,  # 强制保存结果以便提取
                    test_compress=True
                )

            # 获取捕获的输出
            stdout_content = captured.getvalue()

            # 从输出目录或 stdout 中提取结果
            page_result = extract_ocr_result(output_path, stdout_content)
            all_results.append({
                "page": idx,
                "text": page_result["text"],
                "text_length": len(page_result["text"])
            })

            logger.info(f"第 {idx} 页识别完成，文本长度: {len(page_result['text'])}")

        # 清理转换的图片文件
        if is_pdf(str(upload_path)):
            for img_file in image_files:
                try:
                    Path(img_file).unlink()
                except:
                    pass

        logger.info(f"✅ OCR 识别完成: {task_id}")

        # 合并所有页面的结果并保存到文件
        combined_text = "\n\n<--- Page Split --->\n\n".join([r["text"] for r in all_results])

        # 保存合并后的文本到文件
        result_file = Path(output_path) / "result.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(combined_text)

        logger.info(f"结果已保存到: {result_file}")

        # 获取最终结果文件列表
        final_result = extract_ocr_result(output_path, None)

        # 构建文件路径（相对路径）
        result_files = {
            "text": f"/download/{task_id}/result.txt",
            "markdown": f"/download/{task_id}/result.mmd" if Path(output_path, "result.mmd").exists() else None,
            "image_with_boxes": f"/download/{task_id}/result_with_boxes.jpg" if Path(output_path, "result_with_boxes.jpg").exists() else None
        }

        # 准备响应（不包含大量文本内容）
        response_data = {
            "task_id": task_id,
            "status": "success",
            "file_type": "pdf" if is_pdf(str(upload_path)) else "image",
            "total_pages": len(image_files),
            "total_characters": len(combined_text),
            "pages": [
                {
                    "page": r["page"],
                    "text_length": r["text_length"]
                } for r in all_results
            ],
            "files": result_files,
            "output_path": output_path if save_results else None,
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

        # 保存文本结果到文件
        result_file = Path(output_path) / "result.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(ocr_result["text"])

        logger.info(f"结果已保存到: {result_file}")

        # 构建文件路径（相对路径）
        result_files = {
            "text": f"/download/{task_id}/result.txt",
            "markdown": f"/download/{task_id}/result.mmd" if Path(output_path, "result.mmd").exists() else None,
            "image_with_boxes": f"/download/{task_id}/result_with_boxes.jpg" if Path(output_path, "result_with_boxes.jpg").exists() else None
        }

        # 清理文件
        upload_path.unlink()

        return JSONResponse(content={
            "task_id": task_id,
            "status": "success",
            "file_type": "image",
            "total_pages": 1,
            "total_characters": len(ocr_result["text"]),
            "files": result_files,
            "output_path": output_path
        })

    except Exception as e:
        logger.error(f"❌ OCR 处理失败: {str(e)}")
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"OCR 处理失败: {str(e)}")


@app.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """
    下载 OCR 结果文件

    参数:
    - task_id: 任务 ID
    - filename: 文件名（result.txt, result.mmd, result_with_boxes.jpg 等）

    返回:
    文件内容
    """
    # 安全检查：防止路径遍历攻击
    if ".." in task_id or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="非法的文件路径")

    # 构建文件路径
    file_path = OUTPUT_DIR / task_id / filename

    # 检查文件是否存在
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    # 检查是否为文件（不是目录）
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="请求的不是一个文件")

    # 返回文件
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


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
