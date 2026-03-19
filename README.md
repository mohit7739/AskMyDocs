# AskMyDocs — Production-Grade RAG System

A domain-specific **"Ask My Docs"** system for technical documentation that retrieves information and answers questions with **proper citations**. Built with a production-grade pipeline featuring hybrid retrieval, cross-encoder re-ranking, and citation enforcement.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Hybrid Retrieval** | Combines BM25 keyword search with vector-based semantic search using Reciprocal Rank Fusion (RRF) |
| **Cross-Encoder Re-ranking** | Uses `ms-marco-MiniLM-L-6-v2` to re-score and filter results for precision |
| **Citation Enforcement** | Every claim is cited as `[Source N]`; system declines if evidence is insufficient |
| **Golden Evaluation** | 60 verified Q&A pairs with CI quality gates that break the build on regression |
| **Premium Web UI** | Dark-mode glassmorphism interface with interactive citation highlighting |

## 🏗️ Architecture

```
Query → [BM25 + Vector Search] → RRF Fusion → Cross-Encoder Re-rank → Citation-Enforced LLM → Answer + Citations
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /path/to/project
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Ingest Documents

```bash
python -c "from src.ingestion.pipeline import IngestionPipeline; p = IngestionPipeline(); print(p.run())"
```

Or use the API after starting the server.

### 4. Start the Server

```bash
uvicorn src.api.main:app --reload
```

Open **http://localhost:8000** to use the web UI.

## 📁 Project Structure

```
├── src/                    # Core application
│   ├── config.py           # Centralized settings
│   ├── ingestion/          # Document loading, chunking, embedding
│   ├── retrieval/          # BM25, vector, and hybrid search
│   ├── reranker/           # Cross-encoder re-ranking
│   ├── generation/         # Citation-enforced LLM generation
│   └── api/                # FastAPI endpoints
├── static/                 # Web UI (HTML/CSS/JS)
├── docs/                   # Knowledge base (FastAPI docs)
├── eval/                   # Evaluation pipeline
│   ├── golden_dataset.json # 60 verified Q&A pairs
│   ├── evaluator.py        # Metrics engine
│   └── test_quality_gates.py # CI quality assertions
├── tests/                  # Unit & integration tests
└── .github/workflows/      # CI pipeline
```

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Run quality gate evaluation (requires OPENAI_API_KEY)
python -m pytest eval/test_quality_gates.py -v
```

## 📊 Quality Thresholds

| Metric | Threshold |
|--------|-----------|
| Answer Relevance | ≥ 0.75 |
| Citation Precision | ≥ 0.70 |
| Citation Recall | ≥ 0.60 |
| Abstention Accuracy | ≥ 0.80 |

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Ask a question |
| `POST` | `/api/ingest` | Trigger document ingestion |
| `GET` | `/api/stats` | Index statistics |

## ⚙️ Tech Stack

- **Python 3.11+** / **FastAPI** / **Pydantic**
- **ChromaDB** (vector store) / **rank-bm25** (keyword search)
- **OpenAI** `text-embedding-3-small` + `gpt-4o-mini`
- **sentence-transformers** `ms-marco-MiniLM-L-6-v2` (re-ranker)
- **GitHub Actions** (CI/CD)
# AskMyDocs
