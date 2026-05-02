# API Endpoint Handlers
import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

from fastapi import HTTPException

try:
    from .models import (
        EmbeddingRequest,
        EmbeddingResponse,
        HealthResponse,
        IngestResponse,
        SearchRequest,
        SearchResponse,
        SearchResult,
    )
    from .ingest import pdf_to_chunks
    from ..embeddings.spark_embedder import SparkEmbedder
    from ..observability.logging_config import log_search_query
    from ..observability.metrics import metrics
    from ..retrieval.hybrid_search import HybridSearch
    from ..retrieval.reranker import Reranker
except ImportError:  # Notebook path when `src` is injected into sys.path
    from service.models import (
        EmbeddingRequest,
        EmbeddingResponse,
        HealthResponse,
        IngestResponse,
        SearchRequest,
        SearchResponse,
        SearchResult,
    )
    from service.ingest import pdf_to_chunks
    from embeddings.spark_embedder import SparkEmbedder
    from observability.logging_config import log_search_query
    from observability.metrics import metrics
    from retrieval.hybrid_search import HybridSearch
    from retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.search_engine: HybridSearch | None = None
        self.reranker = Reranker()
        self.embedder = SparkEmbedder()
        # doc_store maps doc ID → content so search results carry real text
        self._doc_store: Dict[str, str] = {}

    def initialize_search(self, documents: List[dict], embeddings: List[List[float]]):
        """Index documents for hybrid search and store content for retrieval."""
        self.search_engine = HybridSearch()
        self.search_engine.index_documents(documents, embeddings)
        # Build content lookup (id → content)
        self._doc_store = {doc["id"]: doc.get("content", "") for doc in documents}
        logger.info("Search engine initialised with %d documents", len(documents))
        metrics.index_size.set(len(documents))

    async def search(self, request: SearchRequest) -> SearchResponse:
        start_time = time.time()

        if not self.search_engine:
            raise HTTPException(status_code=500, detail="Search engine not initialised")

        try:
            query_embedding = self.embedder.embed_batch([request.query])[0]

            # Retrieve 2× candidates for reranking
            raw_results = self.search_engine.search(
                request.query,
                query_embedding,
                top_k=request.top_k * 2,
                alpha=getattr(request, "alpha", 0.6),
            )

            # Enrich with stored content
            results = [
                SearchResult(
                    doc_id=r["doc_id"],
                    content=self._doc_store.get(r["doc_id"], ""),
                    score=r["score"],
                )
                for r in raw_results
            ]

            rerank_time = None
            if request.rerank and results:
                rerank_start = time.time()
                docs_for_rerank = [
                    {"content": r.content, "doc_id": r.doc_id, "score": r.score}
                    for r in results
                ]
                reranked = self.reranker.rerank(request.query, docs_for_rerank, top_k=request.top_k)
                rerank_time = time.time() - rerank_start
                results = [
                    SearchResult(
                        doc_id=d["doc_id"],
                        content=d["content"],
                        score=d.get("score", 0.0),
                        rerank_score=d["rerank_score"],
                    )
                    for d in reranked
                ]
            else:
                results = results[: request.top_k]

            search_time = time.time() - start_time
            log_search_query(request.query, len(results), search_time)
            metrics.searches_performed.inc()

            answer = None
            answer_time = None
            if getattr(request, "generate", True) and results:
                ans_start = time.time()
                chunks_for_llm = [
                    {"doc_id": r.doc_id, "content": r.content} for r in results
                ]
                answer = await self._generate_answer(request.query, chunks_for_llm)
                answer_time = time.time() - ans_start

            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                rerank_time=rerank_time,
                answer=answer or None,
                answer_time=answer_time,
            )

        except Exception as e:
            logger.error("Search failed: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        start_time = time.time()
        try:
            embeddings = self.embedder.embed_batch(request.texts)
            processing_time = time.time() - start_time
            metrics.embeddings_generated.inc(len(request.texts))
            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model or self.embedder.model_name,
                processing_time=processing_time,
            )
        except Exception as e:
            logger.error("Embedding generation failed: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    async def _generate_answer(self, query: str, chunks: list[dict]) -> str:
        """Call Claude API to synthesise an answer from retrieved chunks."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return ""
        try:
            import anthropic
            context = "\n\n".join(
                f"[Chunk {i+1} — {c['doc_id']}]\n{c['content']}"
                for i, c in enumerate(chunks)
            )
            prompt = (
                f"You are a research assistant. Use ONLY the context below to answer the question. "
                f"If the answer is not in the context, say so clearly.\n\n"
                f"CONTEXT:\n{context}\n\n"
                f"QUESTION: {query}\n\n"
                f"ANSWER:"
            )
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.warning("LLM answer generation failed: %s", e)
            return ""

    async def ingest(self, filename: str, file_bytes: bytes) -> IngestResponse:
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=422, detail="Only PDF files are supported.")

        chunks = await asyncio.to_thread(pdf_to_chunks, file_bytes, filename)
        if not chunks:
            raise HTTPException(status_code=422, detail="No text could be extracted from this PDF.")

        embeddings = await asyncio.to_thread(
            self.embedder.embed_batch,
            [c["content"] for c in chunks],
        )

        if not self.search_engine:
            self.initialize_search(chunks, embeddings)
        else:
            self.search_engine.add_documents(chunks, embeddings)
            for c in chunks:
                self._doc_store[c["id"]] = c["content"]
            metrics.index_size.set(len(self._doc_store))

        logger.info("Ingested %d chunks from '%s'", len(chunks), filename)
        return IngestResponse(
            filename=filename,
            chunks_indexed=len(chunks),
            message=f"Indexed {len(chunks)} chunks from '{filename}'",
        )

    async def health_check(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services={
                "search_engine": "ready" if self.search_engine else "not_initialised",
                "embedder": "ready",
                "reranker": "ready",
                "doc_store": f"{len(self._doc_store)} docs indexed",
            },
        )


# Global service instance
rag_service = RAGService()
