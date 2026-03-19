"""Tests for the hybrid retrieval system."""

import pytest
from src.retrieval.hybrid import HybridRetriever


class TestReciprocalRankFusion:
    """Tests for the RRF fusion algorithm."""

    def test_single_result_list(self):
        """RRF with a single list should preserve order."""
        results = [
            [
                {"chunk_id": "a", "text": "text a", "score": 0.9},
                {"chunk_id": "b", "text": "text b", "score": 0.7},
            ]
        ]
        fused = HybridRetriever._reciprocal_rank_fusion(results, k=60)
        assert len(fused) == 2
        assert fused[0]["chunk_id"] == "a"
        assert fused[1]["chunk_id"] == "b"

    def test_two_lists_overlap(self):
        """Overlapping results should get higher RRF scores."""
        list1 = [
            {"chunk_id": "a", "text": "text a", "score": 0.9},
            {"chunk_id": "b", "text": "text b", "score": 0.7},
        ]
        list2 = [
            {"chunk_id": "b", "text": "text b", "score": 0.8},
            {"chunk_id": "c", "text": "text c", "score": 0.6},
        ]
        fused = HybridRetriever._reciprocal_rank_fusion([list1, list2], k=60)

        # 'b' appears in both lists so should have the highest RRF score
        assert fused[0]["chunk_id"] == "b"

    def test_rrf_scores_present(self):
        """Fused results should have rrf_score key."""
        results = [
            [{"chunk_id": "a", "text": "text", "score": 1.0}]
        ]
        fused = HybridRetriever._reciprocal_rank_fusion(results, k=60)
        assert "rrf_score" in fused[0]
        assert fused[0]["rrf_score"] > 0

    def test_empty_lists(self):
        """Empty result lists should produce empty fusion."""
        fused = HybridRetriever._reciprocal_rank_fusion([[], []], k=60)
        assert fused == []

    def test_disjoint_lists(self):
        """Disjoint lists should include all unique results."""
        list1 = [{"chunk_id": "a", "text": "a", "score": 0.9}]
        list2 = [{"chunk_id": "b", "text": "b", "score": 0.8}]
        fused = HybridRetriever._reciprocal_rank_fusion([list1, list2], k=60)
        ids = {r["chunk_id"] for r in fused}
        assert ids == {"a", "b"}

    def test_k_parameter_affects_scores(self):
        """Different k values should produce different scores."""
        results = [
            [
                {"chunk_id": "a", "text": "a", "score": 0.9},
                {"chunk_id": "b", "text": "b", "score": 0.7},
            ]
        ]
        fused_k1 = HybridRetriever._reciprocal_rank_fusion(results, k=1)
        fused_k60 = HybridRetriever._reciprocal_rank_fusion(results, k=60)

        # With k=1, score for rank 0 = 1/(1+1) = 0.5
        # With k=60, score for rank 0 = 1/(60+1) ≈ 0.0164
        assert fused_k1[0]["rrf_score"] > fused_k60[0]["rrf_score"]

    def test_three_lists_fusion(self):
        """RRF should handle three or more result lists."""
        list1 = [{"chunk_id": "a", "text": "a", "score": 1.0}]
        list2 = [{"chunk_id": "a", "text": "a", "score": 1.0}]
        list3 = [{"chunk_id": "b", "text": "b", "score": 0.5}]
        fused = HybridRetriever._reciprocal_rank_fusion([list1, list2, list3], k=60)

        # 'a' appears in two lists, 'b' in one — 'a' should rank first
        assert fused[0]["chunk_id"] == "a"
