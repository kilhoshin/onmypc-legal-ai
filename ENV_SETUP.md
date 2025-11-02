# Environment Setup Guide

Choose the workflow that matches your toolchain. All options end with the same portable build.

## Which path should I follow?

```
Using Conda?      → run build_conda.bat
Using plain Python? → run build.bat
Not sure?         → run `conda --version` first
```

### Quick check

```bash
conda --version
```

- If you see something like `conda 23.x.x`, Conda is available → use `build_conda.bat`.
- If you get "`conda` is not recognized...", use `build.bat`.

---

## Option 1 · Conda environment (recommended when Conda is installed)

### Fast path

```bash
build_conda.bat
```

### Manual steps

```bash
conda create -n legalai python=3.10 -y
conda activate legalai
pip install -r requirements.txt
cd frontend
npm install
npm run build
```

### Day-to-day development

```bash
conda activate legalai
cd backend
python main.py
```

### Tear down later

```bash
conda deactivate
conda env remove -n legalai
```

---

## Option 2 · Python venv (when Conda is unavailable)

### Fast path

```bash
build.bat
```

### Manual steps

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd frontend
npm install
npm run build
```

### Day-to-day development

```bash
venv\Scripts\activate
cd backend
python main.py
```

### Tear down later

```bash
rmdir /s venv
```

---

## Option 3 · System Python only (not recommended)

### Why it is discouraged

- High chance of clashes with other projects
- Pollutes the global Python installation
- Harder to clean up afterwards

### If you must

```bash
cd D:\dev\ClaudeCode\onmypc_legal_ai
pip install -r requirements.txt
cd frontend
npm install
npm run build
```

---

## Comparison table

| Workflow        | Conda | venv | System Python |
|-----------------|-------|------|----------------|
| Extra installs  | Anaconda/Miniconda | None | None |
| Ease of use     | ★★★★★ | ★★★★☆ | ★★☆☆☆ |
| Isolation       | Full  | Full | None |
| Speed           | Slightly slower | Fast | Fastest |
| Recommendation  | ★★★★★ | ★★★★★ | ★★☆☆☆ |

---

## Quick start TL;DR

```bash
# With Conda
build_conda.bat

# Without Conda
build.bat

# Manual fallback
pip install -r requirements.txt
cd frontend
npm install
npm run build
```

---

## Troubleshooting

- **"conda not found"** → switch to `build.bat`.
- **"python not found"** → install Python 3.10+ from https://python.org.
- **Dependency conflicts** → remove the environment (`conda env remove -n legalai` or `rmdir /s venv`) and recreate it.
- **Build runs out of memory** → increase Node heap then rebuild:

  ```bash
  set NODE_OPTIONS=--max-old-space-size=4096
  cd frontend
  npm run build
  ```
