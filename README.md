# DeepSeek-OCR Web API

A FastAPI-based web service wrapper for DeepSeek-OCR model.

## Features

- RESTful API for OCR processing
- Docker deployment support
- Multiple inference modes (Tiny/Small/Base/Large/Gundam)
- File upload and Base64 input support
- Automatic API documentation with Swagger UI

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
pip install -r requirements-api.txt

# Run service
python app.py
```

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /models/info` - Model information
- `POST /ocr` - OCR with file upload
- `POST /ocr/base64` - OCR with Base64 input
- `GET /docs` - Interactive API documentation

## API Response Format

The API now returns structured results with the following format:

```json
{
  "task_id": "unique-task-id",
  "status": "success",
  "text": "OCR recognized text content...",
  "output_files": ["result.md"],
  "images": ["output_image.png"],
  "output_path": "/outputs/task-id",
  "settings": {
    "prompt": "...",
    "base_size": 1024,
    "image_size": 640,
    "crop_mode": true
  }
}
```

**Response Fields:**
- `task_id`: Unique identifier for this OCR task
- `status`: Processing status ("success" or "error")
- `text`: The OCR recognized text content
- `output_files`: List of generated text files (.txt, .md)
- `images`: List of generated image files
- `output_path`: Directory path where output files are saved
- `settings`: The parameters used for this OCR request

## Usage Example

### Python

```python
import requests

with open("document.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:3030/ocr",
        files={"file": f},
        data={
            "prompt": "<image>\n<|grounding|>Convert the document to markdown.",
            "base_size": 1024,
            "image_size": 640,
            "crop_mode": True,
            "save_results": True
        }
    )

    result = response.json()
    print(f"Task ID: {result['task_id']}")
    print(f"Recognized Text:\n{result['text']}")
    print(f"Output Files: {result['output_files']}")
    print(f"Output Images: {result['images']}")
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
