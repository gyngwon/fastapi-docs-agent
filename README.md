cat > README.md << 'DOCEOF'
# FastAPI Docs Agent

A retrieval-augmented, tool-using assistant that answers questions about
[FastAPI](https://fastapi.tiangolo.com) by searching its official
documentation — and falls back to searching GitHub issues on the
`fastapi/fastapi` repo when the docs don't have the answer.

Built as a hands-on learning project to practice the core skills behind
production RAG systems: document chunking, embeddings, vector search,
grounded generation, and agentic tool use with Claude.

## Why this project

Enterprise knowledge search — "let people ask questions against a large,
evolving set of documents and get grounded, cited answers" — is one of the
most common applied-AI use cases in industry today (internal wikis,
customer support, developer docs). This project reproduces that pattern on
a real, sizable public documentation set (155 files / ~2,300 chunks) from
FastAPI, chosen because it's well-structured, code-heavy (a realistic
stress test for retrieval), and free of any data/privacy concerns.

## Architecture

There are two separate flows: one that builds the index (run once, or
whenever the docs change), and one that runs per question.

```mermaid
flowchart LR
    subgraph Ingestion["📥 Ingestion — run once"]
        direction TB
        A[FastAPI docs<br/>.md files] --> B[Chunker<br/>headers + sliding window]
        B --> C[Embedding model<br/>sentence-transformers]
        C --> D[(Chroma<br/>vector DB)]
    end

    subgraph Query["💬 Query — per question"]
        direction TB
        E[User question] --> F[Embed query]
        F --> G{Claude}
        G -->|search_docs| D
        G -->|search_github_issues| H[GitHub API]
        D -.-> G
        H -.-> G
        G --> I[Answer with citations]
    end

    classDef store fill:#4c8bf5,stroke:#1a56c4,color:#fff
    classDef brain fill:#f5a623,stroke:#b9770e,color:#fff
    class D store
    class G brain
```

Two answer modes are planned:

- **Plain RAG** — a fixed pipeline: retrieve top-k chunks, then one Claude
  call with that context as a source of truth.
- **Agentic RAG** — Claude is given both tools and decides for itself
  whether to search the docs, search GitHub, both, or neither.

## Project status

| Step | Status |
|---|---|
| Fetch FastAPI documentation (`data/raw_docs/`) | done |
| Header-aware markdown chunking (`src/chunking.py`) | done |
| Embeddings + vector store (`src/embeddings.py`, `src/ingest.py`, `src/retriever.py`) | in progress |
| Plain RAG answer generation (`src/rag.py`) | planned |
| Agentic RAG with tool use (`src/agent.py`) | planned |
| CLI + retrieval evaluation | planned |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then add your ANTHROPIC_API_KEY
```

## Project structure

```
src/
  chunking.py       header-aware markdown chunking
  embeddings.py     text -> vector (sentence-transformers)
  ingest.py         builds the vector index (run once)
  retriever.py      query-time vector search
data/
  raw_docs/         FastAPI documentation (from fastapi/fastapi, docs/en/docs)
  chroma_db/        vector index (generated, not committed)
tests/
```

## Data source

Documentation content: [fastapi/fastapi](https://github.com/fastapi/fastapi),
`docs/en/docs/`, used here for a non-commercial learning/portfolio project.
DOCEOF
