FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY static/ ./static/
COPY docs/ ./docs/
COPY eval/ ./eval/
COPY tests/ ./tests/
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Pre-download ML models during build (faster cold starts)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Create data directories
RUN mkdir -p chroma_data

# Set PyTorch to CPU only and limit threads
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV PYTORCH_ENABLE_MPS_FALLBACK=1

# Expose port
EXPOSE 10000

# Start the FastAPI app with uvicorn (optimized for low memory)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1", "--timeout-keep-alive", "5"]
