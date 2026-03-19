"""Ingestion pipeline: load → chunk → embed → index."""

import hashlib
import json
from pathlib import Path

import chromadb

from src.config import settings
from src.ingestion.chunker import RecursiveChunker, Chunk
from src.ingestion.loader import DocumentLoader


class IngestionPipeline:
    """Orchestrates document ingestion into BM25 index and ChromaDB."""

    BM25_INDEX_FILE = "bm25_corpus.json"

    def __init__(self):
        self.loader = DocumentLoader(settings.docs_dir)
        self.chunker = RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        # HuggingFace API Setup
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{settings.embedding_model}"
        self.headers = {"Authorization": f"Bearer {settings.hf_token}"} if settings.hf_token else {}
        self.local_model = None

        # ChromaDB
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _get_indexed_hashes(self) -> set[str]:
        """Get the set of content hashes already indexed."""
        try:
            result = self.collection.get(include=["metadatas"])
            if result and result["metadatas"]:
                return {
                    m.get("content_hash", "")
                    for m in result["metadatas"]
                    if m
                }
        except Exception:
            pass
        return set()

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using HuggingFace API."""
        if not texts:
            return []
        
        import requests
        payload = {"inputs": texts, "parameters": {"truncation": True}}
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        
        raise Exception(f"HuggingFace API Error ({response.status_code}): {response.text}")

    def _save_bm25_corpus(self, chunks: list[Chunk]) -> None:
        """Save chunk texts and metadata for BM25 index reconstruction."""
        corpus_data = []
        for chunk in chunks:
            corpus_data.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source_file": chunk.source_file,
                "chunk_index": chunk.chunk_index,
                "section_heading": chunk.section_heading,
            })

        corpus_path = settings.chroma_path / self.BM25_INDEX_FILE
        corpus_path.parent.mkdir(parents=True, exist_ok=True)
        corpus_path.write_text(
            json.dumps(corpus_data, indent=2), encoding="utf-8"
        )

    def run(self) -> dict:
        """Run the full ingestion pipeline. Returns stats."""
        documents = self.loader.load_all()
        indexed_hashes = self._get_indexed_hashes()

        all_chunks: list[Chunk] = []
        new_chunks: list[Chunk] = []

        for doc in documents:
            doc_chunks = self.chunker.chunk_document(doc.text, doc.source_file)
            all_chunks.extend(doc_chunks)

            for chunk in doc_chunks:
                h = self._content_hash(chunk.text)
                if h not in indexed_hashes:
                    new_chunks.append(chunk)
                    indexed_hashes.add(h)

        # Embed and index new chunks into ChromaDB
        if new_chunks:
            batch_size = 100
            for i in range(0, len(new_chunks), batch_size):
                batch = new_chunks[i : i + batch_size]
                texts = [c.text for c in batch]
                embeddings = self._embed_texts(texts)

                self.collection.add(
                    ids=[c.chunk_id for c in batch],
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=[
                        {
                            "source_file": c.source_file,
                            "chunk_index": c.chunk_index,
                            "section_heading": c.section_heading,
                            "content_hash": self._content_hash(c.text),
                        }
                        for c in batch
                    ],
                )

        # Save corpus for BM25
        self._save_bm25_corpus(all_chunks)

        return {
            "documents_loaded": len(documents),
            "total_chunks": len(all_chunks),
            "new_chunks_indexed": len(new_chunks),
            "skipped_existing": len(all_chunks) - len(new_chunks),
        }
