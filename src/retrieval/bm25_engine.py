"""BM25 keyword search engine."""

import json
from pathlib import Path

from rank_bm25 import BM25Okapi

from src.config import settings


class BM25Engine:
    """BM25-based keyword retrieval over the document corpus."""

    def __init__(self):
        self.corpus_data: list[dict] = []
        self.bm25: BM25Okapi | None = None
        self._tokenized_corpus: list[list[str]] = []

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lowercasing tokenization."""
        return text.lower().split()

    def load_corpus(self) -> None:
        """Load the BM25 corpus from the saved JSON file."""
        corpus_path = Path(settings.chroma_persist_dir) / "bm25_corpus.json"
        if not corpus_path.exists():
            raise FileNotFoundError(
                f"BM25 corpus not found at {corpus_path}. Run ingestion first."
            )

        self.corpus_data = json.loads(corpus_path.read_text(encoding="utf-8"))
        self._tokenized_corpus = [
            self._tokenize(item["text"]) for item in self.corpus_data
        ]
        self.bm25 = BM25Okapi(self._tokenized_corpus)

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Search the corpus using BM25.

        Returns list of dicts with keys: chunk_id, text, source_file,
        section_heading, score.
        """
        if self.bm25 is None:
            self.load_corpus()

        top_k = top_k or settings.bm25_top_k
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices sorted by descending score
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                item = self.corpus_data[idx]
                results.append({
                    "chunk_id": item["chunk_id"],
                    "text": item["text"],
                    "source_file": item["source_file"],
                    "section_heading": item.get("section_heading", ""),
                    "score": float(scores[idx]),
                })

        return results
