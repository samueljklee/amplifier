# Amplifier Web UI - Architecture Diagrams

Visual reference for system architecture and data flows.

---

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              React Frontend (Port 3000)                   │ │
│  │                                                           │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │ │
│  │  │  Scenario   │  │  Execution   │  │   WebSocket    │  │ │
│  │  │  Discovery  │  │  Control     │  │   Client       │  │ │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │ │
│  │         │                │                    │          │ │
│  │         └────────────────┴────────────────────┘          │ │
│  │                          ↕                                │ │
│  │                   HTTP + WebSocket                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                      REST API Layer                       │ │
│  │  /scenarios   /executions   /websocket   /artifacts       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ↕                                      │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Service Layer                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │ │
│  │  │   Scenario   │  │   Process    │  │     Event      │ │ │
│  │  │  Discovery   │  │   Manager    │  │  Broadcaster   │ │ │
│  │  └──────────────┘  └──────────────┘  └────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                          ↕                                      │
│                   Subprocess Execution                          │
└─────────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────────┐
│               Amplifier CLI Tools (scenarios/)                  │
│                                                                 │
│  blog_writer · tips_synthesizer · article_illustrator · ...    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                           │  │
│  │                                                          │  │
│  │  /api/v1/scenarios      GET  List scenarios            │  │
│  │                         GET  Get scenario details       │  │
│  │                                                          │  │
│  │  /api/v1/executions     POST Start execution            │  │
│  │                         GET  Get execution status       │  │
│  │                         POST Cancel execution           │  │
│  │                         GET  Download artifact          │  │
│  │                                                          │  │
│  │  /api/v1/ws/{job_id}    WS   Real-time events          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Service Layer                          │  │
│  │                                                          │  │
│  │  ┌───────────────────┐     ┌───────────────────────┐   │  │
│  │  │ ScenarioDiscovery │     │   ProcessManager      │   │  │
│  │  │                   │     │                       │   │  │
│  │  │ • Scan filesystem │     │ • Start subprocess    │   │  │
│  │  │ • Parse README    │     │ • Stream stdout/stderr│   │  │
│  │  │ • Extract params  │     │ • Monitor lifecycle   │   │  │
│  │  └───────────────────┘     └───────────────────────┘   │  │
│  │                                                          │  │
│  │  ┌───────────────────┐     ┌───────────────────────┐   │  │
│  │  │  OutputParser     │     │  EventBroadcaster     │   │  │
│  │  │                   │     │                       │   │  │
│  │  │ • Parse stages    │     │ • WebSocket manager   │   │  │
│  │  │ • Extract progress│     │ • Event distribution  │   │  │
│  │  │ • Find artifacts  │     │ • Connection tracking │   │  │
│  │  └───────────────────┘     └───────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Data Models                          │  │
│  │                                                          │  │
│  │  Scenario · Parameter · Execution · Artifact · Event    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Component Tree                          │  │
│  │                                                          │  │
│  │                        App                               │  │
│  │                         │                                │  │
│  │                    AppShell                              │  │
│  │           ┌─────────────┼─────────────┐                 │  │
│  │        Header        Sidebar      MainContent           │  │
│  │                         │              │                 │  │
│  │                   ScenarioList   ┌─────┴─────┐          │  │
│  │                                  │           │          │  │
│  │                         ScenarioDetail  ExecutionView   │  │
│  │                                         │               │  │
│  │                          ┌──────────────┼──────────┐    │  │
│  │                    WorkflowViz   LogStream   OutputView│  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   State Management                       │  │
│  │                                                          │  │
│  │  ┌─────────────────────┐    ┌──────────────────────┐   │  │
│  │  │  Server State       │    │   Client State       │   │  │
│  │  │  (TanStack Query)   │    │   (Zustand)          │   │  │
│  │  │                     │    │                      │   │  │
│  │  │ • Scenarios         │    │ • Active executions  │   │  │
│  │  │ • Executions        │    │ • WebSocket state    │   │  │
│  │  │ • Artifacts         │    │ • UI preferences     │   │  │
│  │  │ • Caching/refetch   │    │ • Real-time updates  │   │  │
│  │  └─────────────────────┘    └──────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Clients                           │  │
│  │                                                          │  │
│  │  HTTP Client (fetch) ← → Backend REST API               │  │
│  │  WebSocket Client    ← → Backend WebSocket              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Execution Flow

### Starting an Execution

