# Web UI + CLI Integration: Architectural Patterns for Amplifier

**Date**: 2025-10-22
**Context**: Research patterns for adding web UI to visualize Amplifier's CLI-based scenario tools

---

## Executive Summary

Three proven deployment models exist for bridging web UIs with local CLI tools:

1. **Local Web Server** (Recommended for Amplifier) - Web server runs on user's machine, executes CLI tools directly
2. **Electron/Desktop App** - Hybrid approach with web UI + native file system access
3. **Cloud UI + Local Agent** - Remote web UI communicates with local agent for execution

**Recommendation**: Start with Local Web Server pattern (like JupyterLab/Docker Desktop) - provides immediate value with minimal infrastructure complexity.

---

## Pattern 1: Local Web Server (Recommended)

### Architecture

```
┌─────────────────────────────────────────────────┐
│ User's Machine                                  │
│                                                 │
│  ┌──────────────┐         ┌─────────────────┐ │
│  │   Browser    │◄────────┤  FastAPI Server │ │
│  │ (localhost)  │  HTTP   │   Port 8000     │ │
│  └──────────────┘         └────────┬────────┘ │
│                                    │          │
│                            ┌───────▼───────┐  │
│                            │  CLI Executor │  │
│                            │  (subprocess) │  │
│                            └───────┬───────┘  │
│                                    │          │
│                    ┌───────────────▼──────┐   │
│                    │ Filesystem           │   │
│                    │ - scenarios/         │   │
│                    │ - .data/sessions/    │   │
│                    └──────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### How It Works

1. **Server**: FastAPI/Flask runs locally (127.0.0.1:8000)
2. **Execution**: Server shells out to CLI via `subprocess.run()` or `asyncio.create_subprocess_exec()`
3. **Real-time Updates**: WebSocket/SSE streams stdout/stderr back to browser
4. **File Access**: Direct filesystem reads (scenarios/, .data/) - server has full access
5. **State Sync**: Monitor .data/sessions/*.json for state changes

### Real-World Examples

**JupyterLab** (jupyter-server):
- Local server starts with `jupyter lab`
- Browser connects to http://localhost:8888
- Executes Python kernels via ZeroMQ sockets
- 5 channels: Shell (execution), IOPub (output), Stdin (input), Control, Heartbeat

**Docker Desktop**:
- Local API server communicates with Docker daemon
- Web UI reads containers/images via Docker API (Unix socket)
- Direct CLI bridging through `docker` commands
- Everything runs locally on user's machine

**Portainer** (Docker GUI):
- Lightweight web UI for Docker
- Connects to Docker daemon via Unix socket or TCP
- Full lifecycle management through API calls
- Web-based but executes locally

### Implementation for Amplifier

```python
# amplifier/web/server.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from pathlib import Path

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/scenarios")
async def list_scenarios():
    """Discover available scenarios by scanning directory"""
    scenarios_dir = Path("scenarios")
    scenarios = []
    for scenario in scenarios_dir.iterdir():
        if scenario.is_dir() and (scenario / "README.md").exists():
            readme = (scenario / "README.md").read_text()
            # Extract title, description from README
            scenarios.append({
                "id": scenario.name,
                "name": scenario.name.replace("_", " ").title(),
                "path": str(scenario),
                "readme_excerpt": readme[:200]
            })
    return scenarios

