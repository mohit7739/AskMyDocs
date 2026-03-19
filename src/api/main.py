"""FastAPI application for the AskMyDocs RAG system."""

import logging
from contextlib import asynccontextmanager

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import settings
from src.api.models import (
    QueryRequest,
    QueryResponse,
    CitationResponse,
    IngestResponse,
    StatsResponse,
)
from src.generation.generator import RAGGenerator
from src.ingestion.pipeline import IngestionPipeline
from src.observability.tracer import global_tracer

logger = logging.getLogger(__name__)

# Global instances (initialized on startup)
_generator: RAGGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global _generator
    
    # Run ingestion automatically on startup for Vercel (ephemeral DB)
    try:
        logger.info("Starting automatic document ingestion...")
        pipeline = IngestionPipeline()
        stats = pipeline.run()
        logger.info(f"Ingestion complete: {stats}")
    except Exception as e:
        logger.warning(f"Auto-ingestion skipped or failed: {e}")

    _generator = RAGGenerator()
    logger.info("RAG Generator initialized.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AskMyDocs",
    description="Production-grade RAG system with hybrid retrieval, "
    "cross-encoder re-ranking, and citation enforcement.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AskMyDocs RAG"}


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Ask a question about the ingested documents.

    Returns an answer with citations, or a polite decline if
    insufficient evidence is found.
    """
    global _generator
    if _generator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = _generator.generate(request.question)
    except FileNotFoundError as e:
        global_tracer.log_trace(
            endpoint="/api/query",
            question=request.question,
            answer="", latency=0, is_error=True, error_msg=str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=f"No documents indexed yet. Run /api/ingest first. ({e})",
        )
    except Exception as e:
        global_tracer.log_trace(
            endpoint="/api/query",
            question=request.question,
            answer="", latency=0, is_error=True, error_msg=str(e)
        )
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    global_tracer.log_trace(
        endpoint="/api/query",
        question=request.question,
        answer=result.answer,
        latency=result.latency,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cost=result.cost,
        extra={"citations": len(result.citations)}
    )

    return QueryResponse(
        answer=result.answer,
        citations=[
            CitationResponse(
                source_index=c.source_index,
                source_file=c.source_file,
                section_heading=c.section_heading,
                text_excerpt=c.text_excerpt,
            )
            for c in result.citations
        ],
        is_declined=result.is_declined,
        num_chunks_retrieved=len(result.retrieved_chunks),
        num_chunks_reranked=len(result.reranked_chunks),
    )


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_documents():
    """
    Trigger document ingestion from the configured docs directory.

    Loads, chunks, embeds, and indexes all documents. Skips
    already-indexed content (incremental).
    """
    try:
        pipeline = IngestionPipeline()
        stats = pipeline.run()
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Ingestion failed: {str(e)}"
        )

    # Re-initialize generator to pick up new index
    global _generator
    _generator = RAGGenerator()

    return IngestResponse(**stats)


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get index statistics."""
    try:
        client = chromadb.Client()
        collection = client.get_or_create_collection("documents")
        count = collection.count()
    except Exception:
        count = 0

    return StatsResponse(
        total_chunks_indexed=count,
        collection_name="documents",
    )


@app.get("/api/traces")
async def get_traces(limit: int = 50):
    """View recent traces for observability."""
    import json
    traces = []
    if global_tracer.log_path.exists():
        try:
            with open(global_tracer.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        traces.append(json.loads(line))
        except Exception:
            pass
    return list(reversed(traces))  # newest first


# Serve static files (frontend) - Note: Vercel routes /static/ directly via vercel.json
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML page."""
    import os
    # When deployed to Vercel, the current working directory is the project root
    html_path = os.path.join(os.getcwd(), "static", "index.html")
    return FileResponse(html_path)
