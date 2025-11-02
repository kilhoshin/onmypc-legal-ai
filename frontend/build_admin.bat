@echo off
REM Run this script as Administrator to avoid symbolic link issues

echo ==========================================
echo OnMyPC Legal AI - Admin Build
echo ==========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo Running with Administrator privileges...
echo.

REM Change to the script directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo [1/3] Cleaning cache...
if exist "%LOCALAPPDATA%\electron-builder\Cache" (
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache"
    echo Cache cleaned
) else (
    echo No cache found
)

echo.
echo [2/3] Building React app...
call npm run build:vite
if errorlevel 1 (
    echo ERROR: Failed to build React app
    pause
    exit /b 1
)

echo.
echo [3/3] Packaging Electron app...
call npm run build:electron
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
echo Output: dist\OnMyPC Legal AI Portable.exe
echo.
pause
