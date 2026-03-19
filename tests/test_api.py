"""Integration tests for the FastAPI endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.generation.generator import GenerationResult, Citation


# We need to mock the RAG components before importing the app
@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    with patch("src.api.main.RAGGenerator") as MockGenerator:
        mock_gen = MagicMock()
        MockGenerator.return_value = mock_gen

        # Default mock response
        mock_gen.generate.return_value = GenerationResult(
            answer="FastAPI is a web framework [Source 1].",
            citations=[
                Citation(
                    source_index=1,
                    source_file="01_getting_started.md",
                    section_heading="Introduction",
                    text_excerpt="FastAPI is a modern web framework...",
                )
            ],
            is_declined=False,
            retrieved_chunks=[{"chunk_id": "c1"}, {"chunk_id": "c2"}],
            reranked_chunks=[{"chunk_id": "c1"}],
        )

        from src.api.main import app
        # Set the global generator
        import src.api.main as api_module
        api_module._generator = mock_gen

        yield TestClient(app), mock_gen


class TestHealthEndpoint:
    """Tests for /api/health."""

    def test_health_check(self, client):
        test_client, _ = client
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "AskMyDocs" in data["service"]


class TestQueryEndpoint:
    """Tests for POST /api/query."""

    def test_successful_query(self, client):
        test_client, mock_gen = client
        response = test_client.post(
            "/api/query",
            json={"question": "How do I install FastAPI?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert data["is_declined"] is False
        assert data["num_chunks_retrieved"] == 2
        assert data["num_chunks_reranked"] == 1

    def test_query_with_citations(self, client):
        test_client, _ = client
        response = test_client.post(
            "/api/query",
            json={"question": "What is FastAPI?"},
        )
        data = response.json()
        assert len(data["citations"]) == 1
        citation = data["citations"][0]
        assert citation["source_index"] == 1
        assert citation["source_file"] == "01_getting_started.md"

    def test_declined_query(self, client):
        test_client, mock_gen = client
        mock_gen.generate.return_value = GenerationResult(
            answer="I couldn't find sufficient evidence...",
            is_declined=True,
            retrieved_chunks=[],
            reranked_chunks=[],
        )
        response = test_client.post(
            "/api/query",
            json={"question": "What is the capital of France?"},
        )
        data = response.json()
        assert data["is_declined"] is True
        assert data["citations"] == []

    def test_query_validation_short_question(self, client):
        test_client, _ = client
        response = test_client.post(
            "/api/query",
            json={"question": "Hi"},
        )
        assert response.status_code == 422  # Validation error (min_length=3)

    def test_query_missing_question(self, client):
        test_client, _ = client
        response = test_client.post("/api/query", json={})
        assert response.status_code == 422


class TestStatsEndpoint:
    """Tests for GET /api/stats."""

    @patch("src.api.main.chromadb")
    def test_get_stats(self, mock_chromadb, client):
        test_client, _ = client
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        response = test_client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_chunks_indexed" in data
        assert "collection_name" in data
