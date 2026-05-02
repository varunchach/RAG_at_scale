# Test Embedding Generation
import pytest
from src.embeddings.spark_embedder import SparkEmbedder

class TestSparkEmbedder:
    def test_initialization(self):
        embedder = SparkEmbedder()
        assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embedder.model is None

    def test_load_model(self):
        embedder = SparkEmbedder()
        model = embedder.load_model()
        assert model is not None

    def test_embed_batch(self):
        embedder = SparkEmbedder()
        texts = ["Hello world", "This is a test"]
        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384  # Default model dimension
        assert len(embeddings[1]) == 384
