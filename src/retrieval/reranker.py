# Cross-encoder Reranking
from sentence_transformers import CrossEncoder
import torch
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None

    def load_model(self):
        """Load the cross-encoder model"""
        if self.model is None:
            self.model = CrossEncoder(self.model_name)
            if torch.cuda.is_available():
                self.model.model.to('cuda')
                logger.info("Reranker model moved to GPU")
        return self.model

    def rerank(self, query: str, documents: List[Dict],
               top_k: int = 5) -> List[Dict]:
        """
        Rerank documents based on query relevance

        Args:
            query: Search query
            documents: List of document dicts with 'content' and other fields
            top_k: Number of top results to return

        Returns:
            Reranked documents with relevance scores
        """
        model = self.load_model()

        # Prepare input pairs
        query_doc_pairs = [[query, doc['content']] for doc in documents]

        # Get relevance scores
        scores = model.predict(query_doc_pairs)

        # Add scores to documents
        for i, doc in enumerate(documents):
            doc['rerank_score'] = float(scores[i])

        # Sort by rerank score
        reranked = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

        logger.info(f"Reranked {len(documents)} documents, returning top {top_k}")

        return reranked[:top_k]

    def rerank_with_threshold(self, query: str, documents: List[Dict],
                             threshold: float = 0.5) -> List[Dict]:
        """Rerank and filter by threshold"""
        reranked = self.rerank(query, documents, top_k=len(documents))

        # Filter by threshold
        filtered = [doc for doc in reranked if doc['rerank_score'] >= threshold]

        logger.info(f"Filtered to {len(filtered)} documents above threshold {threshold}")

        return filtered
