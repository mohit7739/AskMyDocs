"""Tests for the RAG generator pipeline."""

import pytest
from src.generation.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    SOURCE_BLOCK_TEMPLATE,
    DECLINE_RESPONSE,
)
from src.generation.generator import RAGGenerator, GenerationResult, Citation


class TestPrompts:
    """Tests for prompt templates."""

    def test_system_prompt_contains_citation_rules(self):
        """System prompt must enforce citation rules."""
        assert "CITE" in SYSTEM_PROMPT or "cite" in SYSTEM_PROMPT.lower()
        assert "Source" in SYSTEM_PROMPT
        assert "INSUFFICIENT_EVIDENCE" in SYSTEM_PROMPT

    def test_user_prompt_template_has_placeholders(self):
        """User prompt template must have sources_block and question placeholders."""
        assert "{sources_block}" in USER_PROMPT_TEMPLATE
        assert "{question}" in USER_PROMPT_TEMPLATE

    def test_source_block_template_format(self):
        """Source block template must format correctly."""
        block = SOURCE_BLOCK_TEMPLATE.format(
            index=1,
            source_file="test.md",
            section_heading="Introduction",
            text="Test content here.",
        )
        assert "[Source 1]" in block
        assert "test.md" in block
        assert "Introduction" in block
        assert "Test content here." in block

    def test_decline_response_is_informative(self):
        """Decline response should be helpful and not empty."""
        assert len(DECLINE_RESPONSE) > 20
        assert "evidence" in DECLINE_RESPONSE.lower() or "documentation" in DECLINE_RESPONSE.lower()


class TestGeneratorHelpers:
    """Tests for generator helper methods (without API calls)."""

    def test_is_declined_positive(self):
        """Should detect INSUFFICIENT_EVIDENCE in answer."""
        gen = object.__new__(RAGGenerator)
        assert gen._is_declined("INSUFFICIENT_EVIDENCE")
        assert gen._is_declined("The answer is INSUFFICIENT_EVIDENCE here.")
        assert gen._is_declined("insufficient_evidence")

    def test_is_declined_negative(self):
        """Normal answers should not be detected as declined."""
        gen = object.__new__(RAGGenerator)
        assert not gen._is_declined("FastAPI is a web framework.")
        assert not gen._is_declined("You can install it with pip.")

    def test_extract_citations_basic(self):
        """Should extract [Source N] citations from answer text."""
        gen = object.__new__(RAGGenerator)
        chunks = [
            {"text": "Chunk 1 content here that is about FastAPI installation.", "source_file": "doc1.md", "section_heading": "Install"},
            {"text": "Chunk 2 content about path parameters.", "source_file": "doc2.md", "section_heading": "Paths"},
        ]
        answer = "FastAPI can be installed [Source 1] and supports path params [Source 2]."
        citations = gen._extract_citations(answer, chunks)

        assert len(citations) == 2
        assert citations[0].source_index == 1
        assert citations[0].source_file == "doc1.md"
        assert citations[1].source_index == 2
        assert citations[1].source_file == "doc2.md"

    def test_extract_citations_invalid_index(self):
        """Citations with invalid indices should be ignored."""
        gen = object.__new__(RAGGenerator)
        chunks = [{"text": "Only one chunk.", "source_file": "doc1.md", "section_heading": "S1"}]
        answer = "Some text [Source 1][Source 5]."
        citations = gen._extract_citations(answer, chunks)

        # Source 5 doesn't exist, should be filtered
        assert len(citations) == 1
        assert citations[0].source_index == 1

    def test_extract_citations_no_citations(self):
        """Answer with no citations should return empty list."""
        gen = object.__new__(RAGGenerator)
        chunks = [{"text": "Chunk.", "source_file": "doc.md", "section_heading": "S"}]
        answer = "A plain answer without any citations."
        citations = gen._extract_citations(answer, chunks)
        assert citations == []

    def test_extract_citations_duplicate_references(self):
        """Duplicate [Source N] references should be deduplicated."""
        gen = object.__new__(RAGGenerator)
        chunks = [{"text": "Chunk.", "source_file": "doc.md", "section_heading": "S"}]
        answer = "Text [Source 1] and more text [Source 1]."
        citations = gen._extract_citations(answer, chunks)
        assert len(citations) == 1

    def test_build_sources_block(self):
        """Sources block should format chunks correctly."""
        gen = object.__new__(RAGGenerator)
        chunks = [
            {"text": "Content A", "source_file": "a.md", "section_heading": "Section A"},
            {"text": "Content B", "source_file": "b.md", "section_heading": "Section B"},
        ]
        block = gen._build_sources_block(chunks)
        assert "[Source 1]" in block
        assert "[Source 2]" in block
        assert "a.md" in block
        assert "b.md" in block


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_default_values(self):
        """Default GenerationResult should have empty citations and not declined."""
        result = GenerationResult(answer="Test answer")
        assert result.citations == []
        assert result.is_declined is False
        assert result.retrieved_chunks == []
        assert result.reranked_chunks == []

    def test_declined_result(self):
        """Declined result should have is_declined=True."""
        result = GenerationResult(answer=DECLINE_RESPONSE, is_declined=True)
        assert result.is_declined is True
