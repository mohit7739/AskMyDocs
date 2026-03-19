"""Pydantic request/response models for the API."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for the /api/query endpoint."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The question to ask about the documents.",
        examples=["How do I define path parameters in FastAPI?"],
    )


class CitationResponse(BaseModel):
    """A single citation in the response."""
    source_index: int = Field(description="1-based source index")
    source_file: str = Field(description="Source document filename")
    section_heading: str = Field(description="Section heading of the source")
    text_excerpt: str = Field(description="Excerpt from the source text")


class QueryResponse(BaseModel):
    """Response body for the /api/query endpoint."""
    answer: str = Field(description="The generated answer with inline citations")
    citations: list[CitationResponse] = Field(
        default_factory=list,
        description="List of cited sources",
    )
    is_declined: bool = Field(
        default=False,
        description="Whether the system declined to answer",
    )
    num_chunks_retrieved: int = Field(
        default=0,
        description="Total chunks retrieved from hybrid search",
    )
    num_chunks_reranked: int = Field(
        default=0,
        description="Chunks surviving re-ranking",
    )


class IngestResponse(BaseModel):
    """Response body for the /api/ingest endpoint."""
    documents_loaded: int
    total_chunks: int
    new_chunks_indexed: int
    skipped_existing: int


class StatsResponse(BaseModel):
    """Response body for the /api/stats endpoint."""
    total_chunks_indexed: int
    collection_name: str