@app.post("/scenarios/{scenario_id}/execute")
async def execute_scenario(scenario_id: str, params: dict):
    """Execute a scenario via CLI"""
    cmd = [
        "make",
        f"{scenario_id.replace('_', '-')}",
        *[f"{k.upper()}={v}" for k, v in params.items()]
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    return {
        "exit_code": process.returncode,
        "stdout": stdout.decode(),
        "stderr": stderr.decode()
    }

@app.websocket("/ws/execute/{scenario_id}")
async def execute_with_streaming(websocket: WebSocket, scenario_id: str):
    """Execute scenario with real-time output streaming"""
    await websocket.accept()
    params = await websocket.receive_json()

    cmd = ["uv", "run", "python", "-m", f"scenarios.{scenario_id}"]
    for k, v in params.items():
        cmd.extend([f"--{k}", str(v)])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Stream stdout line-by-line
    async for line in process.stdout:
        await websocket.send_json({
            "type": "stdout",
            "data": line.decode()
        })

    await websocket.close()

@app.get("/sessions")
async def list_sessions():
    """Read .data/ directory to find all sessions"""
    data_dir = Path(".data")
    sessions = []
    for tool_dir in data_dir.iterdir():
        if tool_dir.is_dir():
            for session_dir in tool_dir.iterdir():
                if session_dir.is_dir():
                    state_file = session_dir / "state.json"
                    if state_file.exists():
                        state = json.loads(state_file.read_text())
                        sessions.append({
                            "tool": tool_dir.name,
                            "session_id": session_dir.name,
                            "state": state
                        })
    return sessions

@app.get("/sessions/{tool}/{session_id}/files")
async def list_session_files(tool: str, session_id: str):
    """List all files in a session directory"""
    session_dir = Path(f".data/{tool}/{session_id}")
    files = []
    for file_path in session_dir.rglob("*"):
        if file_path.is_file():
            files.append({
                "path": str(file_path.relative_to(session_dir)),
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            })
    return files
```

### Frontend Integration

```typescript
// web-ui/src/api/scenarios.ts
export async function executeScenario(
  scenarioId: string,
  params: Record<string, string>,
  onProgress: (line: string) => void
) {
  const ws = new WebSocket(`ws://localhost:8000/ws/execute/${scenarioId}`);

  ws.onopen = () => {
    ws.send(JSON.stringify(params));
  };

  ws.onmessage = (event) => {
    const { type, data } = JSON.parse(event.data);
    if (type === 'stdout') {
      onProgress(data);
    }
  };

  return new Promise((resolve) => {
    ws.onclose = () => resolve();
  });
}

export async function listScenarios() {
  const response = await fetch('http://localhost:8000/scenarios');
  return response.json();
}
```

### Advantages for Amplifier

✅ **Direct file access** - No syncing needed, server reads scenarios/ and .data/ directly
✅ **Native execution** - CLI tools run exactly as designed
✅ **Simple security** - Only accepts localhost connections
✅ **No cloud infrastructure** - Everything local
✅ **Easy debugging** - Same environment as CLI
✅ **Progressive enhancement** - CLI still works independently

### Challenges

⚠️ **User needs to run server** - Requires `make serve` or similar
⚠️ **Port conflicts** - Need to handle 8000 already in use
⚠️ **No authentication** - Anyone on localhost can access (usually acceptable)

---

## Pattern 2: Electron Desktop App

### Architecture

```
┌────────────────────────────────────────┐
│ Electron App                           │
│  ┌──────────────────────────────────┐ │
│  │  Renderer Process (Web UI)       │ │
│  │  - React/Vue frontend            │ │
│  └────────────┬─────────────────────┘ │
│               │ IPC                   │
│  ┌────────────▼─────────────────────┐ │
│  │  Main Process (Node.js)          │ │
│  │  - Filesystem access             │ │
│  │  - CLI execution (child_process) │ │
│  │  - Native APIs                   │ │
│  └────────────┬─────────────────────┘ │
│               │                       │
│               ▼                       │
│         User's Filesystem             │
└────────────────────────────────────────┘
```

### How It Works

**VS Code Architecture** (our closest parallel):
- **Main Process**: Node.js with full system access
- **Renderer Process**: Chromium rendering UI (sandboxed)
- **IPC Communication**: Message passing between processes via `contextBridge`
- **Extensions**: Run in separate processes, communicate via message ports
- **File Watching**: Main process monitors filesystem, notifies renderers
- **Terminal Integration**: PTY (pseudo-terminal) in main process, rendered in UI

### Implementation Approach

```javascript
// electron/main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

// Execute scenario
ipcMain.handle('execute-scenario', async (event, scenarioId, params) => {
  const makeArgs = [
    scenarioId,
    ...Object.entries(params).map(([k, v]) => `${k.toUpperCase()}=${v}`)
  ];

  const process = spawn('make', makeArgs, {
    cwd: app.getPath('userData'),
    shell: true
  });

  // Stream output back to renderer
  process.stdout.on('data', (data) => {
    event.sender.send('process-output', {
      type: 'stdout',
      data: data.toString()
    });
  });

  return new Promise((resolve) => {
    process.on('close', (code) => resolve(code));
  });
});

// List scenarios
ipcMain.handle('list-scenarios', async () => {
  const scenariosDir = path.join(app.getPath('userData'), 'scenarios');
  const entries = await fs.readdir(scenariosDir, { withFileTypes: true });
  return entries
    .filter(e => e.isDirectory())
    .map(e => ({ id: e.name, path: path.join(scenariosDir, e.name) }));
});
```

```typescript
// renderer/src/api/electron.ts (preload bridge)
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  executeScenario: (id: string, params: any) =>
    ipcRenderer.invoke('execute-scenario', id, params),

  listScenarios: () =>
    ipcRenderer.invoke('list-scenarios'),

  onProcessOutput: (callback: (data: any) => void) =>
    ipcRenderer.on('process-output', (_, data) => callback(data))
});
```

### Advantages

✅ **Native app experience** - Feels like desktop software
✅ **Auto-updates possible** - electron-updater integration
✅ **System integration** - Menu bar, notifications, file associations
✅ **No server management** - Users just launch the app

### Challenges

⚠️ **Much larger scope** - Need to package entire Electron app
⚠️ **Distribution complexity** - Code signing, installers for each OS
⚠️ **Bundle size** - 100MB+ download (Electron + Chromium)
⚠️ **More maintenance** - Security updates, platform-specific bugs

---

## Pattern 3: Cloud UI + Local Agent

### Architecture

```
┌───────────────────┐          ┌──────────────────────┐
│   Cloud Server    │          │   User's Machine     │
│                   │          │                      │
│  ┌─────────────┐ │          │  ┌────────────────┐ │
│  │  Web UI     │ │          │  │  Local Agent   │ │
│  │  (React)    │ │◄────────►│  │  (Python)      │ │
│  └─────────────┘ │ HTTPS/WS │  └────────┬───────┘ │
│                   │          │           │         │
│  ┌─────────────┐ │          │  ┌────────▼───────┐ │
│  │  Database   │ │          │  │  CLI Executor  │ │
│  │  (sessions) │ │          │  │  (scenarios/)  │ │
│  └─────────────┘ │          │  └────────────────┘ │
└───────────────────┘          └──────────────────────┘
```

### How It Works

1. **Web UI**: Hosted remotely (Vercel/Netlify)
2. **Local Agent**: Long-running process on user's machine
3. **Communication**: WebSocket connection with auth token
4. **Execution**: Agent receives commands, executes locally, streams results
5. **State Sync**: Agent uploads session state to cloud DB

### Implementation

```python
# amplifier/agent/client.py
import asyncio
import websockets
import json
from pathlib import Path

