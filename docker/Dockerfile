# Multi-stage Dockerfile for RAG Service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy slim runtime requirements (excludes PySpark, pytest, awscli)
COPY requirements.docker.txt .
RUN pip install --no-cache-dir -r requirements.docker.txt

# Production stage
FROM base as production

# Copy source code and sample documents
COPY src/ ./src/
COPY data/raw/ ./data/raw/

# Create non-root user and set ownership before switching
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# Pre-download ML models as the app user so the cache path matches runtime.
# Without this, models download from HuggingFace on every cold start (~170 MB,
# 60-90s) and fail if HuggingFace is unreachable from the container.
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
print('Models pre-downloaded OK')"

# Disable runtime HuggingFace network calls — models are baked into the image.
ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1

# Expose ports
EXPOSE 8000 8001

# Generous start period — sentence-transformers loads ~170 MB of weights on first inference.
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
