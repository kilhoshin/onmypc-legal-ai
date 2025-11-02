@echo off
REM Quick test - Let Electron handle backend startup

echo ==========================================
echo OnMyPC Legal AI - Test Run
echo ==========================================
echo.

echo Starting Application...
echo (Electron will start backend automatically)
echo.

cd /d "%~dp0\frontend"
npm run dev:electron

pause
