# Resume Intelligence Agent 

A full-stack multi-agent RAG system that parses resumes, performs semantic search, finds matching jobs, and suggests improvements using LLMs.

## Features

- **Resume Parsing** — Extracts and chunks PDF resumes with section-aware splitting
- **Semantic Search** — Vector embeddings + cosine similarity search via Qdrant
- **RAG Pipeline** — Multiple query generation + cross-encoder reranking + Groq LLM
- **Job Finder Agent** — Finds real job listings matching your resume via Tavily
- **Resume Improver Agent** — Gap analysis + rewrite suggestions against job descriptions
- **Streaming** — Real-time LLM response streaming via SSE
- **Caching** — Redis caching for job search results with TTL
- **History** — PostgreSQL logging of uploads, searches, and Q&A sessions

## Tech Stack

### Backend
- **FastAPI** — REST API with streaming support
- **sentence-transformers** — Local embeddings (`all-MiniLM-L6-v2`)
- **Qdrant** — Vector database for semantic search
- **Groq** — LLM inference (Llama 3.3 70B)
- **Tavily** — Real-time job search
- **Redis** — Job search result caching
- **PostgreSQL + SQLAlchemy** — Structured data persistence
- **PyMuPDF** — PDF parsing

### Frontend
- **Next.js 15** — React framework
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling

## Architecture

```
PDF Upload
    ↓
Parser (PyMuPDF) → section-aware chunking
    ↓
Embedder (sentence-transformers) → 384-dim vectors
    ↓
Qdrant (vector storage)
    ↓
Query → Multiple query generation (Groq)
    ↓
Vector search + Cross-encoder reranking
    ↓
Groq LLM → streamed answer
```

## Project Structure

```
resume-agent/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── agents/       # Job finder + Resume improver
│   │   ├── core/         # Config, database, cache
│   │   ├── pipeline/     # Parser, chunker, embedder, store, reranker
│   │   └── models/       # Pydantic schemas
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/app/page.tsx  # Single page UI
└── docker-compose.yml    # Qdrant + Redis + Postgres
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create `.env` from `.env.example`:
```bash
cp .env.example .env
```

Fill in your API keys:
```
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
QDRANT_URL=your_qdrant_cloud_url        # or leave empty for local
QDRANT_API_KEY=your_qdrant_api_key
REDIS_URL=your_upstash_redis_url        # or leave empty for local
DATABASE_URL=postgresql://resume_agent:resume_agent@127.0.0.1:5433/resume_agent
```

Start Docker services:
```bash
docker compose up -d
```

Start backend:
```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/resume/upload` | Upload and process PDF resume |
| POST | `/resume/ask` | Ask questions about resume |
| GET | `/resume/ask/stream` | Streaming Q&A |
| POST | `/resume/find-jobs` | Find matching job listings |
| POST | `/resume/improve` | Gap analysis + suggestions |
| GET | `/resume/history` | View past activity |
| GET | `/resume/search` | Semantic chunk search |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM inference | Yes |
| `TAVILY_API_KEY` | Tavily API key for job search | Yes |
| `QDRANT_URL` | Qdrant Cloud URL (empty = local) | No |
| `QDRANT_API_KEY` | Qdrant Cloud API key | No |
| `REDIS_URL` | Upstash Redis URL (empty = local) | No |
| `DATABASE_URL` | PostgreSQL connection string | Yes |

## Key Engineering Concepts

- **RAG (Retrieval Augmented Generation)** — Grounding LLM answers in resume content
- **Vector embeddings** — Semantic similarity search beyond keyword matching
- **Cross-encoder reranking** — Two-stage retrieval for precision
- **Multiple query generation** — Casting wider retrieval net
- **SSE streaming** — Real-time token delivery to frontend
- **Redis TTL caching** — Avoiding redundant API calls
- **Parent document retrieval** — Balancing chunk size for retrieval vs generation
