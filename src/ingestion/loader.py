"""Document loader for Markdown and text files."""

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class RawDocument:
    """A loaded document with text and metadata."""
    text: str
    source_file: str
    title: str
    metadata: dict


class DocumentLoader:
    """Loads documents from a directory, extracting text and metadata."""

    SUPPORTED_EXTENSIONS = {".md", ".txt", ".rst"}

    def __init__(self, docs_dir: str | Path):
        self.docs_dir = Path(docs_dir)

    def _extract_title(self, text: str, filename: str) -> str:
        """Extract title from Markdown heading or use filename."""
        match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return Path(filename).stem.replace("_", " ").replace("-", " ").title()

    def _extract_sections(self, text: str) -> list[str]:
        """Extract all section headings from a document."""
        return re.findall(r"^#{1,4}\s+(.+)$", text, re.MULTILINE)

    def load_file(self, filepath: Path) -> RawDocument | None:
        """Load a single file and return a RawDocument."""
        if filepath.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return None

        try:
            text = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return None

        if not text.strip():
            return None

        relative_path = str(filepath.relative_to(self.docs_dir))
        title = self._extract_title(text, filepath.name)
        sections = self._extract_sections(text)

        return RawDocument(
            text=text,
            source_file=relative_path,
            title=title,
            metadata={
                "filename": filepath.name,
                "title": title,
                "sections": sections,
                "char_count": len(text),
            },
        )

    def load_all(self) -> list[RawDocument]:
        """Load all supported documents from the docs directory."""
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"Docs directory not found: {self.docs_dir}")

        documents = []
        for filepath in sorted(self.docs_dir.rglob("*")):
            if filepath.is_file():
                doc = self.load_file(filepath)
                if doc:
                    documents.append(doc)

        return documents
