"""Cross-encoder re-ranker for precision improvement."""

import requests

from src.config import settings


class ReRanker:
    """Re-ranks retrieved chunks using a cross-encoder via HuggingFace API for
    low-memory environments."""

    def __init__(self):
        self.top_n = settings.reranker_top_n
        self.threshold = settings.relevance_threshold
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{settings.reranker_model}"
        self.headers = {"Authorization": f"Bearer {settings.hf_token}"} if settings.hf_token else {}

    def _get_scores(self, pairs: list[dict]) -> list[float]:
        """Get scores from HF API."""
        try:
            payload = {"inputs": pairs, "parameters": {"truncation": True}}
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            if response.status_code == 200:
                results = response.json()
                # HF API returns [[{"label": "LABEL_0", "score": 0.9}, {"score": 0.5}]]
                if isinstance(results, list) and len(results) == 1 and isinstance(results[0], list):
                    return [r["score"] if isinstance(r, dict) else r for r in results[0]]
                # Or [{"label": "LABEL_0", "score": 0.9}, ...]
                elif results and isinstance(results[0], dict) and "score" in results[0]:
                    return [r["score"] for r in results]
                return results
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            raise Exception(f"Re-ranking API failed: {str(e)}")

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """
        Re-score query-chunk pairs using the cross-encoder and return
        the top-N chunks above the relevance threshold.

        Args:
            query: The user's question.
            chunks: List of chunk dicts from hybrid retrieval.

        Returns:
            Re-ranked list of chunk dicts with added 'rerank_score' key.
            Sorted by descending cross-encoder score.
        """
        if not chunks:
            return []

        # Prepare query-document pairs
        pairs = [{"text": query, "text_pair": chunk["text"]} for chunk in chunks]

        # Score all pairs
        scores = self._get_scores(pairs)

        # Attach scores and filter by threshold
        scored_chunks = []
        for chunk, score in zip(chunks, scores):
            rerank_score = float(score)
            if rerank_score >= self.threshold:
                entry = chunk.copy()
                entry["rerank_score"] = rerank_score
                scored_chunks.append(entry)

        # Sort by descending score and take top-N
        scored_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_chunks[: self.top_n]
