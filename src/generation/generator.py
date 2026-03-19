"""Citation-enforced RAG generation pipeline using Groq."""

import re
import time
from dataclasses import dataclass, field

from groq import Groq

from src.config import settings
from src.generation.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    SOURCE_BLOCK_TEMPLATE,
    DECLINE_RESPONSE,
)
from src.retrieval.hybrid import HybridRetriever
from src.reranker.cross_encoder import ReRanker


@dataclass
class Citation:
    """A single citation reference."""
    source_index: int
    source_file: str
    section_heading: str
    text_excerpt: str


@dataclass
class GenerationResult:
    """Result from the RAG generation pipeline."""
    answer: str
    citations: list[Citation] = field(default_factory=list)
    is_declined: bool = False
    retrieved_chunks: list[dict] = field(default_factory=list)
    reranked_chunks: list[dict] = field(default_factory=list)
    latency: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


class RAGGenerator:
    """Full RAG pipeline: retrieve → re-rank → generate with citations."""

    INSUFFICIENT_EVIDENCE_MARKER = "INSUFFICIENT_EVIDENCE"

    def __init__(self):
        self.retriever = HybridRetriever()
        self.reranker = ReRanker()
        self.client = Groq(api_key=settings.groq_api_key)

    def _build_sources_block(self, chunks: list[dict]) -> str:
        """Build the sources block for the prompt."""
        blocks = []
        for i, chunk in enumerate(chunks, 1):
            blocks.append(SOURCE_BLOCK_TEMPLATE.format(
                index=i,
                source_file=chunk.get("source_file", "unknown"),
                section_heading=chunk.get("section_heading", "N/A"),
                text=chunk["text"],
            ))
        return "\n".join(blocks)

    def _extract_citations(
        self, answer: str, chunks: list[dict]
    ) -> list[Citation]:
        """Extract and validate citation references from the answer."""
        pattern = r"\[Source\s+(\d+)\]"
        cited_indices = set(int(m) for m in re.findall(pattern, answer))

        citations = []
        for idx in sorted(cited_indices):
            if 1 <= idx <= len(chunks):
                chunk = chunks[idx - 1]
                citations.append(Citation(
                    source_index=idx,
                    source_file=chunk.get("source_file", "unknown"),
                    section_heading=chunk.get("section_heading", ""),
                    text_excerpt=chunk["text"][:200] + "..."
                    if len(chunk["text"]) > 200
                    else chunk["text"],
                ))

        return citations

    def _is_declined(self, answer: str) -> bool:
        """Check if the model declined to answer."""
        return self.INSUFFICIENT_EVIDENCE_MARKER in answer.upper()

    def generate(self, question: str) -> GenerationResult:
        """
        Run the full RAG pipeline for a question.

        Steps:
        1. Hybrid retrieval (BM25 + vector)
        2. Cross-encoder re-ranking
        3. Citation-enforced LLM generation via Groq
        4. Post-processing and validation
        """
        start_time = time.perf_counter()
        
        # Step 1: Hybrid retrieval
        retrieved = self.retriever.search(question)

        # Step 2: Re-rank
        reranked = self.reranker.rerank(question, retrieved)

        # If no relevant chunks survive re-ranking, decline
        if not reranked:
            return GenerationResult(
                answer=DECLINE_RESPONSE,
                is_declined=True,
                retrieved_chunks=retrieved,
                reranked_chunks=[],
                latency=time.perf_counter() - start_time,
            )

        # Step 3: Generate answer with citations via Groq
        sources_block = self._build_sources_block(reranked)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            sources_block=sources_block,
            question=question,
        )

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.max_generation_tokens,
            temperature=settings.temperature,
        )

        raw_answer = response.choices[0].message.content.strip()
        
        latency = time.perf_counter() - start_time
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cost = 0.0
        
        if hasattr(response, "usage") and response.usage:
            prompt_tokens = response.usage.prompt_tokens or 0
            completion_tokens = response.usage.completion_tokens or 0
            total_tokens = response.usage.total_tokens or 0
            # Cost calculation based on Groq Llama-3.3-70b-versatile
            # $0.59 per 1M input tokens, $0.79 per 1M output tokens
            cost = (prompt_tokens / 1_000_000) * 0.59 + (completion_tokens / 1_000_000) * 0.79

        # Step 4: Post-process
        if self._is_declined(raw_answer):
            return GenerationResult(
                answer=DECLINE_RESPONSE,
                is_declined=True,
                retrieved_chunks=retrieved,
                reranked_chunks=reranked,
                latency=latency,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
            )

        citations = self._extract_citations(raw_answer, reranked)

        return GenerationResult(
            answer=raw_answer,
            citations=citations,
            is_declined=False,
            retrieved_chunks=retrieved,
            reranked_chunks=reranked,
            latency=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )
