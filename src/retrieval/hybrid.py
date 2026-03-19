"""Hybrid retrieval combining BM25 and vector search with RRF fusion."""

from src.config import settings
from src.retrieval.bm25_engine import BM25Engine
from src.retrieval.vector_engine import VectorEngine


class HybridRetriever:
    """Combines BM25 keyword search and vector semantic search using
    Reciprocal Rank Fusion (RRF)."""

    def __init__(self):
        self.bm25 = BM25Engine()
        self.vector = VectorEngine()

    @staticmethod
    def _reciprocal_rank_fusion(
        result_lists: list[list[dict]],
        k: int = 60,
    ) -> list[dict]:
        """
        Merge multiple ranked result lists using Reciprocal Rank Fusion.

        RRF score = Σ 1 / (k + rank_i) for each result list.
        """
        fused_scores: dict[str, float] = {}
        chunk_map: dict[str, dict] = {}

        for results in result_lists:
            for rank, result in enumerate(results):
                chunk_id = result["chunk_id"]
                fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + (
                    1.0 / (k + rank + 1)
                )
                # Keep the chunk data from the first occurrence
                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = result

        # Sort by fused score descending
        sorted_ids = sorted(
            fused_scores.keys(),
            key=lambda cid: fused_scores[cid],
            reverse=True,
        )

        fused_results = []
        for chunk_id in sorted_ids:
            entry = chunk_map[chunk_id].copy()
            entry["rrf_score"] = fused_scores[chunk_id]
            fused_results.append(entry)

        return fused_results

    def search(self, query: str) -> list[dict]:
        """
        Run hybrid retrieval: BM25 + vector search → RRF fusion.

        Returns a unified ranked list of chunks sorted by RRF score.
        """
        bm25_results = self.bm25.search(query, top_k=settings.bm25_top_k)
        vector_results = self.vector.search(query, top_k=settings.vector_top_k)

        fused = self._reciprocal_rank_fusion(
            [bm25_results, vector_results],
            k=settings.rrf_k,
        )

        return fused
