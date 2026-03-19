"""Cross-encoder re-ranker for precision improvement."""

from sentence_transformers import CrossEncoder

from src.config import settings


class ReRanker:
    """Re-ranks retrieved chunks using a cross-encoder model for
    improved precision."""

    def __init__(self):
        self.model = CrossEncoder(
            settings.reranker_model,
            max_length=512,
        )
        self.top_n = settings.reranker_top_n
        self.threshold = settings.relevance_threshold

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
        pairs = [(query, chunk["text"]) for chunk in chunks]

        # Score all pairs
        scores = self.model.predict(pairs)

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
