# Amplifier Web UI

Beautiful, real-time web interface for executing and visualizing Amplifier AI agent workflows.

## Features

- 🎨 **Rich Visualization**: Watch AI agents collaborate in real-time
- ⚡ **Live Updates**: WebSocket-powered real-time progress
- 🚀 **Easy Execution**: Run scenarios with intuitive web forms
- 📊 **Results Display**: View and export execution results
- 🌙 **Dark Mode**: System-aware dark/light themes

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Amplifier CLI tools installed

### Easiest Way - One Command

```bash
cd amplifier-web-ui
./start.sh
```

This will:
- Auto-install dependencies (first time only)
- Start both backend and frontend servers
- Open at http://localhost:5173
- Press Ctrl+C to stop both servers

### Alternative - Manual Steps

```bash
# Install dependencies (first time only)
make install

# Start both servers
make dev
```

This starts:
- Backend API server on http://localhost:8000
- Frontend dev server on http://localhost:5173

### Production Build

```bash
# Build frontend for production
make build

# Run production server
make start
```

## Architecture

```
amplifier-web-ui/
├── backend/          # FastAPI server
│   ├── main.py              # API endpoints + WebSocket
│   ├── models.py            # Pydantic models
│   ├── scenario_discovery.py   # Scan scenarios/
│   ├── process_manager.py   # Execute CLI tools
│   └── requirements.txt     # Python dependencies
│
└── frontend/         # React + TypeScript
    ├── src/
    │   ├── components/      # UI components
    │   ├── hooks/           # Custom React hooks
    │   ├── stores/          # State management
    │   └── types/           # TypeScript types
    └── package.json
```

## Development

### Backend Development

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## Usage

1. **Browse Scenarios**: View all available Amplifier scenarios
2. **Configure**: Fill in scenario parameters via web form
3. **Execute**: Click "Run" to start execution
4. **Watch**: Real-time visualization of agent activity
5. **Results**: View and download outputs

## Integration with Amplifier CLI

The web UI integrates seamlessly with existing Amplifier CLI tools:

- Discovers scenarios from `scenarios/` directory
- Executes via `make` commands
- Parses CLI output for visualization
- Preserves all CLI functionality

## Philosophy

Built with [Amplifier's implementation philosophy](../ai_context/IMPLEMENTATION_PHILOSOPHY.md):

- **Ruthless Simplicity**: Minimal abstractions, clear code
- **Modular Design**: Regeneratable components with stable contracts
- **UX-Focused**: Delightful experience without complexity

## Contributing

Follow the modular design principles:

1. Keep components under 200 lines
2. Clear separation of concerns
3. Stable API contracts
4. Comprehensive error handling

## License

Same as Amplifier project
