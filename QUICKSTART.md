# OnMyPC Legal AI – Quick Start

## End Users (Portable Build)

1. **Download** the latest portable release (`OnMyPC Legal AI Portable.exe`).
2. **Extract** the archive to a folder of your choice.
3. **Add documents** to a folder such as `C:\Users\<you>\Documents\LegalDocs` (PDF, DOCX, TXT).
4. **Launch** `OnMyPC Legal AI.exe`, accept the EULA, and point the app to your document folder.
5. **Index & search** once the progress bar completes.

No external services or internet connection are required.

## Developers

```bash
git clone https://github.com/your-org/onmypc_legal_ai.git
cd onmypc_legal_ai

# Backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### Run in Development Mode

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

The Electron shell connects to `http://127.0.0.1:8000` (backend) and the React dev server at `http://127.0.0.1:3000`.

### Package a Portable Build

```bash
python scripts/prepare_portable_env.py --env legalai  # once per dependency change
cd frontend
npm run build
```

Find installers and unpacked builds inside `frontend/dist/`.
