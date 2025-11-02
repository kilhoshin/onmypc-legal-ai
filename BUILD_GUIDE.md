# OnMyPC Legal AI – Build Guide

Use this guide when preparing a portable desktop release.

## Prerequisites

- Python 3.10+ (Conda recommended for packaging)
- Node.js 18+
- Git (optional)

All commands below assume the repository root as the working directory.

## 1. Prepare the Backend Environment

```bash
conda create -n legalai python=3.10          # optional but recommended
conda activate legalai                       # or source your virtualenv
pip install -r requirements.txt
```

Generate an `.env` if you need custom defaults:

```bash
cp .env.example .env
# Edit values as needed
```

## 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## 3. Bundle the Python Runtime

Electron ships with Node, but the backend needs Python. Package your environment into `portable/python/` so end users do not need their own interpreter.

```bash
python scripts/prepare_portable_env.py --env legalai
```

- Run this script whenever you change Python dependencies.
- The script copies site-packages, interpreter binaries, and prunes unused Conda metadata.

## 4. Build the Desktop Application

```bash
cd frontend
npm run build
```

Under the hood this runs:

1. `vite build` → writes static assets to `frontend/build/`
2. `electron-builder --win portable` (and other targets if available) → produces artifacts in `frontend/dist/`

### Output Highlights

- `frontend/dist/OnMyPC Legal AI Portable.exe`
- `frontend/dist/win-unpacked/` (folder you can zip directly)
- `frontend/dist/*.dmg` / `*.AppImage` if macOS/Linux tooling is installed

## 5. Smoke-Test the Build

Before shipping:

1. Run the unpacked app (`frontend/dist/win-unpacked/OnMyPC Legal AI.exe`).
2. Confirm the Python backend launches (terminal logs show “Application startup complete”).
3. Accept the EULA, select a test folder, and verify search results appear.

For automated checks you can also execute:

```bash
python test_new_architecture.py     # Parser → indexer → query smoke test
python test_api.py                  # Calls /api/query with a sample prompt
```

## 6. Package for Distribution

1. Zip the `win-unpacked/` directory (or platform equivalent).
2. Share the archive with users or upload to GitHub Releases.
3. Provide release notes that mention:
   - Supported OS
   - Minimum RAM/CPU
   - Instructions to place documents and start indexing

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Backend cannot find Python | Re-run `scripts/prepare_portable_env.py` and rebuild. |
| Electron build fails | `rm -rf node_modules package-lock.json` then `npm install` and retry. |
| App opens but shows blank screen | Backend likely failed. Run the unpacked app from a terminal to view logs. |
| Indexing never starts | Ensure the chosen folder contains supported file types and that `data/` is writable. |

## Useful Commands

```bash
# Clean previous build outputs
rm -rf frontend/build frontend/dist portable/python

# Rebuild everything from scratch
python scripts/prepare_portable_env.py --env legalai
cd frontend
npm run build
```

You now have a repeatable process for creating a self-contained release.