```
User                 Frontend              Backend              CLI Tool
 │                      │                      │                    │
 │  1. Fill form        │                      │                    │
 ├─────────────────────>│                      │                    │
 │                      │                      │                    │
 │  2. Submit           │                      │                    │
 │                      │  POST /executions    │                    │
 │                      ├─────────────────────>│                    │
 │                      │                      │                    │
 │                      │  { job_id }          │                    │
 │                      │<─────────────────────┤                    │
 │                      │                      │                    │
 │  3. Redirect to      │                      │  subprocess.exec   │
 │     /executions/123  │                      ├───────────────────>│
 │<─────────────────────┤                      │                    │
 │                      │                      │  stdout/stderr     │
 │                      │                      │<───────────────────┤
 │                      │                      │                    │
 │  4. Connect WS       │                      │                    │
 │                      │  WS /ws/123          │                    │
 │                      ├─────────────────────>│                    │
 │                      │                      │                    │
 │  5. Receive events   │  { type: output }    │                    │
 │                      │<─────────────────────┤                    │
 │<─────────────────────┤                      │                    │
 │  (visualize stages)  │                      │                    │
```

### Real-time Event Flow

```
CLI Output           ProcessManager       EventBroadcaster      Frontend
    │                      │                      │                 │
    │  stdout line         │                      │                 │
    ├─────────────────────>│                      │                 │
    │                      │                      │                 │
    │                      │  Parse stage         │                 │
    │                      │  change              │                 │
    │                      │                      │                 │
    │                      │  Create event        │                 │
    │                      ├─────────────────────>│                 │
    │                      │                      │                 │
    │                      │                      │  Broadcast      │
    │                      │                      ├────────────────>│
    │                      │                      │                 │
    │                      │                      │                 │  Update
    │                      │                      │                 │  WorkflowViz
    │                      │                      │                 ├────────┐
    │                      │                      │                 │        │
    │                      │                      │                 │<───────┘
```

---

## Module Dependencies

### Backend Module Graph

```
main.py
  │
  ├─> api/scenarios.py
  │     └─> services/scenario_discovery.py
  │           └─> models/scenario.py
  │
  ├─> api/execution.py
  │     ├─> services/process_manager.py
  │     │     ├─> services/output_parser.py
  │     │     └─> services/event_broadcaster.py
  │     └─> models/execution.py
  │
  └─> api/websocket.py
        └─> services/event_broadcaster.py
              └─> models/events.py
```

**Key Property**: No circular dependencies. Each layer depends only on layers below.

### Frontend Module Graph

```
App.tsx
  │
  ├─> components/layout/AppShell.tsx
  │     ├─> components/layout/Header.tsx
  │     ├─> components/layout/Sidebar.tsx
  │     └─> components/scenarios/ScenarioList.tsx
  │
  ├─> components/scenarios/ScenarioDetail.tsx
  │     └─> components/scenarios/ScenarioForm.tsx
  │           └─> hooks/useScenarios.ts
  │                 └─> api/scenarios.ts
  │
  └─> components/execution/ExecutionView.tsx
        ├─> components/execution/WorkflowViz.tsx
        ├─> components/execution/LogStream.tsx
        ├─> components/execution/OutputView.tsx
        ├─> hooks/useExecution.ts
        │     └─> api/execution.ts
        └─> hooks/useWebSocket.ts
              ├─> api/websocket.ts
              └─> stores/executionStore.ts
```

**Key Property**: Components depend on hooks, hooks depend on API clients and stores.

---

## Data Flow Diagrams

### Scenario Discovery

```
Filesystem                   Backend                    Frontend
    │                           │                          │
    │  scenarios/               │                          │
    │  ├─ blog_writer/          │                          │
    │  │  ├─ README.md          │                          │
    │  │  └─ main.py            │                          │
    │  └─ tips_synthesizer/     │                          │
    │     ├─ README.md          │                          │
    │     └─ cli.py             │                          │
    │                           │                          │
    │                           │  GET /scenarios          │
    │                           │<─────────────────────────┤
    │                           │                          │
    │  Read directories         │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │  README.md content        │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │  Parse @click.option      │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │                           │  { scenarios: [...] }    │
    │                           ├─────────────────────────>│
    │                           │                          │
    │                           │                          │  Render
    │                           │                          │  list
```

### Execution with Real-time Updates

