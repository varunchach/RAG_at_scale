# Test API Service
import pytest
from fastapi.testclient import TestClient
from src.service.app import app

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("src.service.app.metrics.start_server", lambda port=8001: None)
    with TestClient(app) as test_client:
        yield test_client

class TestRAGService:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "RAG at Scale" in response.text

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_search_endpoint(self, client):
        request_data = {
            "query": "machine learning",
            "top_k": 5,
            "rerank": False,
            "generate": False,
        }
        response = client.post("/search", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data

    def test_search_captures_shadow_eval_payload(self, client, monkeypatch):
        captured = {}

        def fake_schedule(payload):
            captured["payload"] = payload

        monkeypatch.setattr(
            "src.service.handlers.rag_service._schedule_post_response_observability",
            fake_schedule,
        )

        response = client.post(
            "/search",
            json={
                "query": "machine learning",
                "top_k": 3,
                "rerank": False,
                "generate": False,
            },
        )

        assert response.status_code == 200
        payload = captured["payload"]
        assert payload.request_id
        assert payload.route == "search"
        assert payload.query == "machine learning"
        assert payload.answer is None
        assert payload.retrieval_count >= 1
        assert payload.reranked_count >= 1

    def test_search_stays_healthy_when_observability_fails(self, client, monkeypatch):
        def boom(_payload):
            raise RuntimeError("shadow metrics unavailable")

        monkeypatch.setattr(
            "src.service.handlers.rag_service._schedule_post_response_observability",
            boom,
        )

        response = client.post(
            "/search",
            json={
                "query": "machine learning",
                "top_k": 3,
                "rerank": False,
                "generate": False,
            },
        )

        assert response.status_code == 200
        assert response.json()["query"] == "machine learning"
