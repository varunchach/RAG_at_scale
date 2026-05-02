# FastAPI Application
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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

StructuredLogger.setup_logging(json_format=True)
logger = logging.getLogger(__name__)
tracing_manager.setup_tracing()

_STATIC_DIR = Path(__file__).parent / "static"
_DATA_DIR   = Path("/app/data/raw")          # populated in Docker image


def _load_startup_docs() -> list[dict]:
    """Load real docs from data/raw if available, otherwise fall back to samples."""
    if _DATA_DIR.exists():
        files = sorted(_DATA_DIR.glob("*.txt"))
        if files:
            logger.info("Loading %d docs from %s", len(files), _DATA_DIR)
            return [{"id": p.stem, "content": p.read_text("utf-8").strip()} for p in files]
    logger.warning("data/raw not found — using built-in sample docs")
    return [
        {"id": "ml-intro",  "content": "Machine learning enables systems to learn from data without explicit programming."},
        {"id": "ai-basics", "content": "Artificial intelligence encompasses machine learning, NLP, and computer vision."},
        {"id": "nlp-transformers", "content": "Transformers revolutionised NLP via self-attention; BERT and GPT are key examples."},
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG Service")
    metrics.start_server()

    if not rag_service.search_engine:
        docs = _load_startup_docs()
        try:
            embeddings = await asyncio.to_thread(
                rag_service.embedder.embed_batch,
                [d["content"] for d in docs],
            )
        except Exception:
            logger.exception("Embedding failed at startup; using zero vectors")
            embeddings = [[0.0] * 384 for _ in docs]
        rag_service.initialize_search(docs, embeddings)

    yield
    logger.info("Shutting down RAG Service")


app = FastAPI(
    title="RAG at Scale",
    description="Distributed RAG service with hybrid search, reranking, and observability",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the UI from /static and expose root as the main page
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    index = _STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global exception: %s", str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.service.app:app", host="0.0.0.0", port=8000, reload=True)
