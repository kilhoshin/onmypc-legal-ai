## Portable Build Guide

These steps create a **fully self-contained** Windows build that ships with its
own Python runtime. No user-side Python or Conda installation is required.

1. **Activate your existing backend environment** (e.g. `conda activate legalai`)
   and make sure all dependencies are installed (`pip install -r requirements.txt`).

2. **Pack the environment into the repo**:

   ```bash
   python scripts/prepare_portable_env.py --env legalai
   ```

   This command uses `conda-pack` to copy the `legalai` environment into
   `portable/python/`. If `conda-pack` is missing, install it with
   `conda install -c conda-forge conda-pack`.

3. **Build the frontend + Electron portable bundle**:

   ```bash
   cd frontend
   npm install      # first time only
   npm run build
   ```

   The resulting portable app lives in `frontend/dist/win-unpacked/`. It now
   contains:

   ```
   resources/
     app.asar
     backend/        (FastAPI code)
     python/         (self-contained runtime)
   ```

4. **Distribute the `win-unpacked` folder**. Users can run
   `OnMyPC Legal AI.exe` directly with no additional dependencies.

### Notes

- The `portable/python/` directory is ignored by git. Re-run the prepare script
  after upgrading dependencies.
- Existing knowledge-base data (`backend/data`) is not bundled; the app creates
  new indexes on first run.
- If you want to reset the portable runtime, delete `portable/python/` and run
  the prepare script again.
