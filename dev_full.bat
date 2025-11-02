@echo off
REM Full development mode with hot reload

echo ==========================================
echo OnMyPC Legal AI - Full Dev Mode
echo ==========================================
echo.

echo Starting Vite dev server...
cd /d "%~dp0\frontend"
start "Vite Server" cmd /k "npm run dev:vite"

echo Waiting for Vite to start...
timeout /t 5 /nobreak >nul

echo.
echo Starting Electron...
npm run dev:electron

pause
