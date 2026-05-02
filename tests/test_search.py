# Test Search Functionality
import pytest
from src.retrieval.hybrid_search import HybridSearch

class TestHybridSearch:
    def test_initialization(self):
        search = HybridSearch()
        assert search.vector_client is None
        assert search.es_client is None
        assert search.bm25 is None

    def test_sparse_search(self):
        search = HybridSearch()

        # Mock documents
        documents = [
            {"id": "1", "content": "machine learning is awesome"},
            {"id": "2", "content": "artificial intelligence and deep learning"},
            {"id": "3", "content": "natural language processing with transformers"}
        ]

        search.index_documents(documents, [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])

        # Test search
        results = search._sparse_search("machine learning", 5)
        assert len(results) > 0
        assert results[0][0] == "1"  # Should find document 1
