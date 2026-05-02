# FastAPI Application
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from .handlers import rag_service
    from .models import SearchRequest, EmbeddingRequest
    from ..observability.logging_config import StructuredLogger
    from ..observability.metrics import metrics
    from ..observability.tracing import tracing_manager
except ImportError:  # Notebook path when `src` is injected into sys.path
    from service.handlers import rag_service
    from service.models import SearchRequest, EmbeddingRequest
    from observability.logging_config import StructuredLogger
    from observability.metrics import metrics
    from observability.tracing import tracing_manager

# Setup logging
StructuredLogger.setup_logging(json_format=True)
logger = logging.getLogger(__name__)

# Setup tracing
tracing_manager.setup_tracing()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RAG Service")
    metrics.start_server()

    # Initialize with sample data (in production, load from database)
    sample_docs = [
        {"id": "1", "content": "This is a sample document about machine learning."},
        {"id": "2", "content": "Another document discussing artificial intelligence."},
        {"id": "3", "content": "Document about natural language processing and transformers."}
    ]
    # Only initialize if notebook hasn't already done so with real data
    if not rag_service.search_engine:
        try:
            sample_embeddings = await asyncio.to_thread(
                rag_service.embedder.embed_batch,
                [doc["content"] for doc in sample_docs],
            )
        except Exception:
            logger.exception(
                "Failed to precompute sample embeddings; starting with sparse-only search"
            )
            sample_embeddings = []

        rag_service.initialize_search(sample_docs, sample_embeddings)

    yield

    # Shutdown
    logger.info("Shutting down RAG Service")

# Create FastAPI app
app = FastAPI(
    title="RAG at Scale Service",
    description="Distributed RAG service with observability",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "RAG at Scale Service", "status": "running"}

@app.get("/health")
async def health():
    return await rag_service.health_check()

@app.post("/search")
async def search(request: SearchRequest):
    return await rag_service.search(request)

@app.post("/embeddings")
async def generate_embeddings(request: EmbeddingRequest):
    return await rag_service.generate_embeddings(request)

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.service.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
