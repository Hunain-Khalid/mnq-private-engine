#!/bin/bash

echo "🏛️ [Alpha Node] Initializing Quantitative Infrastructure..."

# 0. Kill any existing zombie processes on ports 3000 and 8000
echo "🧹 [Cleanup] Freeing ports 3000 and 8000..."
fuser -k 8000/tcp >/dev/null 2>&1 || true
fuser -k 3000/tcp >/dev/null 2>&1 || true

# 1. Check if DuckDB storage exists, run ETL if missing
if [ ! -f "./storage/alpha_node.duckdb" ]; then
    echo "📦 [ETL] Storage tier missing. Running ETL pipeline..."
    python3 etl_pipeline.py
else
    echo "✅ [ETL] DuckDB storage tier detected."
fi

# 2. Start FastAPI Backend in the background
echo "🚀 [Backend] Launching FastAPI execution server on port 8000..."
cd backend/app
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ../..

# 3. Start Next.js Frontend Development Server
echo "🌐 [Frontend] Launching Next.js trading deck on port 3000..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "⚙️ [Frontend] Installing npm dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo "=================================================="
echo "🎉 [Alpha Node] All systems online!"
echo "📊 Trading Deck: http://localhost:3000"
echo "🔌 FastAPI Docs: http://localhost:8000/docs"
echo "Press [CTRL+C] at any time to gracefully shutdown all nodes."
echo "=================================================="

# Trap Ctrl+C to kill background processes cleanly
cleanup() {
    echo ""
    echo "🛑 [Alpha Node] Shutting down backend and frontend nodes..."
    kill -9 $BACKEND_PID $FRONTEND_PID 2>/dev/null
    fuser -k 8000/tcp >/dev/null 2>&1 || true
    fuser -k 3000/tcp >/dev/null 2>&1 || true
    echo "✅ [Alpha Node] Shutdown complete."
    exit 0
}

trap cleanup INT

while true; do
    sleep 1
done