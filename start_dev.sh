#!/bin/bash
# OnMyPC Legal AI - Development Startup Script (macOS/Linux)

echo "=========================================="
echo "OnMyPC Legal AI - Development Mode"
echo "=========================================="
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found! Please install Python 3.10+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found! Please install Node.js 18+"
    exit 1
fi

# Start Backend in background
echo "Starting Backend Server..."
cd backend
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start Frontend
echo "Starting Frontend..."
cd ../frontend
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
