# New Architecture Overview

This document captures the core pieces of the post-refactor system. It reiterates how the application moved from the original single-index pipeline to the richer knowledge representation now committed to the repository.

## Design Principles

- **Search-first** – prioritise precision/recall over generative summaries.
- **Metadata aware** – every document is parsed into a structured object with sections, parties, and jurisdiction tags.
- **Hybrid ranking** – combine BM25 keyword search with FAISS similarity and metadata boosts.
- **Hosted locally** – no third-party AI services, no Ollama, no external APIs.

## Key Modules

| Module | Responsibility |
| --- | --- |
| `backend/models/knowledge_schema.py` | Pydantic models for documents, enriched chunks, search queries, and results. |
| `backend/services/advanced_parser.py` | Parses PDF/DOCX/TXT, extracts sections, dates, parties, clause hints. |
| `backend/services/knowledge_indexer.py` | Coordinates parsing, chunking, BM25 corpus creation, FAISS vector indexing, and persistence. |
| `backend/services/hybrid_search.py` | Implements hybrid search (BM25 + vector + metadata boosts + optional reranker). |
| `backend/services/query_agent.py` | Lightweight rule-based query normalisation and filter extraction. |
| `backend/services/security.py` | EULA acceptance, disclaimer management, and audit logging helpers. |
| `backend/main.py` | FastAPI entrypoint, static asset hosting, and service wiring. |

## Data Lifecycle

1. **Document ingestion** – files enter the parser and come out as `StructuredDocument` objects.
2. **Chunk enrichment** – pages are chunked, tagged with section metadata, and embedded using `sentence-transformers`.
3. **Index persistence** – BM25 corpus, FAISS index, and structured document JSON are stored under `data/`.
4. **Query interpretation** – `QueryAgent` classifies intent, extracts filters, and builds a `SearchQuery`.
5. **Hybrid retrieval** – `HybridSearchEngine` fuses BM25 and vector scores, applies boosts, and returns ranked `SearchResult` objects.
6. **Audit logging** – `AuditLogger` writes indexing and query events to JSONL for compliance.

## Frontend/Electron Integration

- Electron launches the Python backend and forwards requests through `ipcMain` handlers.
- The React UI (Vite + axios) calls `/api/*` endpoints for status, indexing, folder management, and search.
- In production, the Electron bundle includes:
  - `resources/backend/` – backend source
  - `resources/python/` – portable Python runtime
  - `resources/web/` – prebuilt frontend assets served by FastAPI’s `StaticFiles`

## Migration Notes

- Legacy modules (`backend/services/indexing.py`, `search.py`, `embedding.py`, and `backend/models/document.py`) were removed.
- All documentation now reflects the self-contained pipeline—no Ollama, no PyInstaller executable workflow.
- Test utilities (`test_new_architecture.py`, `scripts/generate_sample_docs.py`) were updated to create sample corpora and exercise the new stack automatically.

The repository is now aligned around this architecture, making it ready for GitHub release and continued development.