```
User     Frontend        Backend         Process        CLI Tool
 │          │               │               │               │
 │  Click   │               │               │               │
 │  "Start" │               │               │               │
 ├─────────>│               │               │               │
 │          │               │               │               │
 │          │  POST         │               │               │
 │          │  /executions  │               │               │
 │          ├──────────────>│               │               │
 │          │               │  spawn        │               │
 │          │               ├──────────────>│  python -m    │
 │          │               │               ├──────────────>│
 │          │               │               │               │
 │          │  { job_id }   │               │  stdout       │
 │          │<──────────────┤               │<──────────────┤
 │          │               │               │               │
 │          │  WS connect   │               │               │
 │          ├──────────────>│               │               │
 │          │               │               │               │
 │          │               │  Parse output │               │
 │          │               │<──────────────┤               │
 │          │               │               │               │
 │          │  WS event     │               │               │
 │          │  (stage)      │               │               │
 │          │<──────────────┤               │               │
 │          │               │               │               │
 │  Update  │               │               │               │
 │  viz     │               │               │               │
 │<─────────┤               │               │               │
 │          │               │               │               │
 │          │  WS event     │               │               │
 │          │  (progress)   │               │               │
 │          │<──────────────┤               │               │
 │          │               │               │               │
 │  Update  │               │               │  File saved   │
 │  progress│               │               │<──────────────┤
 │<─────────┤               │               │               │
 │          │               │  Scan files   │               │
 │          │               │<──────────────┤               │
 │          │               │               │               │
 │          │  WS event     │               │               │
 │          │  (artifact)   │               │               │
 │          │<──────────────┤               │               │
 │          │               │               │               │
 │  Show    │               │               │  Exit         │
 │  artifact│               │               │<──────────────┤
 │<─────────┤               │               │               │
 │          │               │  WS event     │               │
 │          │               │  (completed)  │               │
 │          │<──────────────┤               │               │
```

---

## State Transitions

### Execution Lifecycle

```
    ┌──────────┐
    │  queued  │
    └────┬─────┘
         │ Process starts
         ↓
    ┌──────────┐
    │ running  │──────────┐
    └────┬─────┘          │ Cancel requested
         │                │
         │ Process exits  ↓
         ↓           ┌────────────┐
    ┌──────────┐    │ cancelled  │
    │completed │    └────────────┘
    └──────────┘
         ↑
         │ Non-zero exit
         │
    ┌──────────┐
    │  failed  │
    └──────────┘
```

### Stage Lifecycle

```
    ┌──────────┐
    │ pending  │
    └────┬─────┘
         │ Stage starts
         ↓
    ┌──────────┐
    │  active  │──────────┐
    └────┬─────┘          │ Error occurs
         │                │
         │ Stage completes↓
         ↓           ┌──────────┐
    ┌──────────┐    │  failed  │
    │completed │    └──────────┘
    └──────────┘
```

---

## Visualization Components

### WorkflowViz Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Visualization                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stage 1          Stage 2          Stage 3        Stage 4  │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐   ┌─────────┐│
│  │ Extract │────>│  Draft  │────>│ Review  │──>│ Refine  ││
│  │  Style  │     │ Content │     │ Sources │   │  Draft  ││
│  │         │     │         │     │         │   │         ││
│  │    ✓    │     │    ⟳    │     │    ○    │   │    ○    ││
│  │  2.3s   │     │  15.1s  │     │    —    │   │    —    ││
│  └─────────┘     └─────────┘     └─────────┘   └─────────┘│
│   Completed      In Progress      Pending        Pending   │
│                                                             │
│  ───────────────────────────────────────────────────────   │
│  Progress: ████████████░░░░░░░░░░░░░░░░░░░░ 40%          │
│  Stage 2 of 4 · Elapsed: 17.4s                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Stage Detail Card

```
┌─────────────────────────────────────────────────────────────┐
│ ⟳ Draft Content                              [Collapse ▲]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Status:  In Progress                                        │
│ Started: 10:32:18                                           │
│ Elapsed: 15.1 seconds                                       │
│                                                             │
│ Details:                                                    │
│  • Generating blog draft from idea                          │
│  • Using extracted style profile                            │
│  • Tokens used: 1,234 / 4,000                              │
│                                                             │
│ Recent logs:                                                │
│  10:32:18 | INFO  | ✍️ Writing initial blog draft...       │
│  10:32:20 | DEBUG | Analyzing brain dump (547 words)       │
│  10:32:25 | DEBUG | Applying style profile                 │
│  10:32:30 | INFO  | Draft generation 75% complete          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Log Stream View

```
┌─────────────────────────────────────────────────────────────┐
│ Execution Log                                               │
│ [Filter: All ▼] [Search: ________] [Auto-scroll: ON]       │
├─────────────────────────────────────────────────────────────┤
│ Time     │ Level │ Message                                  │
├──────────┼───────┼──────────────────────────────────────────┤
│ 10:32:15 │ INFO  │ 🚀 Starting Blog Post Writer Pipeline   │
│ 10:32:15 │ INFO  │ Session: 20251022_103215                │
│ 10:32:16 │ INFO  │ 📝 Extracting author's style...         │
│ 10:32:17 │ DEBUG │ Found 5 writing samples                 │
│ 10:32:17 │ DEBUG │ • sample1.md (1,234 words)              │
│ 10:32:17 │ DEBUG │ • sample2.md (987 words)                │
│ 10:32:18 │ INFO  │ ✓ Style extraction complete (2.3s)      │
│ 10:32:18 │ INFO  │ ✍️ Writing initial blog draft...        │
│ 10:32:20 │ DEBUG │ Analyzing brain dump (547 words)        │
│ 10:32:25 │ DEBUG │ Applying style profile                  │
│ 10:32:30 │ INFO  │ Draft generation 75% complete           │
│ 10:32:33 │ INFO  │ ✓ Draft generation complete (15.1s)     │
│ 10:32:33 │ INFO  │ 🔍 Reviewing source accuracy...         │
│          │       │                                          │
│          │       │ [Streaming new lines...]                │
│          │       │                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
Error Occurs          Backend              Frontend          User
     │                   │                    │               │
     │  Exception        │                    │               │
     ├──────────────────>│                    │               │
     │                   │                    │               │
     │                   │  Log error         │               │
     │                   │  details           │               │
     │                   │                    │               │
     │                   │  Create error      │               │
     │                   │  event             │               │
     │                   │                    │               │
     │                   │  WS broadcast      │               │
     │                   ├───────────────────>│               │
     │                   │                    │               │
     │                   │                    │  Show error   │
     │                   │                    │  notification │
     │                   │                    ├──────────────>│
     │                   │                    │               │
     │                   │                    │  Display      │
     │                   │                    │  details      │
     │                   │                    │  and actions  │
     │                   │                    ├──────────────>│
     │                   │                    │               │
     │                   │                    │  User decides │
     │                   │                    │  (retry/cancel)│
     │                   │                    │<──────────────┤