class AmplifierAgent:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.ws_url = "wss://amplifier.app/agent/connect"

    async def connect(self):
        async with websockets.connect(
            self.ws_url,
            extra_headers={"Authorization": f"Bearer {self.api_token}"}
        ) as websocket:
            while True:
                message = await websocket.recv()
                command = json.loads(message)

                if command["type"] == "execute":
                    await self.execute_scenario(
                        websocket,
                        command["scenario_id"],
                        command["params"]
                    )

    async def execute_scenario(self, ws, scenario_id, params):
        cmd = ["uv", "run", "python", "-m", f"scenarios.{scenario_id}"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE
        )

        async for line in process.stdout:
            await ws.send(json.dumps({
                "type": "output",
                "data": line.decode()
            }))
```

### Advantages

✅ **No local server setup** - Agent runs in background
✅ **Mobile access** - Control from phone/tablet
✅ **Collaboration potential** - Share sessions with team
✅ **Centralized UI updates** - Deploy changes instantly

### Challenges

⚠️ **Complex architecture** - Need cloud backend + auth + DB
⚠️ **Network dependency** - Requires internet connection
⚠️ **Security concerns** - Executing commands from remote server
⚠️ **Cost** - Cloud hosting + database fees
⚠️ **Harder debugging** - Distributed system complexity

---

## State Synchronization Patterns

### Pattern A: Direct Filesystem Monitoring

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SessionMonitor(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('state.json'):
            # Notify connected WebSocket clients
            state = json.loads(Path(event.src_path).read_text())
            broadcast_to_websockets({
                "type": "state_update",
                "session_id": Path(event.src_path).parent.name,
                "state": state
            })

observer = Observer()
observer.schedule(SessionMonitor(), path=".data", recursive=True)
observer.start()
```

