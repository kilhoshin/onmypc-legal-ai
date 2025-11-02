@echo off
REM OnMyPC Legal AI - Conda Build Script (Windows)

echo ==========================================
echo OnMyPC Legal AI - Conda Build
echo ==========================================
echo.

REM Check if conda is available
where conda >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda not found! Please install Anaconda or Miniconda
    echo Or use build.bat for regular Python
    pause
    exit /b 1
)

echo [1/5] Creating conda environment...
call conda create -n legalai python=3.10 -y
if errorlevel 1 (
    echo ERROR: Failed to create conda environment
    pause
    exit /b 1
)

echo.
echo [2/5] Activating conda environment...
call conda activate legalai
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment
    pause
    exit /b 1
)

echo.
echo [3/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Capturing portable Python runtime...
python scripts\prepare_portable_env.py --env legalai
if errorlevel 1 (
    echo ERROR: Failed to create portable runtime
    pause
    exit /b 1
)

echo.
echo [4/5] Installing Node dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)

echo.
echo [5/5] Building Electron portable bundle...
call npm run build
if errorlevel 1 (
    echo ERROR: Failed to package Electron app
    pause
    exit /b 1
)

echo.
echo ==========================================
echo BUILD SUCCESSFUL!
echo ==========================================
echo.
echo Output: frontend\dist\OnMyPC Legal AI Portable.exe
echo.
echo To run development server later:
echo   conda activate legalai
echo   cd backend
echo   python main.py
echo.
pause
