"""Vector-based semantic search engine using ChromaDB + local embeddings."""

import chromadb
import requests

from src.config import settings

class VectorEngine:
    """Semantic search using ChromaDB with HuggingFace Inference API embeddings."""

    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{settings.embedding_model}"
        self.headers = {"Authorization": f"Bearer {settings.hf_token}"} if settings.hf_token else {}

    def _embed_query(self, query: str) -> list[float]:
        """Embed a single query string using HuggingFace API."""
        response = requests.post(self.api_url, headers=self.headers, json={"inputs": [query]})
        if response.status_code != 200:
             raise Exception(f"HuggingFace API Error ({response.status_code}): {response.text}")
        
        return response.json()[0]

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Search the vector store for semantically similar chunks.

        Returns list of dicts with keys: chunk_id, text, source_file,
        section_heading, score.
        """
        top_k = top_k or settings.vector_top_k
        query_embedding = self._embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        output = []
        for i, chunk_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            similarity = 1.0 - distance

            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            text = results["documents"][0][i] if results["documents"] else ""

            output.append({
                "chunk_id": chunk_id,
                "text": text,
                "source_file": metadata.get("source_file", ""),
                "section_heading": metadata.get("section_heading", ""),
                "score": float(similarity),
            })

        return output
