# Python 3.12 Slim base image
FROM python:3.12-slim

# Set environment variables for extreme memory efficiency
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PORT=8000 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    TRANSFORMERS_OFFLINE=0

# Set work directory
WORKDIR /app

# Install minimal system dependencies & OCR packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-tur \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*


# Install PyTorch CPU-only (saves 2.5GB and prevents CUDA memory overhead)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download & cache KeyBERT model in the Docker image during build time
RUN python -c "\
from keybert import KeyBERT; \
KeyBERT(model='all-MiniLM-L6-v2'); \
print('KeyBERT model baked into Docker image successfully!'); \
"

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI application with single worker & dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
