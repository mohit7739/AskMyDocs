"""Tests for the BM25 search engine."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.retrieval.bm25_engine import BM25Engine


@pytest.fixture
def sample_corpus(tmp_path):
    """Create a temporary BM25 corpus file."""
    corpus = [
        {
            "chunk_id": "doc1.md::chunk_0",
            "text": "FastAPI is a modern web framework for building APIs with Python.",
            "source_file": "doc1.md",
            "chunk_index": 0,
            "section_heading": "Introduction",
        },
        {
            "chunk_id": "doc1.md::chunk_1",
            "text": "You can install FastAPI using pip install fastapi.",
            "source_file": "doc1.md",
            "chunk_index": 1,
            "section_heading": "Installation",
        },
        {
            "chunk_id": "doc2.md::chunk_0",
            "text": "Path parameters are declared using curly braces in the URL path.",
            "source_file": "doc2.md",
            "chunk_index": 0,
            "section_heading": "Path Parameters",
        },
        {
            "chunk_id": "doc3.md::chunk_0",
            "text": "Query parameters are function parameters not in the path.",
            "source_file": "doc3.md",
            "chunk_index": 0,
            "section_heading": "Query Parameters",
        },
    ]

    corpus_path = tmp_path / "bm25_corpus.json"
    corpus_path.write_text(json.dumps(corpus))
    return tmp_path


class TestBM25Engine:
    """Tests for BM25Engine."""

    def test_tokenize(self):
        """Tokenization should lowercase and split by whitespace."""
        tokens = BM25Engine._tokenize("Hello World FastAPI")
        assert tokens == ["hello", "world", "fastapi"]

    def test_tokenize_empty(self):
        """Empty string should return empty list."""
        tokens = BM25Engine._tokenize("")
        assert tokens == []

    def test_search_returns_relevant_results(self, sample_corpus):
        """Search should return results relevant to the query."""
        engine = BM25Engine()
        with patch.object(
            type(engine), "load_corpus",
            lambda self: self._load_from_path(sample_corpus)
        ):
            engine.corpus_data = json.loads(
                (sample_corpus / "bm25_corpus.json").read_text()
            )
            engine._tokenized_corpus = [
                BM25Engine._tokenize(item["text"])
                for item in engine.corpus_data
            ]
            from rank_bm25 import BM25Okapi
            engine.bm25 = BM25Okapi(engine._tokenized_corpus)

            results = engine.search("install FastAPI", top_k=2)

            assert len(results) > 0
            # The installation chunk should rank high
            source_files = [r["source_file"] for r in results]
            assert any("doc1" in sf for sf in source_files)

    def test_search_result_format(self, sample_corpus):
        """Results should have the expected keys."""
        engine = BM25Engine()
        engine.corpus_data = json.loads(
            (sample_corpus / "bm25_corpus.json").read_text()
        )
        engine._tokenized_corpus = [
            BM25Engine._tokenize(item["text"])
            for item in engine.corpus_data
        ]
        from rank_bm25 import BM25Okapi
        engine.bm25 = BM25Okapi(engine._tokenized_corpus)

        results = engine.search("FastAPI", top_k=1)
        if results:
            r = results[0]
            assert "chunk_id" in r
            assert "text" in r
            assert "source_file" in r
            assert "score" in r
            assert r["score"] > 0

    def test_search_no_match(self, sample_corpus):
        """Query with no matching terms should return empty or low-score results."""
        engine = BM25Engine()
        engine.corpus_data = json.loads(
            (sample_corpus / "bm25_corpus.json").read_text()
        )
        engine._tokenized_corpus = [
            BM25Engine._tokenize(item["text"])
            for item in engine.corpus_data
        ]
        from rank_bm25 import BM25Okapi
        engine.bm25 = BM25Okapi(engine._tokenized_corpus)

        results = engine.search("xyzzyplugh", top_k=5)
        # No documents contain this made-up word, so all scores should be 0
        assert len(results) == 0
