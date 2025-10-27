.PHONY: install dev dev-backend dev-frontend build clean test

install:
	@echo "📦 Installing dependencies..."
	@echo "Backend (Python)..."
	cd backend && uv sync
	@echo "Frontend (Node)..."
	cd frontend && npm install
	@echo "✅ Installation complete!"

dev-backend:
	@echo "🚀 Starting backend server..."
	@echo "📁 Working dir: $$(pwd)"
	PYTHONPATH=$$(pwd)/backend uv run --directory backend uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "🚀 Starting frontend dev server..."
	cd frontend && npm run dev

dev:
	@echo "🚀 Starting both servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@$(MAKE) -j2 dev-backend dev-frontend

build:
	@echo "🏗️  Building frontend..."
	cd frontend && npm run build
	@echo "✅ Build complete!"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf frontend/dist frontend/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	@echo "🧪 Running tests..."
	cd .. && uv run pytest amplifier-web-ui/backend/tests/

.DEFAULT_GOAL := help

help:
	@echo "Amplifier Web UI - Available Commands"
	@echo ""
	@echo "  make install       Install all dependencies"
	@echo "  make dev           Run both backend and frontend"
	@echo "  make dev-backend   Run backend only (port 8000)"
	@echo "  make dev-frontend  Run frontend only (port 5173)"
	@echo "  make build         Build frontend for production"
	@echo "  make test          Run tests"
	@echo "  make clean         Clean build artifacts"
	@echo ""
