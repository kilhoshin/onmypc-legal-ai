@echo off
REM OnMyPC Legal AI - Development Startup Script (Windows)

echo ==========================================
echo OnMyPC Legal AI - Development Mode
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

echo Starting Backend Server...
start "Backend Server" cmd /k "python backend/main.py"

timeout /t 5 /nobreak >nul

echo Starting Frontend...
cd frontend
npm run dev

pause
