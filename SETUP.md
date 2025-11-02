# OnMyPC Legal AI – Setup Guide

Clean-room instructions for getting the project running locally, packaging the desktop build, and shipping the portable bundle that includes Python.

## Prerequisites

- Python 3.10 or newer (`python --version`)
- Node.js 18 or newer (`node --version`)
- Git (optional, but recommended)
- Conda or another isolated Python environment manager (required for bundling the portable runtime)

## Development Setup

1. **Clone and enter the repository**
   ```bash
   git clone https://github.com/your-org/onmypc_legal_ai.git
   cd onmypc_legal_ai
   ```

2. **Create and activate a Python environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
   (If you prefer Conda, create an environment such as `conda create -n legalai python=3.10` and `conda activate legalai`.)

3. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env   # Optional: customise values inside .env
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Prepare sample documents (optional)**
   ```bash
   python scripts/generate_sample_docs.py --output ./data/sample_docs
   ```
   Alternatively, copy your own `.pdf`, `.docx`, or `.txt` files into a folder such as `~/Documents/LegalDocs`.

6. **Run in development mode**
   - Terminal A:
     ```bash
     cd backend
     python main.py
     ```
   - Terminal B:
     ```bash
     cd frontend
     npm run dev
     ```
   The Electron shell connects to the backend at `http://127.0.0.1:8000` and serves the Vite dev server UI on `http://127.0.0.1:3000`.

## Building a Portable Release

1. **Capture the Python runtime (first time only or after dependency changes)**
   ```bash
   python scripts/prepare_portable_env.py --env legalai
   ```
   Replace `legalai` with the name of your active Conda environment. The script copies the interpreter and installed packages into `portable/python/`.

2. **Build the Electron bundle**
   ```bash
   cd frontend
   npm run build
   ```
   This runs the Vite production build and `electron-builder` portable target. The output appears in `frontend/dist/`.

### Resulting Artifacts

- `frontend/dist/OnMyPC Legal AI Portable.exe` — Windows portable executable
- `frontend/dist/OnMyPC Legal AI.dmg` — macOS build (requires Apple tooling)
- `frontend/dist/OnMyPC Legal AI.AppImage` — Linux build (requires Linux target tooling)

### Bundle Layout

```
OnMyPC Legal AI/
├─ OnMyPC Legal AI.exe
└─ resources/
   ├─ app.asar        # React frontend
   ├─ backend/        # FastAPI source
   ├─ python/         # Self-contained runtime (from portable/)
   └─ web/            # Pre-built Vite assets
```

## Configuration Reference

Modify `.env` (or set environment variables) to override defaults:

```
# Server
HOST=127.0.0.1
PORT=8000

# Paths
DOCS_DIR=C:\Users\YourName\Documents\LegalDocs

# Models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANKER_MODEL=BAAI/bge-reranker-base

# Search behaviour
CHUNK_SIZE=512
TOP_K_RESULTS=5
```

## Deploying to End Users

1. Build the portable artifact.
2. Zip the entire `frontend/dist/win-unpacked` folder (or platform equivalent).
3. Share the archive. No system-wide installation is required.
4. End users extract, accept the EULA, choose a documents folder, and index before searching.

### Minimum System Requirements

- Windows 10/11, macOS 12+, or a modern Linux distribution
- Quad-core CPU
- 8 GB RAM (16 GB recommended)
- 5 GB free disk space plus room for indexed documents

## Troubleshooting

- **Backend fails to start** — ensure Python dependencies are installed and port 8000 is free (`netstat -ano | findstr :8000` on Windows, `lsof -i :8000` on Unix).
- **Electron shows a blank window** — confirm the backend console shows “Application startup complete” and the `/api/status` endpoint returns JSON.
- **Indexer finds no documents** — verify supported file types exist in the selected folder and that the app has read permissions.
- **Corrupted index or stale data** — delete the `data/` directory and re-run indexing; the folders are recreated automatically.
- **Electron build errors** — from `frontend/` run `rm -rf node_modules package-lock.json`, then `npm install` and `npm run build`.

## Developer Tips

- Hot reload the backend with `uvicorn backend.main:app --reload`.
- Toggle Electron DevTools to inspect renderer logs (`View > Toggle Developer Tools`).
- Run the simple API smoke test: `python test_api.py`.
- Regenerate test documents quickly: `python scripts/generate_sample_docs.py --count 5`.

You now have a lean, fully local setup tuned for GitHub distribution and offline use. Happy shipping!
