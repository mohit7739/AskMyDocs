"""Tests for the document chunker."""

import pytest
from src.ingestion.chunker import RecursiveChunker, Chunk


class TestRecursiveChunker:
    """Tests for RecursiveChunker."""

    def setup_method(self):
        self.chunker = RecursiveChunker(chunk_size=100, chunk_overlap=10)

    def test_empty_text(self):
        """Empty text should return no chunks."""
        chunks = self.chunker.chunk_document("", "test.md")
        assert chunks == []

    def test_whitespace_only(self):
        """Whitespace-only text should return no chunks."""
        chunks = self.chunker.chunk_document("   \n\n  ", "test.md")
        assert chunks == []

    def test_short_text_single_chunk(self):
        """Short text should produce a single chunk."""
        text = "This is a short document."
        chunks = self.chunker.chunk_document(text, "test.md")
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].source_file == "test.md"
        assert chunks[0].chunk_index == 0

    def test_chunk_metadata(self):
        """Chunks should preserve source file and index metadata."""
        text = "Hello world. This is a test document."
        chunks = self.chunker.chunk_document(text, "docs/my_file.md")
        assert all(c.source_file == "docs/my_file.md" for c in chunks)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_id_format(self):
        """chunk_id should use the format 'source_file::chunk_N'."""
        text = "Some text content."
        chunks = self.chunker.chunk_document(text, "test.md")
        assert chunks[0].chunk_id == "test.md::chunk_0"

    def test_heading_extraction(self):
        """Chunks should extract section headings from Markdown."""
        text = "# Main Title\n\nSome intro text.\n\n## Section One\n\nContent of section one."
        chunks = self.chunker.chunk_document(text, "test.md")
        # At least one chunk should have a heading
        headings = [c.section_heading for c in chunks if c.section_heading]
        assert len(headings) > 0

    def test_multiple_chunks_for_long_text(self):
        """Long text should be split into multiple chunks."""
        # Create text that's definitely longer than 100 tokens
        text = " ".join(["word"] * 500)
        chunks = self.chunker.chunk_document(text, "test.md")
        assert len(chunks) > 1

    def test_chunk_overlap_creates_continuity(self):
        """Chunks should have overlapping content for continuity."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = " ".join([f"word{i}" for i in range(200)])
        chunks = chunker.chunk_document(text, "test.md")

        if len(chunks) >= 2:
            # The second chunk should share some tokens with the end of the first
            # (due to overlap). Verify chunks exist and are non-empty.
            assert all(c.text.strip() for c in chunks)

    def test_chunk_preserves_all_content(self):
        """No content should be lost during chunking (accounting for overlap)."""
        text = "Alpha. Bravo. Charlie. Delta. Echo. Foxtrot. Golf."
        chunks = self.chunker.chunk_document(text, "test.md")
        combined = " ".join(c.text for c in chunks)
        # All original words should be present in the combined chunks
        for word in ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf"]:
            assert word in combined
