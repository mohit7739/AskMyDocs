"""Tests for the cross-encoder re-ranker."""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestReRanker:
    """Tests for ReRanker with mocked cross-encoder model."""

    def _make_chunks(self, n: int) -> list[dict]:
        """Helper to create n mock chunks."""
        return [
            {
                "chunk_id": f"doc{i}.md::chunk_0",
                "text": f"Content of chunk {i}",
                "source_file": f"doc{i}.md",
                "section_heading": f"Section {i}",
                "rrf_score": 0.1 * (n - i),
            }
            for i in range(n)
        ]

    @patch("src.reranker.cross_encoder.CrossEncoder")
    def test_rerank_returns_top_n(self, MockCrossEncoder):
        """Re-ranker should return at most top_n results."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
        MockCrossEncoder.return_value = mock_model

        from src.reranker.cross_encoder import ReRanker
        reranker = ReRanker()
        reranker.model = mock_model
        reranker.top_n = 3
        reranker.threshold = 0.0

        chunks = self._make_chunks(7)
        results = reranker.rerank("test query", chunks)

        assert len(results) <= 3

    @patch("src.reranker.cross_encoder.CrossEncoder")
    def test_rerank_filters_by_threshold(self, MockCrossEncoder):
        """Chunks below the relevance threshold should be filtered out."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.9, 0.1, 0.05])
        MockCrossEncoder.return_value = mock_model

        from src.reranker.cross_encoder import ReRanker
        reranker = ReRanker()
        reranker.model = mock_model
        reranker.top_n = 10
        reranker.threshold = 0.3

        chunks = self._make_chunks(3)
        results = reranker.rerank("test query", chunks)

        # Only the first chunk (score 0.9) is above 0.3 threshold
        assert len(results) == 1
        assert results[0]["rerank_score"] == 0.9

    @patch("src.reranker.cross_encoder.CrossEncoder")
    def test_rerank_sorted_by_score(self, MockCrossEncoder):
        """Results should be sorted by descending rerank_score."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.3, 0.9, 0.6])
        MockCrossEncoder.return_value = mock_model

        from src.reranker.cross_encoder import ReRanker
        reranker = ReRanker()
        reranker.model = mock_model
        reranker.top_n = 10
        reranker.threshold = 0.0

        chunks = self._make_chunks(3)
        results = reranker.rerank("test query", chunks)

        scores = [r["rerank_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @patch("src.reranker.cross_encoder.CrossEncoder")
    def test_rerank_empty_chunks(self, MockCrossEncoder):
        """Empty chunk list should return empty results."""
        mock_model = MagicMock()
        MockCrossEncoder.return_value = mock_model

        from src.reranker.cross_encoder import ReRanker
        reranker = ReRanker()
        reranker.model = mock_model

        results = reranker.rerank("test query", [])
        assert results == []

    @patch("src.reranker.cross_encoder.CrossEncoder")
    def test_rerank_adds_score_key(self, MockCrossEncoder):
        """Results should have 'rerank_score' key added."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.8])
        MockCrossEncoder.return_value = mock_model

        from src.reranker.cross_encoder import ReRanker
        reranker = ReRanker()
        reranker.model = mock_model
        reranker.top_n = 5
        reranker.threshold = 0.0

        chunks = self._make_chunks(1)
        results = reranker.rerank("test query", chunks)

        assert "rerank_score" in results[0]
        assert results[0]["rerank_score"] == 0.8
