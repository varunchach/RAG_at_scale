# Configuration Management
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings  # pydantic v2: BaseSettings in separate package

class Settings(BaseSettings):
    # Project paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    embeddings_dir: Path = data_dir / "embeddings"

    # Spark configuration
    spark_master: str = "local[*]"
    spark_app_name: str = "RAG_at_Scale"

    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Service
    service_host: str = "0.0.0.0"
    service_port: int = 8000

    # Observability
    otlp_endpoint: Optional[str] = None
    prometheus_port: int = 8001

    class Config:
        env_file = ".env"

settings = Settings()