```

---

## Key Contracts (Studs)

### Backend → Frontend

**REST Response Format**:
```json
{
  "data": { /* response data */ },
  "error": null
}
```

**Error Response Format**:
```json
{
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { /* additional context */ }
  }
}
```

**WebSocket Event Format**:
```json
{
  "type": "event.type",
  "job_id": "uuid",
  "timestamp": "ISO-8601",
  "data": { /* event-specific data */ }
}
```

### Frontend → Backend

**Execution Request Format**:
```json
{
  "scenario_id": "blog_writer",
  "parameters": {
    "idea": "/path/to/idea.md",
    "writings_dir": "/path/to/writings"
  },
  "options": {
    "verbose": true,
    "max_iterations": 10
  }
}
```

### CLI Tool → Backend

**Output Format Expectations**:
- Stage indicators: `📝 Doing something...`
- Progress: `Processing 3 of 10` or `[75%]`
- Completions: `✓ Task complete`
- Errors: `ERROR:` or `❌ Failed`

---

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                        Public Internet                      │
│                     (Future: Auth/TLS)                      │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│                    (Input Validation)                       │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                    Subprocess Boundary                      │
│                  (Process Isolation)                        │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                       CLI Tool Process                      │
│                (Limited Filesystem Access)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Backend Optimization Points

```
API Endpoint → Caching → Response
     │
     ├─> Scenario discovery: Cache for 5 minutes
     ├─> Execution status: No cache (always fresh)
     └─> Artifacts: Cache-Control headers

WebSocket → Connection Pool → Broadcast
     │
     ├─> Max connections: 100
     ├─> Heartbeat: Every 30s
     └─> Auto-reconnect: Client-side

Process → Resource Limits → Monitoring
     │
     ├─> Max concurrent: 10
     ├─> CPU limit: 2 cores per process
     └─> Memory limit: 2GB per process
```

### Frontend Optimization Points

```
Component → Memoization → Render
     │
     ├─> WorkflowViz: React.memo
     ├─> LogStream: Virtualized scrolling
     └─> StageCard: Memoize expensive calculations

State → Normalization → Updates
     │
     ├─> Executions: Map<id, Execution>
     ├─> Stages: Normalized by execution_id
     └─> Logs: Ring buffer (max 10,000 lines)

Assets → Code Splitting → Loading
     │
     ├─> Route-based chunks
     ├─> Component lazy loading
     └─> Image lazy loading
```

---

## Testing Strategy

### Backend Testing Pyramid

```
┌─────────────────────────┐
│   E2E Tests (~10%)      │  Full flow with real subprocess
├─────────────────────────┤
│   Integration (~30%)    │  API endpoints + services
├─────────────────────────┤
│   Unit Tests (~60%)     │  Individual functions
└─────────────────────────┘
```

### Frontend Testing Pyramid

```
┌─────────────────────────┐
│   E2E Tests (~10%)      │  Playwright/Cypress
├─────────────────────────┤
│   Integration (~30%)    │  Component + hooks
├─────────────────────────┤
│   Unit Tests (~60%)     │  Utils, formatters, parsers
└─────────────────────────┘
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Purpose**: Visual reference for system architecture
