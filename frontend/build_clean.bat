@echo off
REM Clean build without macOS signing tools

echo ==========================================
echo OnMyPC Legal AI - Clean Build (No Warnings)
echo ==========================================
echo.

REM Set environment to skip macOS signing
set CSC_IDENTITY_AUTO_DISCOVERY=false
set ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true

echo [1/3] Cleaning cache...
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" (
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign"
    echo Cache cleaned
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
echo [3/3] Packaging Electron app (Windows only)...
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
