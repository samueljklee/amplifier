# Amplifier Web UI - Quick Reference

**For**: Developers implementing the web UI  
**See**: `IMPLEMENTATION_SPEC.md` for complete details

---

## At a Glance

**What**: Web interface for Amplifier CLI tools  
**Stack**: FastAPI (backend) + React/TypeScript (frontend)  
**Lines of Code**: ~5,500 total (2,000 backend + 3,500 frontend)  
**Timeline**: 3-4 weeks for production MVP

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [IMPLEMENTATION_SPEC.md](./IMPLEMENTATION_SPEC.md) | Full specification (complete blueprint) |
| [API.md](../docs/API.md) | API reference (after implementation) |
| [ARCHITECTURE.md](../docs/ARCHITECTURE.md) | Architecture deep-dive (after implementation) |

---

## Module Boundaries (Studs)

### Backend "Bricks"

Each module is regeneratable independently:

```
1. Scenario Discovery (services/scenario_discovery.py)
   Input:  scenarios/ directory path
   Output: List[Scenario] with metadata
   
2. Process Manager (services/process_manager.py)
   Input:  CLI command + parameters
   Output: job_id + stdout/stderr stream
   
3. Event Broadcaster (services/event_broadcaster.py)
   Input:  WebSocket events
   Output: Broadcast to connected clients
   
4. Output Parser (services/output_parser.py)
   Input:  CLI stdout/stderr lines
   Output: Structured stage/progress data
```

### Frontend "Bricks"

Each component is regeneratable independently:

```
1. ScenarioForm (components/scenarios/ScenarioForm.tsx)
   Input:  Scenario with parameters
   Output: ExecutionRequest object
   
2. WorkflowViz (components/execution/WorkflowViz.tsx)
   Input:  StageState[]
   Output: Visual workflow diagram
   
3. LogStream (components/execution/LogStream.tsx)
   Input:  LogLine[] + filters
   Output: Virtualized log display
   
4. useWebSocket (hooks/useWebSocket.ts)
   Input:  job_id
   Output: Real-time event stream
```

---

## API Contracts (Studs)

### REST Endpoints

```typescript
GET    /api/v1/scenarios          → List all scenarios
GET    /api/v1/scenarios/{id}     → Get scenario details
POST   /api/v1/executions         → Start execution
GET    /api/v1/executions/{id}    → Get execution status
POST   /api/v1/executions/{id}/cancel → Cancel execution
GET    /api/v1/executions/{id}/artifacts/{file} → Download artifact
```

### WebSocket Events

```typescript
// Server → Client
execution.started       // Execution began
execution.stage_changed // New stage active
execution.progress      // Progress update
execution.output        // stdout/stderr line
execution.artifact      // File generated
execution.completed     // Execution finished
execution.error         // Error occurred
```

---

## Implementation Phases

### Phase 1: MVP (Week 1)
- [x] Basic scenario listing
- [x] Simple parameter form
- [x] Execute CLI via subprocess
- [x] Stream logs via WebSocket
- **Output**: Can run scenarios and see logs

### Phase 2: Enhanced UX (Week 2)
- [x] Workflow visualization
- [x] Stage progress tracking
- [x] File upload support
- [x] Artifact download
- **Output**: Beautiful, informative UI

### Phase 3: Polish (Week 3)
- [x] Dark mode
- [x] Log filtering
- [x] Responsive design
- [x] Accessibility
- **Output**: Production-ready

---

## Key Design Decisions

