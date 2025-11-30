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
# Build image
docker build -t deepseek-ocr-api:latest .

# Run container
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
            "crop_mode": True
        }
    )
    print(response.json())
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

Environment variables:

- `PORT` - Service port (default: 3030)
- `MODEL_PATH` - Path to DeepSeek-OCR model
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