### Pattern B: Event-Driven Updates

```python
# Existing CLI tools emit events
class StateManager:
    def update_stage(self, stage: str):
        self.state.stage = stage
        self.save()
        # NEW: Notify web UI
        if web_server_running():
            emit_websocket_event({
                "type": "stage_change",
                "session_id": self.session_id,
                "stage": stage
            })
```

### Pattern C: Polling (Simplest)

```typescript
// Frontend polls for updates
async function pollSessionState(sessionId: string) {
  const interval = setInterval(async () => {
    const state = await fetch(`/api/sessions/${sessionId}/state`).then(r => r.json());
    updateUI(state);
  }, 1000); // Poll every second

  return () => clearInterval(interval);
}
```

---

## Visualization Opportunities

### What CLI Cannot Show

1. **Real-time Progress Trees**
   ```
   Blog Writer Session
   ├─ ✅ Extract Style (12.3s)
   │  ├─ Analyzed 15 files
   │  └─ Found 3 style patterns
   ├─ ⏳ Write Initial Draft (in progress)
   │  └─ 45% complete (1,234 / 2,500 words)
   └─ ⏸️  Review (pending)
   ```

2. **Interactive Parameter Forms**
   - File pickers for IDEA and WRITINGS paths
   - Validation before execution (file exists, directory not empty)
   - Save presets for common workflows

3. **Side-by-Side Comparisons**
   ```
   ┌─────────────────┬─────────────────┐
   │ Iteration 1     │ Iteration 2     │
   │ (draft)         │ (revised)       │
   │                 │                 │
   │ Lorem ipsum...  │ Updated text... │
   └─────────────────┴─────────────────┘
   ```

4. **Session History Timeline**
   ```
   10:30 AM  Started session
   10:32 AM  ✅ Style extraction complete
   10:45 AM  ✅ Draft written (2,341 words)
   10:47 AM  ⚠️  Source review: 3 issues found
   10:50 AM  User feedback: "Make introduction shorter"
   10:55 AM  ✅ Revision complete
   ```

5. **Live Log Streaming with Filtering**
   ```
   [Filter: ⚙️ Show only warnings and errors]

   ⚠️ 10:47:23 - Source review found unsupported claim
   ℹ️  10:48:01 - Revising paragraph 3
   ❌ 10:49:12 - Retry: LLM rate limit (attempt 2/3)
   ✅ 10:49:45 - Retry successful
   ```

6. **Dependency Graph Visualization**
   ```
   [blog_writer] → requires → [style_extractor]
                            ↘
                              [style_reviewer]
   ```

7. **Session Comparison**
   - Compare parameters between sessions
   - "What changed between Session A and Session B?"
   - Success rate metrics by configuration

---

## Recommended Approach for Amplifier

### Phase 1: Minimal Local Server (Week 1-2)

**Goal**: Prove value with minimal code

```bash
# Start server
make web-serve

# Opens browser to http://localhost:8000
# Shows:
# - List of available scenarios
# - Recent sessions with state
# - Click to view session details
```

**Features**:
- ✅ List scenarios (read scenarios/ directory)
- ✅ List sessions (read .data/ directory)
- ✅ View session state/files
- ✅ Trigger execution via WebSocket
- ✅ Stream output in real-time

**Tech Stack**:
- Backend: FastAPI (already have FleetCode example)
- Frontend: Plain HTML + Alpine.js (minimal framework)
- Communication: WebSocket for streaming

### Phase 2: Enhanced Visualizations (Week 3-4)

**Add**:
- Progress indicators (parse log output)
- Timeline view of sessions
- Side-by-side draft comparison
- Interactive parameter forms

**Tech Stack**:
- Frontend: Upgrade to React/Vue if needed
- Charts: D3.js or Recharts for timelines

