"""Document chunker with metadata preservation."""

from dataclasses import dataclass, field
import re
import tiktoken


@dataclass
class Chunk:
    """A single chunk of text with metadata."""
    text: str
    source_file: str
    chunk_index: int
    section_heading: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def chunk_id(self) -> str:
        return f"{self.source_file}::chunk_{self.chunk_index}"


class RecursiveChunker:
    """Splits documents into overlapping chunks by token count."""

    SEPARATORS = ["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " "]

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _token_len(self, text: str) -> int:
        return len(self._enc.encode(text, disallowed_special=()))

    def _extract_heading(self, text: str) -> str:
        """Extract the most recent Markdown heading from text."""
        headings = re.findall(r"^#{1,4}\s+(.+)$", text, re.MULTILINE)
        return headings[-1].strip() if headings else ""

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using a hierarchy of separators."""
        if not text or self._token_len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        sep = separators[0] if separators else " "
        remaining_seps = separators[1:] if len(separators) > 1 else []

        parts = text.split(sep)
        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part
            if self._token_len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if self._token_len(part) > self.chunk_size and remaining_seps:
                    sub_chunks = self._split_text(part, remaining_seps)
                    chunks.extend(sub_chunks)
                else:
                    current = part
                    continue
                current = ""

        if current.strip():
            chunks.append(current)

        return chunks

    def chunk_document(self, text: str, source_file: str) -> list[Chunk]:
        """Split a document into overlapping chunks with metadata."""
        raw_chunks = self._split_text(text, self.SEPARATORS)
        if not raw_chunks:
            return []

        chunks: list[Chunk] = []
        overlap_text = ""

        for i, raw in enumerate(raw_chunks):
            chunk_text = (overlap_text + " " + raw).strip() if overlap_text else raw

            heading = self._extract_heading(chunk_text) or (
                chunks[-1].section_heading if chunks else ""
            )

            chunks.append(Chunk(
                text=chunk_text,
                source_file=source_file,
                chunk_index=i,
                section_heading=heading,
            ))

            # Build overlap for next chunk
            tokens = self._enc.encode(raw, disallowed_special=())
            if len(tokens) > self.chunk_overlap:
                overlap_tokens = tokens[-self.chunk_overlap:]
                overlap_text = self._enc.decode(overlap_tokens)
            else:
                overlap_text = raw

        return chunks