### Why subprocess execution?
- Isolation (can't crash server)
- Works with any CLI tool
- Maintains CLI-first philosophy

### Why WebSocket not SSE?
- Bi-directional (can send commands)
- Better browser support
- More flexible

### Why TanStack Query?
- Best server state management
- Auto caching/refetching
- Less boilerplate than Redux

### Why Vite not CRA?
- 10x faster HMR
- Modern tooling
- Smaller bundles

---

## File Size Estimates

**Backend Python**:
```
api/         ~470 lines (3 files)
services/    ~700 lines (4 files)
models/      ~240 lines (3 files)
tests/       ~250 lines (3 files)
config/main  ~230 lines (2 files)
─────────────────────────
Total:      ~1,890 lines
```

**Frontend TypeScript**:
```
components/  ~1,480 lines (15 files)
api/ws/      ~380 lines (4 files)
hooks/       ~360 lines (4 files)
stores/      ~230 lines (2 files)
types/       ~300 lines (3 files)
utils/       ~210 lines (3 files)
tests/       ~400 lines (many files)
─────────────────────────
Total:      ~3,360 lines
```

**Grand Total: ~5,250 lines**

---

## Getting Started (After Implementation)

### Development Setup

```bash
# Backend
cd amplifier-web-ui/backend
make install          # Install Python deps with uv
make dev              # Start backend (port 8000)

# Frontend (separate terminal)
cd amplifier-web-ui/frontend
npm install           # Install Node deps
npm run dev           # Start frontend (port 3000)
```

### Testing

```bash
# Backend tests
cd backend
make test

# Frontend tests
cd frontend
npm test
```

### Production Build

```bash
# Frontend
cd frontend
npm run build         # Creates dist/ bundle

# Backend serves frontend static files
cd backend
make start-prod       # Serves frontend + API
```

---

## Common Tasks

### Adding a New Scenario

No code changes needed! Just add to `scenarios/` directory:

```
scenarios/my_new_tool/
├── README.md         # Auto-parsed for description
├── main.py          # CLI with @click.option decorators
└── ...
```

Web UI will automatically discover it on next scan.

### Adding a New WebSocket Event

1. Define in `backend/models/events.py`:
   ```python
   class MyNewEvent(BaseModel):
       type: Literal["execution.my_event"]
       data: dict
   ```

2. Emit in `backend/services/event_broadcaster.py`:
   ```python
   await broadcaster.broadcast(job_id, MyNewEvent(...))
   ```

3. Handle in `frontend/stores/executionStore.ts`:
   ```typescript
   handleEvent: (event) => {
     if (event.type === 'execution.my_event') {
       // Handle event
     }
   }
   ```

### Customizing Visualization

Edit `frontend/components/execution/WorkflowViz.tsx`:
- Modify stage node appearance
- Add custom animations
- Change layout (vertical/horizontal)

All visualization logic is isolated in this component.

---

## Troubleshooting

### "WebSocket connection failed"

Check:
1. Backend is running on port 8000
2. No firewall blocking WebSocket
3. Job ID is valid

### "Scenario not found"

Check:
1. Scenario directory exists in `scenarios/`
2. Has valid `README.md`
3. Has CLI entry point (main.py or cli.py)

### "Logs not updating"

Check:
1. WebSocket is connected (see browser console)
2. Process is actually outputting (check stderr)
3. Output parser patterns match your CLI format

---

## Performance Targets

- **Scenario listing**: < 100ms
- **Execution start**: < 500ms
- **WebSocket latency**: < 50ms
- **Log rendering**: 60fps with 10,000+ lines
- **Bundle size**: < 500kb gzipped

---

## Security Considerations

### Phase 1 (MVP)
- No authentication (localhost only)
- No input sanitization beyond basic validation
- Trust all file paths provided

### Phase 2+ (Production)
- Add authentication/authorization
- Sanitize all user inputs
- Validate/sandbox file paths
- Rate limiting on API endpoints
- CORS configuration

---

## Code Generation Tips

When regenerating modules:

1. **Start with the contract**: Read the interface/type definitions first
2. **Preserve the studs**: Don't change public APIs
3. **Test in isolation**: Each module should work standalone
4. **Check integration points**: Verify data flows between modules
5. **Update this doc**: If contracts change, update spec

---

## Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- TanStack Query: https://tanstack.com/query
- Zustand: https://github.com/pmndrs/zustand

### Examples
- See existing scenarios in `scenarios/`
- blog_writer is the exemplar
- Study its CLI parameter patterns

### Getting Help
- Review full spec: `IMPLEMENTATION_SPEC.md`
- Check project philosophy: `@ai_context/IMPLEMENTATION_PHILOSOPHY.md`
- Understand modular design: `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Status**: Ready for implementation
