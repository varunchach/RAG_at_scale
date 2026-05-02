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

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
