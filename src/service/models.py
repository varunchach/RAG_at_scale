# Pydantic Models for API
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    rerank: bool = True
    alpha: float = 0.6   # 0.0 = pure keyword (BM25), 1.0 = pure semantic (dense)
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    doc_id: str
    content: str
    score: float
    rerank_score: Optional[float] = None
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    rerank_time: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2"

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    processing_time: float
