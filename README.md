# DeepSeek-OCR Web API

A FastAPI-based web service wrapper for DeepSeek-OCR model.

## Features

- 🚀 RESTful API for OCR processing
- 📄 **Automatic PDF detection and multi-page processing**
- 📦 Docker deployment support
- 🎯 Multiple inference modes (Tiny/Small/Base/Large/Gundam)
- 📤 File upload and Base64 input support
- 📥 **File download API for results**
- 🔄 Optimized JSON responses (no large text in JSON)
- 📚 Automatic API documentation with Swagger UI

## Quick Start

### Using Docker

```bash
# 1. Create .env file with your configuration
cp .env.example .env
# Edit .env and set MODEL_LOCAL_PATH to your model directory

# 2. Build image
docker build -t deepseek-ocr-api:latest .

# 3. Run container
docker-compose up -d
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python app.py
```

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /models/info` - Model information
- `POST /ocr` - OCR with file upload (supports images and PDFs)
- `POST /ocr/base64` - OCR with Base64 input (images only)
- `GET /download/{task_id}/{filename}` - **Download result files**
- `GET /docs` - Interactive API documentation

See [API.md](API.md) for detailed API documentation.

## API Response Format

The API returns **optimized responses** with file download URLs instead of large text content:

```json
{
  "task_id": "044b3b96-51e7-4641-b5ba-6df4bb195b60",
  "status": "success",
  "file_type": "image",
  "total_pages": 1,
  "total_characters": 4392,
  "pages": [
    {"page": 1, "text_length": 4392}
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

**Response Fields:**
- `task_id`: Unique identifier for this OCR task
- `status`: Processing status ("success" or "error")
- `file_type`: File type ("image" or "pdf")
- `total_pages`: Total number of pages processed
- `total_characters`: Total character count
- `pages`: Array of page statistics (for PDFs)
- `files`: **Download URLs for result files** (text, markdown, images)
- `output_path`: Directory path where output files are saved
- `settings`: The parameters used for this OCR request

**Key Advantage:** JSON responses are small and fast, even for large PDFs!

## Usage Example

### Python - Image OCR

```python
import requests

# Step 1: Upload and process
with open("document.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:3030/ocr",
        files={"file": f},
        data={
            "base_size": 1024,
            "image_size": 640,
            "crop_mode": True,
            "save_results": True
        }
    )

result = response.json()
print(f"Task ID: {result['task_id']}")
print(f"Total characters: {result['total_characters']}")

# Step 2: Download text result
API_BASE = "http://your-server:3030"
text_path = result['files']['text']
text_response = requests.get(f"{API_BASE}{text_path}")
text_content = text_response.text

print(f"OCR Result:\n{text_content[:500]}...")  # First 500 chars
```

### Python - PDF OCR (Multi-page)

```python
import requests

# Step 1: Upload PDF
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:3030/ocr",
        files={"file": f},
        data={
            "base_size": 1024,
            "image_size": 640,
            "crop_mode": True,
            "save_results": True
        },
        timeout=600  # 10 minutes for large PDFs
    )

result = response.json()
print(f"Task ID: {result['task_id']}")
print(f"File type: {result['file_type']}")  # "pdf"
print(f"Total pages: {result['total_pages']}")
print(f"Total characters: {result['total_characters']}")

# Step 2: Download combined text
API_BASE = "http://your-server:3030"
text_path = result['files']['text']
text_response = requests.get(f"{API_BASE}{text_path}")

# Save to file
with open('ocr_result.txt', 'w', encoding='utf-8') as f:
    f.write(text_response.text)

print("✅ Result saved to ocr_result.txt")
```

### cURL

```bash
curl -X POST http://localhost:3030/ocr \
  -F "file=@document.jpg" \
  -F "base_size=1024" \
  -F "image_size=640" \
  -F "crop_mode=true"
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env and set MODEL_LOCAL_PATH to your model directory
```

Environment variables:

- `MODEL_LOCAL_PATH` - Local path to DeepSeek-OCR model directory (required, set in .env file)
- `PORT` - Service port (default: 3030)
- `MODEL_PATH` - Path to model inside container (default: /models/DeepSeek-OCR)
- `CUDA_VISIBLE_DEVICES` - GPU device (default: 0)

## Supported Modes

| Mode | base_size | image_size | crop_mode | Vision Tokens |
|------|-----------|------------|-----------|---------------|
| Tiny | 512 | 512 | false | 64 |
| Small | 640 | 640 | false | 100 |
| Base | 1024 | 1024 | false | 256 |
| Large | 1280 | 1280 | false | 400 |
| Gundam (Recommended) | 1024 | 640 | true | Dynamic |

## Requirements

- Python 3.8+
- CUDA 11.8+
- PyTorch 2.6.0+
- DeepSeek-OCR model files

## License

This project follows the license of the original DeepSeek-OCR project.

## Related Links

- [DeepSeek-OCR Official Repository](https://github.com/deepseek-ai/DeepSeek-OCR)
- [DeepSeek-OCR Paper](https://arxiv.org/abs/2510.18234)
- [Model Download](https://huggingface.co/deepseek-ai/DeepSeek-OCR)

## Acknowledgements

Thanks to the DeepSeek AI team for the excellent DeepSeek-OCR model.
