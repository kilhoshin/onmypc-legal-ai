# OnMyPC Legal AI – Project Overview

Fully local legal search and discovery delivered as a portable Electron desktop app.

## Product Pillars

- **Offline-first** – all analysis runs on the user's machine; no cloud calls.
- **Document aware** – PDFs, DOCX, and TXT files are parsed into structured knowledge.
- **Hybrid relevance** – BM25 keyword search fused with vector similarity and metadata boosts.
- **Operational guardrails** – license/EULA gate, configurable disclaimer, and audit logging.
- **One-click distribution** – Electron packaging plus a bundled Python runtime for zero-install delivery.

## Architecture Snapshot

```
┌──────────────────────────┐
│ Electron Shell           │
│  - launches Python       │
│  - handles native menus  │
└──────────┬───────────────┘
           │ IPC + HTTP
┌──────────▼───────────────┐
│ FastAPI Backend          │
│  routes.py               │ REST + background jobs
│  legal_ai_service.py     │ orchestrates indexing/query
│  knowledge_indexer.py    │ BM25 + FAISS + metadata store
│  hybrid_search.py        │ fusion & scoring
│  security.py             │ EULA + disclaimer logging
└──────────┬───────────────┘
           │ Local storage
┌──────────▼───────────────┐
│ Data Folder (`data/`)    │
│  structured_documents    │
│  FAISS index             │
│  audit logs              │
└──────────────────────────┘
```

The React renderer (built with Vite) talks to the backend via `/api/*` endpoints and is packaged into `resources/app.asar`.

## End-to-End Flow

1. **EULA gate** – users must accept the license before any indexing runs.
2. **Folder selection** – the Electron preload layer prompts for a directory.
3. **Parsing** – `LegalDocumentParser` extracts sections, metadata, and enriched chunks.
4. **Indexing** – `KnowledgeIndexer` writes structured JSON, BM25 corpus, and FAISS vectors.
5. **Search** – `HybridSearchEngine` executes BM25 + vector search, fuses scores, applies boosts, and (optionally) reranks.
6. **Audit logging** – `AuditLogger` stores indexing and query events for compliance review.

## Key Directories

```
backend/
├─ api/                     FastAPI routers + schemas
├─ services/                Domain logic (parser, indexer, search, security)
├─ models/                  Pydantic data contracts
├─ utils/logger.py          Structured logging + audit helper
└─ main.py                  Application entrypoint

frontend/
├─ electron/                Main process + preload bridge
├─ src/                     React components and API client
├─ package.json             Build scripts (Vite + electron-builder)
└─ vite.config.js           Configures dev server and build output

scripts/
├─ generate_sample_docs.py  Quick test corpus generator
└─ prepare_portable_env.py  Bundle Python runtime into portable/python/

portable/
└─ README.md                Notes for runtime packaging
```

## Build & Release Pipeline (at a glance)

1. `python scripts/prepare_portable_env.py --env legalai`
2. `npm install` (one-time) inside `frontend/`
3. `npm run build` → outputs to `frontend/dist/`
4. Distribute `frontend/dist/win-unpacked` (or platform equivalent) to end users

## Testing & Diagnostics

- `python test_new_architecture.py` – full parser→indexer→query smoke test (auto-generates sample data).
- `python test_api.py` – ping the `/api/query` endpoint with a sample request.
- Browser DevTools + backend logs provide end-to-end visibility during development.

This document reflects the streamlined “new architecture” codebase after removing legacy modules (e.g., the original `indexing.py`/`search.py` stack) and the defunct Ollama integration.
