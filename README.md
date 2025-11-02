# OnMyPC Legal AI

> **Local-first legal document search** — 100% offline, private, and optimized for in-house use.

OnMyPC Legal AI helps lawyers and legal teams explore large collections of local documents using natural-language search. Everything runs on your machine; no cloud services or external LLMs are required.

## Key Features

- **Fully local** – all processing and storage stay on your PC.
- **Hybrid search** – combines BM25 keyword search, vector embeddings, and reranking for high-quality results.
- **Flexible document support** – PDF, DOCX, and TXT files are parsed into structured chunks.
- **Operational safeguards** – EULA acceptance, configurable disclaimers, and detailed audit logs.
- **Desktop ready** – Electron shell with React UI for a smooth end-user experience.

## Architecture

- Electron desktop shell provides the packaged application.
- React frontend offers the search experience and status dashboards.
- FastAPI backend orchestrates parsing, indexing, and query handling.
- Search pipeline:
  - Document indexing (metadata + FAISS vectors)
  - Embeddings via sentence-transformers
  - BM25 keyword search plus vector fusion
  - Optional reranking step for higher precision
  - Local storage for indexes, audit logs, and configuration

## Prerequisites (Development)

1. **Python 3.10+**
   ```bash
   python --version
   ```
2. **Node.js 18+**
   ```bash
   node --version
   ```

For packaged Windows builds no additional runtime dependencies are required.

## Development Setup

1. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Run in development mode**
   ```bash
   # terminal 1
   cd backend
   python main.py

   # terminal 2
   cd frontend
   npm run dev
   ```
   The Electron shell will open automatically against the Vite dev server.

4. **Package the desktop app (optional)**
   ```bash
   cd frontend
   npm run build        # Builds Vite + Electron portable bundle
   ```
   Before running the build, package your Python environment once:
   ```bash
   python scripts/prepare_portable_env.py --env legalai
   ```
   Generated installers and portable builds are written to `frontend/dist/`.

## Using the App

1. Launch the desktop app and accept the EULA.
2. Choose the folder containing your legal documents and start indexing.
3. After indexing completes, enter natural-language queries such as:
   - “Find every termination clause mentioning 90 days notice”
   - “What does the non-compete clause say about California?”
   - “Show indemnification language between Acme Corp and Beta LLC”
4. Review ranked results with highlighted matches and document metadata.

## Configuration

Create a `.env` file (or copy `.env.example`) to override defaults such as:

| Variable        | Default                      | Description                              |
|-----------------|------------------------------|------------------------------------------|
| `DOCS_DIR`      | `~/Documents/LegalDocs`      | Default folder to index on first run     |
| `CHUNK_SIZE`    | `512`                        | Character length of chunks during parse  |
| `TOP_K_RESULTS` | `5`                          | Number of hits returned per query        |

Embedding and reranker models can also be adjusted through the same file if you wish to experiment with different sentence-transformer checkpoints.

## Troubleshooting

- **Indexing takes too long** — ensure large PDFs are not scanned images; OCR is not performed automatically.
- **No results returned** — confirm the target folder actually contains supported documents and rerun indexing.
- **Empty summaries** — summaries were removed in this build; focus is on high-quality search results. Use the highlighted snippets to review context.

## Project Structure

```
backend/    FastAPI application, services, and search pipeline
frontend/   React + Electron client
data/       Persisted indexes, vectors, and audit logs
```

## License

Internal project – consult your organization’s policies before redistribution.
