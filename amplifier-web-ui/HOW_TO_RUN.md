# 🚀 How to Run Amplifier Web UI

## Super Simple Method

### Terminal 1 - Start Backend
```bash
cd amplifier-web-ui
./run_backend.sh
```

You'll see:
```
🚀 Amplifier Web UI starting...
📁 Scenarios path: /Users/samule/repo/amplifier/scenarios
✅ Found X scenarios
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Start Frontend
```bash
cd amplifier-web-ui
./run_frontend.sh
```

You'll see:
```
VITE vX.X.X  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.X.X:5173/
```

### Terminal 3 - Open Browser
```bash
open http://localhost:5173
```

Or just navigate to http://localhost:5173 in your browser.

## Using Make (Alternative)

```bash
# Terminal 1
cd amplifier-web-ui
make dev-backend

# Terminal 2
cd amplifier-web-ui
make dev-frontend
```

## What You'll See

1. **Landing Page**: Grid of scenario cards
2. **Click a scenario**: See parameters and description
3. **Fill in parameters**: Dynamic form based on scenario
4. **Run**: Click "▶ Run Scenario"
5. **Watch**: Real-time agent activity visualization
6. **Results**: See outputs when complete

## Example: Run Blog Writer

1. Open http://localhost:5173
2. Click "Blog Writer" card
3. Enter:
   - `idea`: `scenarios/blog_writer/tests/sample_brain_dump.md`
   - `writings_dir`: `scenarios/blog_writer/tests/sample_writings/`
4. Click "▶ Run Scenario"
5. Watch agents work!

## Troubleshooting

**Backend won't start?**
- Check if port 8000 is free: `lsof -i :8000`
- Kill if needed: `lsof -ti:8000 | xargs kill`

**Frontend won't start?**
- First time? Run: `cd frontend && npm install`
- Check if port 5173 is free: `lsof -i :5173`

**No scenarios showing?**
- Make sure scenarios/ directory exists in parent repo
- Check backend terminal for "✅ Found X scenarios" message
- Try: `curl http://localhost:8000/api/scenarios`

**Connection refused in frontend?**
- Make sure backend is running (Terminal 1)
- Check backend shows: "Uvicorn running on http://0.0.0.0:8000"

## Features to Try

- **Dark Mode**: System-aware, toggle in system preferences
- **Real-time Updates**: WebSocket connection shows live agent activity
- **Agent Cards**: Watch agents pulse when active
- **Log Stream**: Terminal-style logs with color coding
- **Responsive Design**: Works on desktop and tablet

Enjoy! 🎨
