@echo off
REM OnMyPC Legal AI - Quick Build Script (Windows)

echo ==========================================
echo OnMyPC Legal AI - Build Script
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
if not exist portable\python\python.exe (
    echo.
    echo WARNING: Portable Python runtime not found.
    echo          Run: python scripts\prepare_portable_env.py --env legalai
    echo          (Replace "legalai" with your environment name.)
)

echo.
echo [2/3] Installing Node dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Building Electron portable bundle...
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
pause
