"""Citation-enforced RAG generation pipeline using Groq."""

import re
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

        # Step 4: Post-process
        if self._is_declined(raw_answer):
            return GenerationResult(
                answer=DECLINE_RESPONSE,
                is_declined=True,
                retrieved_chunks=retrieved,
                reranked_chunks=reranked,
            )

        citations = self._extract_citations(raw_answer, reranked)

        return GenerationResult(
            answer=raw_answer,
            citations=citations,
            is_declined=False,
            retrieved_chunks=retrieved,
            reranked_chunks=reranked,
        )
