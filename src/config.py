"""Centralized configuration using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # --- Groq API (LLM generation) ---
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"

    # --- Local Embeddings (sentence-transformers, no API needed) ---
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    
    # --- HuggingFace API (Fallback for low RAM environments) ---
    hf_token: str = ""

    # --- Paths ---
    # Vercel's serverless environment requires writes to occur in /tmp
    chroma_persist_dir: str = "/tmp/chroma_data"
    docs_dir: str = "./docs"

    # --- Chunking ---
    chunk_size: int = 512
    chunk_overlap: int = 50

    # --- Retrieval ---
    bm25_top_k: int = 20
    vector_top_k: int = 20
    rrf_k: int = 60  # Reciprocal Rank Fusion constant

    # --- Re-ranker ---
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_top_n: int = 5
    relevance_threshold: float = 0.3

    # --- Generation ---
    max_generation_tokens: int = 1024
    temperature: float = 0.1

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    @property
    def docs_path(self) -> Path:
        return Path(self.docs_dir)


settings = Settings()
