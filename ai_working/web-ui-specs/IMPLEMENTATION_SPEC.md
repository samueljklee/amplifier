# Amplifier Web UI - Complete Implementation Specification

**Version**: 1.0  
**Date**: 2025-10-22  
**Purpose**: Detailed blueprint for building UX-focused Amplifier web interface

---

## Executive Summary

This specification defines a complete web UI for Amplifier that transforms CLI-based AI tools into beautiful, interactive web experiences. The system follows the "bricks and studs" philosophy with clear module boundaries and regeneratable components.

### Core Value Proposition

- **For Users**: Run complex AI workflows through intuitive web interface with real-time visualization
- **For Developers**: Clean API contracts enable independent frontend/backend development
- **For AI Generation**: Each module can be regenerated independently from this spec

### Key Design Principles

1. **Ruthless Simplicity**: Start with working MVP, add features only when justified
2. **Real-time UX**: Stream progress, visualize agent activity, show what's happening
3. **Scenario-Driven**: Interface auto-adapts to available CLI tools
4. **Modular & Regeneratable**: Each component is self-contained with clear contracts

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Structure](#module-structure)
3. [API Contract Specifications](#api-contract-specifications)
4. [Frontend Architecture](#frontend-architecture)
5. [Visualization Specifications](#visualization-specifications)
6. [Integration Points](#integration-points)
7. [Implementation Phases](#implementation-phases)
8. [Data Structures](#data-structures)

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Browser                          │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           React Frontend (Port 3000)                  │ │
│  │  - Scenario discovery and forms                       │ │
│  │  - Real-time workflow visualization                   │ │
│  │  - WebSocket event handling                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↕                                  │
│                    HTTP + WebSocket                         │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Backend (Port 8000)                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   REST API   │  │  WebSocket   │  │  Process Mgmt   │  │
│  │   Endpoints  │  │   Manager    │  │  (subprocess)   │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                          ↕                                  │
│                   Subprocess Execution                      │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│              Amplifier CLI Tools (scenarios/)               │
│  - blog_writer                                              │
│  - tips_synthesizer                                         │
│  - article_illustrator                                      │
│  - [auto-discovered from filesystem]                        │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend (Python)**
- FastAPI 0.104+ (async web framework)
- uvicorn (ASGI server)
- pydantic 2.0+ (data validation)
- asyncio (subprocess management)
- websockets (real-time events)

**Frontend (TypeScript + React)**
- React 18+ (UI framework)
- TypeScript 5+ (type safety)
- Vite (build tool, fast HMR)
- TanStack Query (server state management)
- Zustand (client state management)
- WebSocket API (real-time updates)
- Tailwind CSS (styling)
- Framer Motion (animations)

**Development Tools**
- ESLint + Prettier (code quality)
- pytest (backend testing)
- Vitest + React Testing Library (frontend testing)

---

## Module Structure

### Complete Directory Tree

```
amplifier-web-ui/
├── README.md                           # Setup and usage guide
├── pyproject.toml                      # Python dependencies (uv)
├── Makefile                            # Development commands
│
├── backend/                            # Python backend (FastAPI)
│   ├── __init__.py
│   ├── main.py                         # FastAPI app entrypoint (~150 lines)
│   ├── config.py                       # Configuration management (~80 lines)
│   │
│   ├── api/                            # REST API endpoints
│   │   ├── __init__.py
│   │   ├── scenarios.py                # Scenario discovery (~100 lines)
│   │   ├── execution.py                # Job execution control (~150 lines)
│   │   └── websocket.py                # WebSocket connection (~120 lines)
│   │
│   ├── models/                         # Pydantic models
│   │   ├── __init__.py
│   │   ├── scenario.py                 # Scenario metadata (~80 lines)
│   │   ├── execution.py                # Job execution models (~100 lines)
│   │   └── events.py                   # WebSocket event types (~60 lines)
│   │
│   ├── services/                       # Business logic
│   │   ├── __init__.py
│   │   ├── scenario_discovery.py       # Filesystem scanning (~200 lines)
│   │   ├── process_manager.py          # Subprocess orchestration (~250 lines)
│   │   ├── output_parser.py            # CLI output parsing (~150 lines)
│   │   └── event_broadcaster.py        # WebSocket broadcasting (~100 lines)
│   │
│   └── tests/                          # Backend tests
│       ├── __init__.py
│       ├── test_scenarios.py           # Scenario discovery tests (~100 lines)
│       ├── test_execution.py           # Execution tests (~150 lines)
│       └── fixtures/                   # Test fixtures
│           └── mock_scenarios/
│
├── frontend/                           # React frontend
│   ├── package.json                    # Node dependencies
│   ├── tsconfig.json                   # TypeScript config
│   ├── vite.config.ts                  # Vite build config
│   ├── index.html                      # Entry HTML
│   │
│   ├── src/
│   │   ├── main.tsx                    # React entrypoint (~30 lines)
│   │   ├── App.tsx                     # Root component (~80 lines)
│   │   │
│   │   ├── api/                        # Backend API client
│   │   │   ├── client.ts               # HTTP client setup (~50 lines)
│   │   │   ├── scenarios.ts            # Scenario endpoints (~80 lines)
│   │   │   ├── execution.ts            # Execution endpoints (~100 lines)
│   │   │   └── websocket.ts            # WebSocket client (~150 lines)
│   │   │
│   │   ├── components/                 # React components
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.tsx        # Main layout (~100 lines)
│   │   │   │   ├── Header.tsx          # Top navigation (~60 lines)
│   │   │   │   └── Sidebar.tsx         # Scenario navigation (~80 lines)
│   │   │   │
│   │   │   ├── scenarios/
│   │   │   │   ├── ScenarioList.tsx    # Scenario browser (~120 lines)
│   │   │   │   ├── ScenarioCard.tsx    # Scenario preview (~80 lines)
│   │   │   │   └── ScenarioForm.tsx    # Dynamic form builder (~200 lines)
│   │   │   │
│   │   │   ├── execution/
│   │   │   │   ├── ExecutionView.tsx   # Main execution UI (~150 lines)
│   │   │   │   ├── WorkflowViz.tsx     # Workflow visualizer (~250 lines)
│   │   │   │   ├── StageProgress.tsx   # Stage progress cards (~100 lines)
│   │   │   │   ├── LogStream.tsx       # Real-time log display (~120 lines)
│   │   │   │   └── OutputView.tsx      # Results display (~100 lines)
│   │   │   │
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx          # Button component (~40 lines)
│   │   │   │   ├── Input.tsx           # Input component (~60 lines)
│   │   │   │   ├── Card.tsx            # Card component (~50 lines)
│   │   │   │   ├── Badge.tsx           # Badge component (~40 lines)
│   │   │   │   ├── Spinner.tsx         # Loading spinner (~30 lines)
│   │   │   │   └── ErrorBoundary.tsx   # Error handling (~80 lines)
│   │   │   │
│   │   │   └── README.md               # Component documentation
│   │   │
│   │   ├── hooks/                      # Custom React hooks
│   │   │   ├── useScenarios.ts         # Scenario data fetching (~60 lines)
│   │   │   ├── useExecution.ts         # Execution management (~100 lines)
│   │   │   ├── useWebSocket.ts         # WebSocket connection (~120 lines)
│   │   │   └── useWorkflowState.ts     # Workflow state mgmt (~80 lines)
│   │   │
│   │   ├── stores/                     # Zustand stores
│   │   │   ├── executionStore.ts       # Execution state (~150 lines)
│   │   │   └── uiStore.ts              # UI state (~80 lines)
│   │   │
│   │   ├── types/                      # TypeScript types
│   │   │   ├── scenario.ts             # Scenario types (~100 lines)
│   │   │   ├── execution.ts            # Execution types (~120 lines)
│   │   │   └── events.ts               # Event types (~80 lines)
│   │   │
│   │   ├── utils/                      # Utility functions
│   │   │   ├── formatters.ts           # Data formatting (~80 lines)
│   │   │   ├── validators.ts           # Input validation (~60 lines)
│   │   │   └── parsers.ts              # Output parsing (~70 lines)
│   │   │
│   │   └── styles/                     # Global styles
│   │       ├── globals.css             # Global CSS + Tailwind
│   │       └── animations.css          # Custom animations
│   │
│   └── tests/                          # Frontend tests
│       ├── components/                 # Component tests
│       ├── hooks/                      # Hook tests
│       └── integration/                # Integration tests
│
├── docs/                               # Documentation
│   ├── API.md                          # API reference
│   ├── ARCHITECTURE.md                 # Architecture details
│   ├── DEPLOYMENT.md                   # Deployment guide
│   └── DEVELOPMENT.md                  # Development guide
│
└── .data/                              # Runtime data (gitignored)
    └── executions/                     # Execution artifacts
        └── <job_id>/                   # Per-job directory
            ├── stdout.log
            ├── stderr.log
            └── results/
```

### File Size Estimates Summary

**Backend**: ~2,000 lines total
- API endpoints: ~470 lines
- Services: ~700 lines
- Models: ~240 lines
- Tests: ~250 lines
- Config/Main: ~230 lines

**Frontend**: ~3,500 lines total
- Components: ~1,480 lines
- API/WebSocket: ~380 lines
- Hooks: ~360 lines
- Stores: ~230 lines
- Types: ~300 lines
- Utils: ~210 lines
- Tests: ~400 lines

**Total Codebase**: ~5,500 lines (small, maintainable, regeneratable)

---

## API Contract Specifications

### REST API Endpoints

All endpoints follow `/api/v1/` prefix convention.

#### 1. Scenario Discovery

**GET /api/v1/scenarios**

Discover all available CLI scenarios from filesystem.

```typescript
// Response
interface ScenariosResponse {
  scenarios: Scenario[];
  count: number;
}

interface Scenario {
  id: string;                    // e.g., "blog_writer"
  name: string;                  // e.g., "Blog Writer"
  description: string;           // From README.md
  path: string;                  // Relative to scenarios/
  cli_command: string;           // e.g., "python -m scenarios.blog_writer"
  
  parameters: Parameter[];       // Extracted from CLI
  examples: Example[];           // From README.md
  
  metadata: {
    version?: string;
    author?: string;
    tags: string[];              // e.g., ["writing", "ai", "content"]
  };
}

interface Parameter {
  name: string;                  // e.g., "idea"
  type: "string" | "path" | "directory" | "boolean" | "number";
  required: boolean;
  default?: any;
  description: string;
  validation?: {
    pattern?: string;            // Regex for validation
    min?: number;
    max?: number;
    choices?: string[];
  };
}

interface Example {
  title: string;
  description: string;
  command: string;
  input_files?: Record<string, string>;  // filename -> content
}
```

**Example Response**:
```json
{
  "scenarios": [
    {
      "id": "blog_writer",
      "name": "Blog Writer",
      "description": "Transform ideas into polished blog posts",
      "path": "scenarios/blog_writer",
      "cli_command": "python -m scenarios.blog_writer",
      "parameters": [
        {
          "name": "idea",
          "type": "path",
          "required": true,
          "description": "Path to idea markdown file"
        },
        {
          "name": "writings_dir",
          "type": "directory",
          "required": true,
          "description": "Directory with existing writings"
        },
        {
          "name": "instructions",
          "type": "string",
          "required": false,
          "description": "Additional instructions"
        }
      ],
      "examples": [
        {
          "title": "Basic Usage",
          "description": "Generate a blog post from rough idea",
          "command": "python -m scenarios.blog_writer --idea=idea.md --writings-dir=posts/"
        }
      ],
      "metadata": {
        "tags": ["writing", "ai", "blog"]
      }
    }
  ],
  "count": 1
}
```

**GET /api/v1/scenarios/{scenario_id}**

Get detailed information about a specific scenario.

```typescript
interface ScenarioDetailResponse {
  scenario: Scenario;
  readme: string;                // Full README.md content
  how_to_create?: string;        // HOW_TO_CREATE_YOUR_OWN.md if exists
}
```

#### 2. Execution Control

**POST /api/v1/executions**

Start a new scenario execution.

```typescript
interface ExecutionRequest {
  scenario_id: string;
  parameters: Record<string, any>;  // Parameter name -> value
  options?: {
    verbose?: boolean;
    max_iterations?: number;
    timeout?: number;              // Seconds
  };
}

interface ExecutionResponse {
  job_id: string;                  // UUID for this execution
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  scenario_id: string;
  created_at: string;              // ISO timestamp
  websocket_url: string;           // WebSocket URL for real-time updates
}
```

**Example Request**:
```json
{
  "scenario_id": "blog_writer",
  "parameters": {
    "idea": "/path/to/idea.md",
    "writings_dir": "/path/to/writings",
    "instructions": "Keep it under 1000 words"
  },
  "options": {
    "verbose": true,
    "max_iterations": 5
  }
}
```

**GET /api/v1/executions/{job_id}**

Get execution status and results.

```typescript
interface ExecutionStatusResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  scenario_id: string;
  
  created_at: string;
  started_at?: string;
  completed_at?: string;
  
  progress: {
    current_stage: string;         // e.g., "Extracting style"
    stage_number: number;          // e.g., 1
    total_stages: number;          // e.g., 5
    percentage: number;            // 0-100
  };
  
  output: {
    stdout: string[];              // Line-by-line stdout
    stderr: string[];              // Line-by-line stderr
    artifacts: Artifact[];         // Generated files
  };
  
  error?: {
    message: string;
    traceback?: string;
  };
}

interface Artifact {
  filename: string;
  path: string;
  size: number;
  content_type: string;
  url: string;                     // Download URL
  created_at: string;
}
```

**POST /api/v1/executions/{job_id}/cancel**

Cancel a running execution.

```typescript
interface CancelResponse {
  job_id: string;
  status: "cancelled";
  message: string;
}
```

**GET /api/v1/executions/{job_id}/artifacts/{filename}**

Download an artifact file.

Response: File download with appropriate Content-Type header.

**GET /api/v1/executions**

List all executions (with filtering).

```typescript
interface ExecutionListRequest {
  scenario_id?: string;
  status?: string;
  limit?: number;                  // Default: 50
  offset?: number;                 // Default: 0
}

interface ExecutionListResponse {
  executions: ExecutionStatusResponse[];
  total: number;
  limit: number;
  offset: number;
}
```

#### 3. Health & System

**GET /api/v1/health**

Health check endpoint.

```typescript
interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  uptime_seconds: number;
  active_executions: number;
}
```

**GET /api/v1/system/info**

System information.

```typescript
interface SystemInfoResponse {
  amplifier_version: string;
  python_version: string;
  scenarios_path: string;
  data_path: string;
}
```

### WebSocket Events

**Connection**: `ws://localhost:8000/api/v1/ws/{job_id}`

#### Client → Server Events

```typescript
// Subscribe to execution events
{
  type: "subscribe",
  job_id: string
}

// Unsubscribe from execution events
{
  type: "unsubscribe",
  job_id: string
}

// Ping to keep connection alive
{
  type: "ping"
}
```

#### Server → Client Events

```typescript
// Base event structure
interface WebSocketEvent {
  type: string;
  job_id: string;
  timestamp: string;              // ISO timestamp
  data: any;
}

// Execution started
{
  type: "execution.started",
  job_id: string,
  timestamp: string,
  data: {
    scenario_id: string,
    parameters: Record<string, any>
  }
}

// Stage changed
{
  type: "execution.stage_changed",
  job_id: string,
  timestamp: string,
  data: {
    stage: string,                // e.g., "Extracting style"
    stage_number: number,
    total_stages: number,
    description?: string
  }
}

// Progress update
{
  type: "execution.progress",
  job_id: string,
  timestamp: string,
  data: {
    percentage: number,           // 0-100
    message: string,              // e.g., "Processing 3 of 10 files"
    current_stage: string
  }
}

// Stdout/stderr line
{
  type: "execution.output",
  job_id: string,
  timestamp: string,
  data: {
    stream: "stdout" | "stderr",
    line: string
  }
}

// Artifact generated
{
  type: "execution.artifact",
  job_id: string,
  timestamp: string,
  data: {
    filename: string,
    path: string,
    size: number,
    url: string
  }
}

// Execution completed
{
  type: "execution.completed",
  job_id: string,
  timestamp: string,
  data: {
    status: "completed" | "failed" | "cancelled",
    artifacts: Artifact[],
    error?: {
      message: string,
      traceback?: string
    }
  }
}

// Error occurred
{
  type: "execution.error",
  job_id: string,
  timestamp: string,
  data: {
    error: string,
    stage?: string,
    recoverable: boolean
  }
}

// Connection confirmed
{
  type: "connection.established",
  timestamp: string,
  data: {
    message: string
  }
}

// Pong response
{
  type: "pong",
  timestamp: string
}
```

### Error Response Format

All error responses follow consistent structure:

```typescript
interface ErrorResponse {
  error: {
    code: string;                  // e.g., "SCENARIO_NOT_FOUND"
    message: string;               // Human-readable message
    details?: Record<string, any>; // Additional context
  };
  timestamp: string;
}
```

**Common Error Codes**:
- `SCENARIO_NOT_FOUND` - Scenario ID doesn't exist
- `INVALID_PARAMETERS` - Parameter validation failed
- `EXECUTION_NOT_FOUND` - Job ID doesn't exist
- `EXECUTION_FAILED` - Subprocess execution failed
- `WEBSOCKET_ERROR` - WebSocket connection issue
- `INTERNAL_ERROR` - Unexpected server error

**Example Error Response**:
```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Parameter 'idea' is required",
    "details": {
      "parameter": "idea",
      "expected_type": "path"
    }
  },
  "timestamp": "2025-10-22T10:30:00Z"
}
```

---

## Frontend Architecture

### Component Hierarchy

```
App
├── AppShell (Layout)
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   └── ThemeToggle
│   │
│   ├── Sidebar
│   │   ├── ScenarioList
│   │   │   └── ScenarioCard (multiple)
│   │   └── ActiveExecutions
│   │
│   └── MainContent (Router outlet)
│       ├── Home (route: /)
│       │   └── ScenarioList
│       │       └── ScenarioCard (multiple)
│       │
│       ├── ScenarioDetail (route: /scenarios/:id)
│       │   ├── ScenarioInfo
│       │   ├── ScenarioForm
│       │   │   ├── ParameterInput (multiple)
│       │   │   └── SubmitButton
│       │   └── ExamplesList
│       │
│       └── ExecutionView (route: /executions/:jobId)
│           ├── ExecutionHeader
│           │   ├── StatusBadge
│           │   ├── ProgressBar
│           │   └── CancelButton
│           │
│           ├── WorkflowViz
│           │   ├── StageNode (multiple)
│           │   ├── StageConnector (multiple)
│           │   └── CurrentStageIndicator
│           │
│           ├── StageProgress
│           │   └── StageCard (multiple)
│           │       ├── StageName
│           │       ├── StageStatus
│           │       └── StageTimeline
│           │
│           ├── LogStream
│           │   ├── LogLine (virtualized list)
│           │   ├── LogFilter
│           │   └── AutoScrollToggle
│           │
│           └── OutputView
│               ├── ArtifactsList
│               │   └── ArtifactCard (multiple)
│               │       ├── FileIcon
│               │       ├── Filename
│               │       └── DownloadButton
│               └── ResultsPreview
```

### State Management Strategy

#### Server State (TanStack Query)

Manages data from backend API with automatic caching, refetching, and synchronization.

```typescript
// Query keys
const queryKeys = {
  scenarios: ['scenarios'] as const,
  scenario: (id: string) => ['scenarios', id] as const,
  executions: (filters?: ExecutionFilters) => ['executions', filters] as const,
  execution: (jobId: string) => ['executions', jobId] as const,
};

// Example query hook
function useScenarios() {
  return useQuery({
    queryKey: queryKeys.scenarios,
    queryFn: fetchScenarios,
    staleTime: 5 * 60 * 1000,      // 5 minutes
  });
}

function useExecution(jobId: string) {
  return useQuery({
    queryKey: queryKeys.execution(jobId),
    queryFn: () => fetchExecution(jobId),
    refetchInterval: (data) => 
      data?.status === 'running' ? 2000 : false,  // Poll every 2s while running
  });
}
```

#### Client State (Zustand)

Manages local UI state and WebSocket-driven real-time updates.

```typescript
// Execution store
interface ExecutionStore {
  // State
  activeExecutions: Map<string, ExecutionState>;
  selectedJobId: string | null;
  
  // Actions
  addExecution: (jobId: string, execution: ExecutionState) => void;
  updateExecution: (jobId: string, update: Partial<ExecutionState>) => void;
  removeExecution: (jobId: string) => void;
  selectExecution: (jobId: string | null) => void;
  
  // WebSocket events
  handleEvent: (event: WebSocketEvent) => void;
}

interface ExecutionState {
  jobId: string;
  status: ExecutionStatus;
  progress: ProgressState;
  stages: StageState[];
  output: OutputState;
  error?: ErrorState;
}

interface ProgressState {
  currentStage: string;
  stageNumber: number;
  totalStages: number;
  percentage: number;
}

interface StageState {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  message?: string;
}

interface OutputState {
  stdout: string[];
  stderr: string[];
  artifacts: Artifact[];
}

// UI store
interface UIStore {
  // State
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  logFilters: LogFilters;
  
  // Actions
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setLogFilters: (filters: LogFilters) => void;
}
```

### Routing Structure

```typescript
const routes = [
  {
    path: '/',
    element: <Home />,
    // Displays scenario list/grid
  },
  {
    path: '/scenarios/:scenarioId',
    element: <ScenarioDetail />,
    // Shows scenario info and parameter form
  },
  {
    path: '/executions/:jobId',
    element: <ExecutionView />,
    // Real-time execution visualization
  },
  {
    path: '/executions',
    element: <ExecutionList />,
    // List all past/active executions
  },
  {
    path: '*',
    element: <NotFound />,
  },
];
```

### Custom Hooks

#### useScenarios

```typescript
function useScenarios() {
  const query = useQuery({
    queryKey: ['scenarios'],
    queryFn: api.scenarios.list,
  });
  
  return {
    scenarios: query.data?.scenarios ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
```

#### useExecution

```typescript
function useExecution(jobId: string) {
  const query = useQuery({
    queryKey: ['executions', jobId],
    queryFn: () => api.executions.get(jobId),
    refetchInterval: (data) => 
      data?.status === 'running' ? 2000 : false,
  });
  
  const cancelMutation = useMutation({
    mutationFn: () => api.executions.cancel(jobId),
    onSuccess: () => query.refetch(),
  });
  
  return {
    execution: query.data,
    isLoading: query.isLoading,
    error: query.error,
    cancel: cancelMutation.mutate,
    isCancelling: cancelMutation.isLoading,
  };
}
```

#### useWebSocket

```typescript
function useWebSocket(jobId: string) {
  const store = useExecutionStore();
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${jobId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ type: 'subscribe', job_id: jobId }));
    };
    
    ws.onmessage = (event) => {
      const wsEvent = JSON.parse(event.data);
      store.handleEvent(wsEvent);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
    };
    
    // Ping every 30s to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [jobId]);
  
  return { isConnected };
}
```

#### useWorkflowState

```typescript
function useWorkflowState(jobId: string) {
  const execution = useExecutionStore(
    (state) => state.activeExecutions.get(jobId)
  );
  
  const currentStage = execution?.stages.find(s => s.status === 'active');
  const completedStages = execution?.stages.filter(s => s.status === 'completed') ?? [];
  const failedStages = execution?.stages.filter(s => s.status === 'failed') ?? [];
  
  return {
    execution,
    currentStage,
    completedStages,
    failedStages,
    isRunning: execution?.status === 'running',
    isCompleted: execution?.status === 'completed',
    isFailed: execution?.status === 'failed',
  };
}
```

---

## Visualization Specifications

### Workflow Visualization Component

The WorkflowViz component is the centerpiece of the execution view, providing real-time visual feedback of the AI workflow progress.

#### Design Philosophy

- **Spatial layout**: Horizontal flow (left → right) showing progression
- **Clear states**: Visual distinction between pending, active, completed, failed
- **Real-time updates**: Smooth animations as stages progress
- **Contextual information**: Tooltips and expanding details

#### Visual Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        Workflow Visualization                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│  │ Extract  │─────▶│  Draft   │─────▶│  Review  │              │
│  │  Style   │      │  Content │      │  Sources │              │
│  │          │      │          │      │          │              │
│  │    ✓     │      │    ⟳     │      │    ○     │              │
│  │  2.3s    │      │  15.1s   │      │    —     │              │
│  └──────────┘      └──────────┘      └──────────┘              │
│   Completed         In Progress        Pending                 │
│                                                                 │
│  [Progress: 40%] [Stage 2 of 5] [Elapsed: 17.4s]              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Stage Node States

```typescript
interface StageVisual {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  icon: ReactNode;
  color: string;
  animation: string;
}

const stageVisuals: Record<StageStatus, StageVisual> = {
  pending: {
    status: 'pending',
    icon: <CircleIcon />,
    color: 'gray',
    animation: 'none',
  },
  active: {
    status: 'active',
    icon: <SpinnerIcon />,
    color: 'blue',
    animation: 'pulse',
  },
  completed: {
    status: 'completed',
    icon: <CheckIcon />,
    color: 'green',
    animation: 'scale-in',
  },
  failed: {
    status: 'failed',
    icon: <XIcon />,
    color: 'red',
    animation: 'shake',
  },
};
```

#### Component Props

```typescript
interface WorkflowVizProps {
  jobId: string;
  stages: StageState[];
  currentStageIndex: number;
  progress: number;              // 0-100
  onStageClick?: (stage: StageState) => void;
}

interface StageNodeProps {
  stage: StageState;
  index: number;
  isActive: boolean;
  onClick?: () => void;
}

interface StageConnectorProps {
  fromStatus: StageStatus;
  toStatus: StageStatus;
  animated: boolean;
}
```

#### Animation Specifications

**Stage Transition Animations**:

```css
/* Stage activation */
@keyframes stage-activate {
  0% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

/* Stage completion */
@keyframes stage-complete {
  0% { transform: scale(1); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

/* Active stage pulse */
@keyframes stage-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
}

/* Connector flow */
@keyframes connector-flow {
  0% { stroke-dashoffset: 24; }
  100% { stroke-dashoffset: 0; }
}
```

**Apply to components**:

```tsx
const StageNode: React.FC<StageNodeProps> = ({ stage, isActive }) => {
  return (
    <motion.div
      className="stage-node"
      initial={false}
      animate={{
        scale: isActive ? [1, 1.05, 1] : 1,
        boxShadow: isActive 
          ? ['0 0 0 0 rgba(59,130,246,0.7)', '0 0 0 10px rgba(59,130,246,0)', '0 0 0 0 rgba(59,130,246,0.7)']
          : 'none',
      }}
      transition={{
        duration: 2,
        repeat: isActive ? Infinity : 0,
      }}
    >
      {/* Stage content */}
    </motion.div>
  );
};
```

### Stage Progress Cards

Below the workflow visualization, detailed cards show information about each stage.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Stage Details                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │ ✓ Extract Style          │  │ ⟳ Draft Content          │    │
│  │                          │  │                          │    │
│  │ Analyzed 5 blog posts    │  │ Generating blog draft    │    │
│  │ Identified tone: casual  │  │ Using extracted style    │    │
│  │                          │  │                          │    │
│  │ Duration: 2.3s           │  │ Elapsed: 15.1s           │    │
│  │ Status: Completed        │  │ Status: In Progress      │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Component Structure

```typescript
interface StageCardProps {
  stage: StageState;
  expanded?: boolean;
  onToggleExpand?: () => void;
}

interface StageState {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  duration?: number;           // seconds
  message?: string;
  details?: {
    filesProcessed?: number;
    linesGenerated?: number;
    tokensUsed?: number;
    errors?: string[];
  };
}
```

### Log Stream Component

Real-time display of stdout/stderr with filtering and auto-scroll.

```
┌─────────────────────────────────────────────────────────────────┐
│  Execution Log                           [Filter] [Auto-scroll] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  10:32:15 | INFO  | Starting blog writer pipeline              │
│  10:32:15 | INFO  | Session: 20251022_103215                   │
│  10:32:16 | INFO  | 📝 Extracting author's style...            │
│  10:32:17 | DEBUG | Found 5 writing samples                    │
│  10:32:18 | INFO  | ✓ Style extraction complete                │
│  10:32:18 | INFO  | ✍️ Writing initial blog draft...           │
│  10:32:33 | INFO  | ✓ Draft generation complete                │
│  10:32:33 | INFO  | 🔍 Reviewing source accuracy...            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Features

- **Virtualized scrolling**: Handle 10,000+ log lines without performance issues
- **Syntax highlighting**: Color-code log levels (INFO, DEBUG, ERROR, etc.)
- **Filtering**: Filter by log level or text search
- **Auto-scroll**: Automatically scroll to bottom as new logs arrive (toggleable)
- **Copy/download**: Copy selected lines or download full log

#### Component Props

```typescript
interface LogStreamProps {
  jobId: string;
  lines: LogLine[];
  filters?: LogFilters;
  onFilterChange?: (filters: LogFilters) => void;
  autoScroll?: boolean;
  onAutoScrollChange?: (enabled: boolean) => void;
}

interface LogLine {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  stream: 'stdout' | 'stderr';
}

interface LogFilters {
  levels: Set<string>;           // Which levels to show
  search: string;                // Text search
  stream?: 'stdout' | 'stderr';  // Which stream
}
```

### Output/Artifacts View

Display generated files and results.

```
┌─────────────────────────────────────────────────────────────────┐
│  Generated Artifacts                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📄 transforming-ideas-into-blog-posts.md                │   │
│  │ Final blog post                                         │   │
│  │ 1,234 words · 8.5 KB · Created 2 minutes ago           │   │
│  │ [Preview] [Download] [Copy Path]                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📄 draft_iter_1.md                                      │   │
│  │ First iteration draft                                   │   │
│  │ 1,150 words · 7.8 KB · Created 5 minutes ago           │   │
│  │ [Preview] [Download] [Copy Path]                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Component Props

```typescript
interface OutputViewProps {
  jobId: string;
  artifacts: Artifact[];
  onPreview?: (artifact: Artifact) => void;
  onDownload?: (artifact: Artifact) => void;
}

interface ArtifactCardProps {
  artifact: Artifact;
  onPreview?: () => void;
  onDownload?: () => void;
}

interface Artifact {
  filename: string;
  path: string;
  size: number;                  // bytes
  contentType: string;
  url: string;                   // download URL
  createdAt: string;
  metadata?: {
    wordCount?: number;
    lineCount?: number;
    description?: string;
  };
}
```

---

## Integration Points

### 1. Scenario Discovery Integration

**How frontend discovers scenarios:**

```typescript
// Frontend: api/scenarios.ts
async function fetchScenarios(): Promise<Scenario[]> {
  const response = await fetch('/api/v1/scenarios');
  const data = await response.json();
  return data.scenarios;
}

// Backend: services/scenario_discovery.py
class ScenarioDiscovery:
    def discover_scenarios(self, scenarios_path: Path) -> list[Scenario]:
        scenarios = []
        for scenario_dir in scenarios_path.iterdir():
            if not scenario_dir.is_dir():
                continue
            
            scenario = self._parse_scenario(scenario_dir)
            if scenario:
                scenarios.append(scenario)
        
        return scenarios
    
    def _parse_scenario(self, scenario_dir: Path) -> Scenario | None:
        # 1. Read README.md for description and examples
        readme = scenario_dir / "README.md"
        if not readme.exists():
            return None
        
        # 2. Extract CLI parameters from main.py or cli.py
        cli_module = self._find_cli_module(scenario_dir)
        parameters = self._extract_parameters(cli_module)
        
        # 3. Build scenario metadata
        return Scenario(
            id=scenario_dir.name,
            name=self._format_name(scenario_dir.name),
            description=self._extract_description(readme),
            path=str(scenario_dir),
            cli_command=f"python -m scenarios.{scenario_dir.name}",
            parameters=parameters,
            examples=self._extract_examples(readme),
        )
```

**Parameter extraction strategy:**

```python
def _extract_parameters(self, cli_module: Path) -> list[Parameter]:
    # Parse CLI module to extract Click options
    # Look for @click.option decorators
    
    import ast
    tree = ast.parse(cli_module.read_text())
    
    parameters = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if self._is_click_option(node):
                param = self._parse_click_option(node)
                parameters.append(param)
    
    return parameters
```

### 2. CLI Execution Integration

**How to execute CLI tools via subprocess:**

```python
# Backend: services/process_manager.py
import asyncio
import uuid
from pathlib import Path
from typing import AsyncIterator

class ProcessManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.processes: dict[str, asyncio.subprocess.Process] = {}
    
    async def start_execution(
        self,
        scenario_id: str,
        cli_command: str,
        parameters: dict[str, any],
        event_broadcaster: EventBroadcaster,
    ) -> str:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create execution directory
        execution_dir = self.data_dir / "executions" / job_id
        execution_dir.mkdir(parents=True, exist_ok=True)
        
        # Build command
        cmd = self._build_command(cli_command, parameters)
        
        # Start subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=execution_dir,
        )
        
        self.processes[job_id] = process
        
        # Stream output in background
        asyncio.create_task(
            self._stream_output(job_id, process, event_broadcaster)
        )
        
        # Broadcast started event
        await event_broadcaster.broadcast(job_id, {
            "type": "execution.started",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "scenario_id": scenario_id,
                "parameters": parameters,
            },
        })
        
        return job_id
    
    async def _stream_output(
        self,
        job_id: str,
        process: asyncio.subprocess.Process,
        event_broadcaster: EventBroadcaster,
    ):
        # Stream stdout
        async def stream_stdout():
            async for line in process.stdout:
                line_str = line.decode().rstrip()
                await event_broadcaster.broadcast(job_id, {
                    "type": "execution.output",
                    "job_id": job_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "stream": "stdout",
                        "line": line_str,
                    },
                })
                
                # Parse for stage changes
                stage_info = self._parse_stage_change(line_str)
                if stage_info:
                    await event_broadcaster.broadcast(job_id, {
                        "type": "execution.stage_changed",
                        "job_id": job_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": stage_info,
                    })
        
        # Stream stderr
        async def stream_stderr():
            async for line in process.stderr:
                line_str = line.decode().rstrip()
                await event_broadcaster.broadcast(job_id, {
                    "type": "execution.output",
                    "job_id": job_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "stream": "stderr",
                        "line": line_str,
                    },
                })
        
        # Run both concurrently
        await asyncio.gather(
            stream_stdout(),
            stream_stderr(),
        )
        
        # Wait for process to complete
        await process.wait()
        
        # Broadcast completion
        await event_broadcaster.broadcast(job_id, {
            "type": "execution.completed",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "status": "completed" if process.returncode == 0 else "failed",
                "exit_code": process.returncode,
            },
        })
```

### 3. Output Parsing Integration

**How to parse CLI output for stage detection:**

```python
# Backend: services/output_parser.py
import re
from typing import Optional

class OutputParser:
    # Common stage indicators from Amplifier CLI tools
    STAGE_PATTERNS = [
        r"📝\s+(?P<stage>.*?)\.\.\.?",              # Emoji prefix
        r"✍️\s+(?P<stage>.*?)\.\.\.?",
        r"🔍\s+(?P<stage>.*?)\.\.\.?",
        r"INFO.*?(?P<stage>Extracting|Writing|Reviewing|Processing).*?",
        r"Starting\s+(?P<stage>.*?)\s+stage",
    ]
    
    PROGRESS_PATTERNS = [
        r"Processing\s+(?P<current>\d+)\s+of\s+(?P<total>\d+)",
        r"\[(?P<percent>\d+)%\]",
        r"(?P<current>\d+)/(?P<total>\d+)\s+(?:complete|done)",
    ]
    
    def parse_stage_change(self, line: str) -> Optional[dict]:
        for pattern in self.STAGE_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {
                    "stage": match.group("stage").strip(),
                }
        return None
    
    def parse_progress(self, line: str) -> Optional[dict]:
        for pattern in self.PROGRESS_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                
                # Calculate percentage
                if "percent" in groups:
                    percentage = int(groups["percent"])
                elif "current" in groups and "total" in groups:
                    current = int(groups["current"])
                    total = int(groups["total"])
                    percentage = int((current / total) * 100)
                else:
                    continue
                
                return {
                    "percentage": percentage,
                    "message": line.strip(),
                }
        
        return None
    
    def extract_artifacts(self, execution_dir: Path) -> list[Artifact]:
        artifacts = []
        
        # Common output patterns
        output_patterns = [
            "*.md",
            "*.json",
            "*.txt",
            "*.html",
            "results/*",
        ]
        
        for pattern in output_patterns:
            for file_path in execution_dir.glob(pattern):
                if file_path.is_file():
                    artifacts.append(Artifact(
                        filename=file_path.name,
                        path=str(file_path.relative_to(execution_dir)),
                        size=file_path.stat().st_size,
                        content_type=self._guess_content_type(file_path),
                        url=f"/api/v1/executions/{execution_dir.name}/artifacts/{file_path.name}",
                        created_at=datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    ))
        
        return artifacts
```

### 4. File Input Handling

**How to handle file/directory parameters:**

Frontend provides file upload or path selection:

```typescript
// Frontend: components/scenarios/ParameterInput.tsx
interface FileParameterInputProps {
  parameter: Parameter;
  value: string;
  onChange: (value: string) => void;
}

function FileParameterInput({ parameter, value, onChange }: FileParameterInputProps) {
  const [uploadMode, setUploadMode] = useState<'path' | 'upload'>('path');
  
  const handleFileUpload = async (files: FileList) => {
    // Upload file to backend, get temporary path
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append('files', file));
    
    const response = await fetch('/api/v1/files/upload', {
      method: 'POST',
      body: formData,
    });
    
    const { path } = await response.json();
    onChange(path);
  };
  
  return (
    <div className="parameter-input">
      <label>{parameter.name}</label>
      
      <div className="input-mode-toggle">
        <button onClick={() => setUploadMode('path')}>Use Path</button>
        <button onClick={() => setUploadMode('upload')}>Upload</button>
      </div>
      
      {uploadMode === 'path' ? (
        <input
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder="/path/to/file"
        />
      ) : (
        <input
          type="file"
          onChange={e => e.target.files && handleFileUpload(e.target.files)}
          multiple={parameter.type === 'directory'}
        />
      )}
    </div>
  );
}
```

Backend handles file uploads:

```python
# Backend: api/files.py
from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/api/v1/files")

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    # Create temporary directory for uploaded files
    temp_dir = Path(".data/uploads") / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        file_path = temp_dir / file.filename
        with file_path.open("wb") as f:
            f.write(await file.read())
    
    return {
        "path": str(temp_dir),
        "files": [f.filename for f in files],
    }
```

---

## Implementation Phases

### Phase 1: MVP (Core Functionality) - Week 1

**Goal**: Working end-to-end flow with minimal UI

**Backend Deliverables**:
1. ✅ FastAPI server setup with health endpoint
2. ✅ Scenario discovery endpoint (basic - just list scenarios from filesystem)
3. ✅ Execution endpoint (start subprocess, return job_id)
4. ✅ Basic WebSocket connection (broadcast stdout/stderr)
5. ✅ Process manager (start/stop subprocesses)

**Frontend Deliverables**:
1. ✅ React app scaffold with routing
2. ✅ Scenario list page (fetch and display)
3. ✅ Simple scenario form (text inputs only)
4. ✅ Basic execution view (show stdout stream)
5. ✅ WebSocket connection (receive and display events)

**Success Criteria**:
- Can browse available scenarios
- Can start a scenario with text parameters
- Can see real-time log output
- Can see when execution completes

**Testing**:
- Manual testing with `blog_writer` scenario
- Verify WebSocket reconnection on disconnect
- Check process cleanup on cancellation

**Estimated Effort**: 40-50 hours total
- Backend: 20-25 hours
- Frontend: 20-25 hours

---

### Phase 2: Enhanced UX - Week 2

**Goal**: Polish UI, add visualization, improve parameter handling

**Backend Deliverables**:
1. ✅ Enhanced scenario discovery (parse CLI parameters, extract README)
2. ✅ Output parsing (detect stages, progress, artifacts)
3. ✅ Artifact download endpoint
4. ✅ File upload endpoint
5. ✅ Execution listing/history endpoint
6. ✅ Better error handling and validation

**Frontend Deliverables**:
1. ✅ Workflow visualization component
2. ✅ Stage progress cards
3. ✅ Dynamic form builder (handle file/directory inputs)
4. ✅ Artifact viewer with preview/download
5. ✅ Execution history page
6. ✅ Better error handling and user feedback
7. ✅ Loading states and skeletons

**Success Criteria**:
- Parameters auto-populate from CLI introspection
- Visual workflow shows current stage
- Can upload files for file parameters
- Can download generated artifacts
- Can see past execution history
- Clear error messages when things fail

**Testing**:
- Test with all existing scenarios (blog_writer, tips_synthesizer, article_illustrator)
- Test file uploads with various file types
- Test long-running executions (>5 minutes)
- Test WebSocket reconnection during execution

**Estimated Effort**: 50-60 hours total
- Backend: 25-30 hours
- Frontend: 25-30 hours

---

### Phase 3: Polish & Enhancement - Week 3

**Goal**: Production-ready with polished UX and advanced features

**Backend Deliverables**:
1. ✅ Execution cancellation
2. ✅ Improved output parsing (more patterns)
3. ✅ Execution filtering/search
4. ✅ Metrics/analytics endpoint
5. ✅ Configuration management
6. ✅ Comprehensive error handling
7. ✅ API documentation (OpenAPI/Swagger)

**Frontend Deliverables**:
1. ✅ Dark mode
2. ✅ Log filtering and search
3. ✅ Virtualized log scrolling (for large logs)
4. ✅ Markdown preview for artifacts
5. ✅ Keyboard shortcuts
6. ✅ Improved animations and transitions
7. ✅ Responsive design (mobile-friendly)
8. ✅ Accessibility improvements (ARIA labels, keyboard nav)
9. ✅ User preferences (persist settings)

**Success Criteria**:
- Fast and smooth UI (60fps animations)
- Handles logs with 10,000+ lines without lag
- Works well on tablet/mobile devices
- Keyboard navigation works throughout
- Passes basic accessibility audit
- User preferences persist across sessions

**Testing**:
- Performance testing (large logs, many artifacts)
- Accessibility testing (screen reader, keyboard-only)
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile testing (iOS Safari, Chrome Android)
- Load testing (multiple concurrent executions)

**Estimated Effort**: 40-50 hours total
- Backend: 15-20 hours
- Frontend: 25-30 hours

---

### Phase 4: Advanced Features (Optional) - Week 4+

**Goal**: Power user features and advanced workflows

**Potential Features**:
1. Execution templates (save parameter sets)
2. Batch execution (run multiple scenarios sequentially)
3. Execution comparison (diff outputs)
4. Scheduled executions
5. Execution sharing (share results via link)
6. Plugin system (custom visualizations per scenario)
7. Collaborative features (multi-user support)
8. Execution branching (retry with modified parameters)

**Implementation Priority**: User-driven based on feedback

---

## Data Structures

### Backend Models (Pydantic)

```python
# models/scenario.py
from pydantic import BaseModel, Field

class Parameter(BaseModel):
    name: str
    type: Literal["string", "path", "directory", "boolean", "number"]
    required: bool
    default: Optional[Any] = None
    description: str
    validation: Optional[dict] = None

class Example(BaseModel):
    title: str
    description: str
    command: str
    input_files: Optional[dict[str, str]] = None

class ScenarioMetadata(BaseModel):
    version: Optional[str] = None
    author: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

class Scenario(BaseModel):
    id: str
    name: str
    description: str
    path: str
    cli_command: str
    parameters: list[Parameter]
    examples: list[Example]
    metadata: ScenarioMetadata

# models/execution.py
class ExecutionRequest(BaseModel):
    scenario_id: str
    parameters: dict[str, Any]
    options: Optional[dict[str, Any]] = None

class ProgressState(BaseModel):
    current_stage: str
    stage_number: int
    total_stages: int
    percentage: int = Field(ge=0, le=100)

class Artifact(BaseModel):
    filename: str
    path: str
    size: int
    content_type: str
    url: str
    created_at: str

class ExecutionOutput(BaseModel):
    stdout: list[str]
    stderr: list[str]
    artifacts: list[Artifact]

class ExecutionError(BaseModel):
    message: str
    traceback: Optional[str] = None

class ExecutionStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    scenario_id: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: ProgressState
    output: ExecutionOutput
    error: Optional[ExecutionError] = None

# models/events.py
class WebSocketEvent(BaseModel):
    type: str
    job_id: str
    timestamp: str
    data: dict[str, Any]
```

### Frontend Types (TypeScript)

```typescript
// types/scenario.ts
export type ParameterType = 'string' | 'path' | 'directory' | 'boolean' | 'number';

export interface Parameter {
  name: string;
  type: ParameterType;
  required: boolean;
  default?: any;
  description: string;
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    choices?: string[];
  };
}

export interface Example {
  title: string;
  description: string;
  command: string;
  input_files?: Record<string, string>;
}

export interface ScenarioMetadata {
  version?: string;
  author?: string;
  tags: string[];
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  path: string;
  cli_command: string;
  parameters: Parameter[];
  examples: Example[];
  metadata: ScenarioMetadata;
}

// types/execution.ts
export type ExecutionStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type StageStatus = 'pending' | 'active' | 'completed' | 'failed';
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';

export interface ExecutionRequest {
  scenario_id: string;
  parameters: Record<string, any>;
  options?: {
    verbose?: boolean;
    max_iterations?: number;
    timeout?: number;
  };
}

export interface ProgressState {
  current_stage: string;
  stage_number: number;
  total_stages: number;
  percentage: number;
}

export interface Artifact {
  filename: string;
  path: string;
  size: number;
  content_type: string;
  url: string;
  created_at: string;
  metadata?: {
    wordCount?: number;
    lineCount?: number;
    description?: string;
  };
}

export interface ExecutionOutput {
  stdout: string[];
  stderr: string[];
  artifacts: Artifact[];
}

export interface ExecutionError {
  message: string;
  traceback?: string;
}

export interface Execution {
  job_id: string;
  status: ExecutionStatus;
  scenario_id: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress: ProgressState;
  output: ExecutionOutput;
  error?: ExecutionError;
}

export interface StageState {
  name: string;
  status: StageStatus;
  startTime?: string;
  endTime?: string;
  duration?: number;
  message?: string;
  details?: {
    filesProcessed?: number;
    linesGenerated?: number;
    tokensUsed?: number;
    errors?: string[];
  };
}

export interface LogLine {
  timestamp: string;
  level: LogLevel;
  message: string;
  stream: 'stdout' | 'stderr';
}

// types/events.ts
export interface WebSocketEvent {
  type: string;
  job_id: string;
  timestamp: string;
  data: any;
}

export interface ExecutionStartedEvent extends WebSocketEvent {
  type: 'execution.started';
  data: {
    scenario_id: string;
    parameters: Record<string, any>;
  };
}

export interface StageChangedEvent extends WebSocketEvent {
  type: 'execution.stage_changed';
  data: {
    stage: string;
    stage_number: number;
    total_stages: number;
    description?: string;
  };
}

export interface ProgressEvent extends WebSocketEvent {
  type: 'execution.progress';
  data: {
    percentage: number;
    message: string;
    current_stage: string;
  };
}

export interface OutputEvent extends WebSocketEvent {
  type: 'execution.output';
  data: {
    stream: 'stdout' | 'stderr';
    line: string;
  };
}

export interface ArtifactEvent extends WebSocketEvent {
  type: 'execution.artifact';
  data: {
    filename: string;
    path: string;
    size: number;
    url: string;
  };
}

export interface CompletedEvent extends WebSocketEvent {
  type: 'execution.completed';
  data: {
    status: 'completed' | 'failed' | 'cancelled';
    artifacts: Artifact[];
    error?: {
      message: string;
      traceback?: string;
    };
  };
}

export interface ErrorEvent extends WebSocketEvent {
  type: 'execution.error';
  data: {
    error: string;
    stage?: string;
    recoverable: boolean;
  };
}
```

### State Management Types

```typescript
// stores/executionStore.ts
export interface ExecutionStore {
  // State
  activeExecutions: Map<string, ExecutionState>;
  selectedJobId: string | null;
  
  // Actions
  addExecution: (jobId: string, execution: ExecutionState) => void;
  updateExecution: (jobId: string, update: Partial<ExecutionState>) => void;
  removeExecution: (jobId: string) => void;
  selectExecution: (jobId: string | null) => void;
  handleEvent: (event: WebSocketEvent) => void;
  reset: () => void;
}

export interface ExecutionState {
  jobId: string;
  status: ExecutionStatus;
  progress: ProgressState;
  stages: StageState[];
  output: {
    stdout: string[];
    stderr: string[];
    artifacts: Artifact[];
  };
  error?: {
    message: string;
    traceback?: string;
  };
  metadata: {
    scenarioId: string;
    parameters: Record<string, any>;
    createdAt: string;
    startedAt?: string;
    completedAt?: string;
  };
}

// stores/uiStore.ts
export interface UIStore {
  // State
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  logFilters: LogFilters;
  preferences: UserPreferences;
  
  // Actions
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setLogFilters: (filters: LogFilters) => void;
  setPreferences: (prefs: Partial<UserPreferences>) => void;
  reset: () => void;
}

export interface LogFilters {
  levels: Set<LogLevel>;
  search: string;
  stream?: 'stdout' | 'stderr';
}

export interface UserPreferences {
  autoScroll: boolean;
  showTimestamps: boolean;
  fontSize: 'small' | 'medium' | 'large';
  animationsEnabled: boolean;
}
```

---

## Appendix: Key Decisions & Rationales

### Why FastAPI?

- Modern, async Python web framework
- Automatic OpenAPI documentation
- Pydantic integration for type safety
- Excellent WebSocket support
- Fast development with auto-reload

### Why React + TypeScript?

- Industry standard for complex UIs
- TypeScript provides type safety and better DX
- Large ecosystem of libraries
- Excellent tooling and debugging

### Why Vite over Create React App?

- Much faster HMR (Hot Module Replacement)
- Modern build tooling (ESBuild)
- Better TypeScript support out of the box
- Smaller bundle sizes

### Why TanStack Query?

- Best-in-class server state management
- Automatic caching and refetching
- Optimistic updates support
- Excellent DevTools

### Why Zustand over Redux?

- Much simpler API
- Less boilerplate
- Better TypeScript support
- Sufficient for our state needs

### Why WebSockets over SSE?

- Bi-directional communication (can send commands to server)
- Better browser support
- More flexible event model
- Can handle binary data if needed later

### Why subprocess over library imports?

- **Isolation**: Each execution runs in clean environment
- **Safety**: Can't crash main server process
- **Compatibility**: Works with any CLI tool
- **Resource management**: Easier to limit CPU/memory per execution
- **User perspective**: Maintains CLI-first philosophy

---

## Next Steps

1. **Review this spec** - Ensure it aligns with vision
2. **Prioritize features** - Confirm Phase 1-3 breakdown
3. **Set up project structure** - Create directories and scaffolding
4. **Start Phase 1** - Delegate to modular-builder agent

---

**Document Status**: Draft v1.0  
**Ready for**: Implementation by modular-builder agent  
**Estimated Total Effort**: 130-160 hours across 3 phases  
**Target Timeline**: 3-4 weeks for production-ready MVP
