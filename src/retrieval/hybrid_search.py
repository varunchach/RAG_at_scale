# Hybrid Search Implementation (Dense + Sparse/BM25)
import numpy as np
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger(__name__)

class HybridSearch:
    def __init__(self):
        # Legacy placeholders retained so older tests/docs still import cleanly.
        self.vector_client = None
        self.es_client = None
        self.bm25 = None
        self.corpus: List[str] = []
        self.doc_ids: List[str] = []
        # Normalised embeddings matrix — shape (N, D), float32
        self._embeddings: np.ndarray | None = None

    # ------------------------------------------------------------------ #
    # Indexing                                                              #
    # ------------------------------------------------------------------ #

    def index_documents(self, documents: List[Dict], embeddings: List[List[float]]):
        """Index documents for hybrid search (dense + BM25 sparse)."""
        self.corpus = [doc["content"] for doc in documents]
        self.doc_ids = [doc["id"] for doc in documents]

        # --- Dense index: pre-normalise for fast cosine via dot-product ---
        if embeddings and len(embeddings[0]) > 0:
            mat = np.array(embeddings, dtype=np.float32)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            self._embeddings = mat / np.maximum(norms, 1e-10)
            logger.info("Dense index built (%d vectors, dim=%d)", len(embeddings), mat.shape[1])
        else:
            self._embeddings = None
            logger.warning("No valid embeddings supplied — dense search disabled")

        # --- Sparse index ---
        tokenised = [doc.split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenised)

        logger.info("Indexed %d documents (dense=%s, sparse=✓)",
                    len(documents), self._embeddings is not None)

    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]):
        """Append new documents to an already-initialised index."""
        if not documents:
            return
        self.corpus.extend(doc["content"] for doc in documents)
        self.doc_ids.extend(doc["id"] for doc in documents)

        if embeddings and len(embeddings[0]) > 0:
            new_mat = np.array(embeddings, dtype=np.float32)
            norms = np.linalg.norm(new_mat, axis=1, keepdims=True)
            new_norm = new_mat / np.maximum(norms, 1e-10)
            self._embeddings = (
                np.vstack([self._embeddings, new_norm])
                if self._embeddings is not None else new_norm
            )

        tokenised = [doc.split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenised)
        logger.info("Added %d docs. Total index size: %d", len(documents), len(self.corpus))

    # ------------------------------------------------------------------ #
    # Search                                                               #
    # ------------------------------------------------------------------ #

    def search(self, query: str, query_embedding: List[float],
               top_k: int = 10, alpha: float = 0.5) -> List[Dict]:
        """
        Hybrid search combining dense + BM25 scores.

        alpha=1.0 → pure dense  |  alpha=0.0 → pure sparse
        Scores are normalised to [0, 1] before fusion so they are comparable.
        """
        dense_results = self._dense_search(query_embedding, top_k * 2)
        sparse_results = self._sparse_search(query, top_k * 2)
        combined = self._fuse_results(dense_results, sparse_results, alpha)
        return combined[:top_k]

    def _dense_search(self, query_embedding: List[float], top_k: int) -> List[Tuple[str, float]]:
        """Cosine similarity via pre-normalised dot-product (in-memory numpy)."""
        if self._embeddings is None:
            return []

        q = np.array(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(q)
        if norm < 1e-10:
            return []
        q = q / norm

        scores = self._embeddings @ q          # shape (N,)
        top_k = min(top_k, len(scores))
        top_idx = np.argpartition(scores, -top_k)[-top_k:]
        top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

        return [(self.doc_ids[i], float(scores[i])) for i in top_idx]

    def _sparse_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """BM25 keyword search."""
        if not self.bm25:
            return []

        scores = self.bm25.get_scores(query.split())
        top_k = min(top_k, len(scores))
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(self.doc_ids[i], float(scores[i])) for i in top_idx]

    @staticmethod
    def _normalise(results: List[Tuple[str, float]]) -> Dict[str, float]:
        """Min-max normalise scores to [0, 1]."""
        if not results:
            return {}
        scores = [s for _, s in results]
        lo, hi = min(scores), max(scores)
        span = hi - lo if hi > lo else 1.0
        return {doc_id: (score - lo) / span for doc_id, score in results}

    def _fuse_results(self, dense: List[Tuple[str, float]],
                      sparse: List[Tuple[str, float]], alpha: float) -> List[Dict]:
        """
        Weighted score fusion after per-list min-max normalisation.

        Teaching point: normalisation is critical — raw BM25 and cosine scores
        live on very different scales, so combining them without normalisation
        would always let one dominate.
        """
        dense_norm = self._normalise(dense)
        sparse_norm = self._normalise(sparse)

        all_ids = set(dense_norm) | set(sparse_norm)
        fused = {}
        for doc_id in all_ids:
            d_score = dense_norm.get(doc_id, 0.0)
            s_score = sparse_norm.get(doc_id, 0.0)
            fused[doc_id] = alpha * d_score + (1.0 - alpha) * s_score

        sorted_results = sorted(fused.items(), key=lambda x: x[1], reverse=True)
        return [{"doc_id": doc_id, "score": score} for doc_id, score in sorted_results]