### Phase 3: Polish & Distribution (Week 5-6)

**Consider**:
- Package as Electron app (optional)
- Auto-start server when Amplifier CLI runs
- Desktop notifications for completed runs
- Session sharing (export/import JSON)

---

## Existing Reference: FleetCode Backend

You already have a perfect example in `/fleetcode/backend/`:

```python
# fleetcode/backend/fleetcode/backend/main.py
app = FastAPI(...)

@app.post("/sessions", response_model=Session)
async def create_session(create: SessionCreate):
    session = await session_manager.create_session(create)
    await ws_manager.broadcast({
        "type": "session_created",
        "session": session.model_dump(mode="json")
    })
    return session

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Stream agent output in real-time
```

**Pattern to replicate**:
1. REST endpoints for CRUD operations
2. WebSocket for real-time streaming
3. Broadcast events to all connected clients
4. SessionManager handles subprocess execution

---

## Decision Framework

### Choose Local Web Server if:
- ✅ Primary use case is single-user on their machine
- ✅ Want fast iteration and simple deployment
- ✅ CLI tools already work perfectly
- ✅ Just need better visibility/UX

### Choose Electron if:
- ✅ Want polished desktop app experience
- ✅ Need system integration (menu bar, notifications)
- ✅ Planning commercial distribution
- ✅ Have resources for packaging/signing

### Choose Cloud + Agent if:
- ✅ Need mobile/remote access
- ✅ Building team collaboration features
- ✅ Want centralized updates
- ✅ Have backend infrastructure expertise

---

## Implementation Checklist

### Minimal Viable Web UI (Local Server)

- [ ] Create `amplifier/web/` directory
- [ ] FastAPI server with basic endpoints:
  - [ ] `GET /scenarios` - List available tools
  - [ ] `GET /sessions` - List all sessions
  - [ ] `GET /sessions/{id}` - Get session details
  - [ ] `POST /execute` - Trigger scenario execution
  - [ ] `WebSocket /ws` - Real-time output streaming
- [ ] Simple HTML frontend:
  - [ ] Scenario list with descriptions
  - [ ] Session browser with timestamps
  - [ ] Execution form with parameters
  - [ ] Output viewer with streaming updates
- [ ] Add `make web-serve` command to Makefile
- [ ] Auto-open browser on server start

### Enhanced Features (Later)

- [ ] File system monitoring for live updates
- [ ] Progress parsing from structured logs
- [ ] Interactive parameter validation
- [ ] Session comparison view
- [ ] Export/share session snapshots

---

## Key Insights from Research

1. **JupyterLab Pattern**: Best match for Amplifier
   - Local server with web UI
   - Multiple communication channels (Shell, IOPub, Stdin)
   - Direct kernel execution, results streamed to browser
   - Everything local, no cloud dependency

2. **Docker Desktop Pattern**: GUI over CLI
   - API-driven (every CLI operation has API equivalent)
   - Web UI just visualizes and triggers API calls
   - Multiple GUI options (Portainer, DockStation) built on same API

3. **VS Code Pattern**: Electron architecture
   - Main process (Node.js) has full system access
   - Renderer process (Chromium) displays UI
   - IPC for communication between processes
   - Extensions run in isolated processes

4. **Critical Insight**: Don't rebuild CLI in web
   - Web UI should **visualize** and **trigger**, not **reimplement**
   - Keep CLI as source of truth
   - Web = convenience layer, not replacement

---

## Next Steps

1. **Validate approach**: Review with user - is Local Web Server the right starting point?
2. **Spike implementation**: Build 1-day prototype with FastAPI + basic HTML
3. **User test**: Can someone execute blog-writer from web UI?
4. **Iterate**: Add visualizations based on actual usage
5. **Document**: Create guide for adding web support to scenarios

---

## References

- JupyterLab Architecture: https://docs.jupyter.org/en/stable/projects/architecture/
- VS Code Sandbox Migration: https://code.visualstudio.com/blogs/2022/11/28/vscode-sandbox
- Docker Desktop Architecture: https://docs.docker.com/desktop/
- FleetCode Backend (internal): `/fleetcode/backend/fleetcode/backend/main.py`
