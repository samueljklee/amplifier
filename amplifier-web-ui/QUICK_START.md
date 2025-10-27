# Quick Start Guide

## Get It Running in 3 Minutes

### 1. Install Dependencies (1 minute)

```bash
cd amplifier-web-ui

# Backend (Python)
cd .. && uv sync

# Frontend (Node)
cd amplifier-web-ui/frontend && npm install
```

### 2. Start Servers (30 seconds)

**Terminal 1 - Backend:**
```bash
cd amplifier-web-ui
make dev-backend
# Server starts on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd amplifier-web-ui
make dev-frontend
# UI opens on http://localhost:5173
```

**Or run both together:**
```bash
cd amplifier-web-ui
make dev
```

### 3. Open Browser (immediate)

Navigate to: **http://localhost:5173**

You should see:
- 🎨 Amplifier Studio welcome page
- List of available scenarios (blog_writer, transcribe, etc.)
- Click any scenario to configure and run

## What You Can Do

### Run a Scenario

1. Click on "Blog Writer" card
2. Fill in parameters:
   - `idea`: Path to your markdown file with rough thoughts
   - `writings_dir`: Directory with your existing blog posts
3. Click "▶ Run Scenario"
4. Watch real-time:
   - Agent activity cards showing progress
   - Live logs streaming
   - Results when complete

### Watch Agent Activity

During execution you'll see:
- 🔍 Research agents finding sources
- ✍️ Writer agents crafting content
- 📊 Editor agents reviewing
- Real-time progress bars
- Streaming logs

### View Results

When complete:
- See generated files
- Download outputs
- View execution summary

## Troubleshooting

**Backend won't start?**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Try different port
uvicorn backend.api.main:app --port 8001
```

**Frontend won't start?**
```bash
# Check if port 5173 is in use
lsof -i :5173

# Clear node_modules and reinstall
cd frontend && rm -rf node_modules && npm install
```

**No scenarios showing?**
- Verify `scenarios/` directory exists in parent directory
- Check backend logs for errors
- Try: `curl http://localhost:8000/api/scenarios`

## API Endpoints

Test the backend directly:

```bash
# List scenarios
curl http://localhost:8000/api/scenarios

# Get scenario details
curl http://localhost:8000/api/scenarios/blog_writer

# Start execution
curl -X POST http://localhost:8000/api/scenarios/blog_writer/execute \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"idea": "test.md", "writings_dir": "~/blog"}}'
```

## Next Steps

- Explore different scenarios
- Create custom parameters
- Watch real-time visualizations
- Export results

Enjoy! 🚀
