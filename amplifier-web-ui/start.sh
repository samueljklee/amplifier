#!/bin/bash
set -e

echo "🚀 Starting Amplifier Web UI..."
echo ""

# Check if dependencies are installed
if [ ! -d "backend/.venv" ] || [ ! -d "frontend/node_modules" ]; then
    echo "📦 First time setup - installing dependencies..."
    make install
    echo ""
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit
}

trap cleanup EXIT INT TERM

# Start backend in background
echo "🔧 Starting backend server on http://localhost:8000 ..."
cd backend
PYTHONPATH=$(pwd) uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend ready!"
        break
    fi
    sleep 1
done

# Start frontend in background
echo "🎨 Starting frontend server on http://localhost:5173 ..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Amplifier Web UI is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 Open: http://localhost:5173"
echo "  📊 API:  http://localhost:8000"
echo ""
echo "  📝 Logs:"
echo "     Backend:  tail -f backend.log"
echo "     Frontend: tail -f frontend.log"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
wait