# Test API Service
import pytest
from fastapi.testclient import TestClient
from src.service.app import app

client = TestClient(app)

class TestRAGService:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "RAG at Scale Service" in response.json()["message"]

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_search_endpoint(self):
        request_data = {
            "query": "machine learning",
            "top_k": 5
        }
        response = client.post("/search", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data
