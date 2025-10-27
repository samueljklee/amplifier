# Amplifier Web UI Implementation Specifications

**Complete blueprint for building the Amplifier web interface**

---

## What's Here

This directory contains the complete implementation specifications for the Amplifier Web UI - a UX-focused web interface that makes CLI-based AI tools accessible through a beautiful, real-time browser experience.

### Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| **[IMPLEMENTATION_SPEC.md](./IMPLEMENTATION_SPEC.md)** | Complete technical specification (1,000+ lines) | Implementers, architects |
| **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** | Quick lookup guide for common tasks | Developers |
| **[ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)** | Visual system architecture | Everyone |

---

## Quick Start

### For Architects

Read **IMPLEMENTATION_SPEC.md** sections:
1. Architecture Overview
2. Module Structure
3. API Contract Specifications
4. Implementation Phases

### For Implementers

1. Read **QUICK_REFERENCE.md** for context
2. Reference **IMPLEMENTATION_SPEC.md** for your module
3. Use **ARCHITECTURE_DIAGRAM.md** to understand data flow
4. Follow the "bricks and studs" philosophy

### For Product/UX

Focus on:
- Visualization Specifications (IMPLEMENTATION_SPEC.md)
- User flows in Architecture Overview
- Phase definitions (what gets built when)

---

## Philosophy Alignment

This specification embodies the Amplifier design philosophy:

### 1. Ruthless Simplicity

- **MVP-first**: Phase 1 delivers working software, not perfect software
- **No premature optimization**: Add complexity only when justified
- **Clear module boundaries**: Each piece has one clear purpose

### 2. Modular & Regeneratable

- **"Bricks and studs" design**: Each module is self-contained with clear interfaces
- **Stable contracts**: Public APIs (the "studs") don't change during regeneration
- **Independent evolution**: Backend and frontend can evolve separately

### 3. Real-time UX Focus

- **Show, don't hide**: Visualize what the AI is doing in real-time
- **Progress transparency**: Users see every stage, every log line
- **Responsive feedback**: WebSocket updates within 50ms

---

## What Makes This Specification Different

### 1. Complete, Not Just Outlines

- Exact file structures with line count estimates
- Full TypeScript interfaces and Python models
- Detailed component hierarchies with props
- Implementation priorities with success criteria

### 2. AI-Generation Ready

- Each module can be generated independently
- Clear contracts prevent integration issues
- Regeneratable without breaking the system
- Designed for parallel development

### 3. Grounded in Reality

- Based on existing Amplifier CLI tools
- Tested patterns from blog_writer scenario
- Realistic timelines (3-4 weeks)
- Achievable scope (~5,500 lines)

---

## Key Numbers

| Metric | Value |
|--------|-------|
| **Total Lines** | ~5,500 |
| **Backend (Python)** | ~2,000 |
| **Frontend (TypeScript)** | ~3,500 |
| **API Endpoints** | 10 core endpoints |
| **WebSocket Events** | 7 event types |
| **React Components** | ~20 components |
| **Implementation Time** | 3-4 weeks |
| **Lines per Module** | 50-250 (manageable) |

---

## Implementation Status

- [x] Specifications complete
- [ ] Backend scaffold
- [ ] Frontend scaffold
- [ ] Phase 1: MVP
- [ ] Phase 2: Enhanced UX
- [ ] Phase 3: Polish

Track detailed progress in main project tracking system.

---

## Design Highlights

### Backend Architecture

```
FastAPI Server (Port 8000)
├── REST API (JSON responses)
├── WebSocket Manager (Real-time events)
├── Process Manager (Subprocess orchestration)
└── Scenario Discovery (Filesystem scanning)
```

**Key Innovation**: Execute CLI tools via subprocess for complete isolation and safety.

### Frontend Architecture

```
React App (Port 3000)
├── Server State (TanStack Query - API data)
├── Client State (Zustand - WebSocket updates)
├── Visualization (Workflow progress)
└── Forms (Dynamic parameter inputs)
```

**Key Innovation**: Dual state management - server state separate from real-time WebSocket state.

### Integration Pattern

```
User submits form → Backend starts subprocess → WebSocket streams output → 
Frontend parses events → Visualization updates → Artifacts download
```

**Key Innovation**: Output parsing detects stages/progress from unstructured CLI logs.

---

## Module Boundaries

### Backend Modules (Regeneratable)

1. **Scenario Discovery** (`services/scenario_discovery.py`)
   - Input: filesystem path
   - Output: List[Scenario]
   - Lines: ~200

2. **Process Manager** (`services/process_manager.py`)
   - Input: CLI command + params
   - Output: job_id + event stream
   - Lines: ~250

3. **Event Broadcaster** (`services/event_broadcaster.py`)
   - Input: WebSocket events
   - Output: Broadcast to clients
   - Lines: ~100

4. **Output Parser** (`services/output_parser.py`)
   - Input: stdout/stderr lines
   - Output: Structured data
   - Lines: ~150

### Frontend Modules (Regeneratable)

1. **ScenarioForm** (`components/scenarios/ScenarioForm.tsx`)
   - Input: Scenario definition
   - Output: ExecutionRequest
   - Lines: ~200

2. **WorkflowViz** (`components/execution/WorkflowViz.tsx`)
   - Input: StageState[]
   - Output: Visual diagram
   - Lines: ~250

3. **LogStream** (`components/execution/LogStream.tsx`)
   - Input: LogLine[]
   - Output: Virtualized display
   - Lines: ~120

4. **useWebSocket** (`hooks/useWebSocket.ts`)
   - Input: job_id
   - Output: Event stream
   - Lines: ~120

---

## Technology Choices

### Backend: Python + FastAPI

**Why FastAPI?**
- Modern async framework
- Automatic OpenAPI docs
- Excellent WebSocket support
- Pydantic integration

**Why subprocess execution?**
- Complete isolation (can't crash server)
- Works with any CLI tool
- Maintains CLI-first philosophy
- Easy resource management

### Frontend: React + TypeScript

**Why React?**
- Industry standard for complex UIs
- Large ecosystem
- Excellent tooling

**Why TypeScript?**
- Type safety catches bugs early
- Better IDE support
- Self-documenting code

**Why Vite?**
- 10x faster than CRA
- Modern tooling (ESBuild)
- Better TypeScript support

### State Management

**TanStack Query** (server state):
- Automatic caching/refetching
- Optimistic updates
- Less boilerplate

**Zustand** (client state):
- Simple API
- Less boilerplate than Redux
- Excellent TypeScript support

---

## Success Criteria

### Phase 1 (MVP)

- ✅ Can browse available scenarios
- ✅ Can start execution with parameters
- ✅ Can see real-time log output
- ✅ Can see when execution completes

### Phase 2 (Enhanced UX)

- ✅ Parameters auto-populate from CLI
- ✅ Visual workflow shows progress
- ✅ Can upload files
- ✅ Can download artifacts
- ✅ Clear error messages

### Phase 3 (Polish)

- ✅ 60fps animations
- ✅ Handles 10,000+ log lines
- ✅ Works on mobile/tablet
- ✅ Keyboard navigation
- ✅ Accessibility compliant

---

## Getting Help

### Questions About Specification

- Review full spec: [IMPLEMENTATION_SPEC.md](./IMPLEMENTATION_SPEC.md)
- Check quick reference: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- See architecture diagram: [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)

### Questions About Implementation

- Consult implementation philosophy: `@ai_context/IMPLEMENTATION_PHILOSOPHY.md`
- Review modular design: `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
- Study existing scenario: `@scenarios/blog_writer/`

### Questions About Approach

- Use `/agents` slash command to consult specialized agents:
  - `zen-architect` - Architecture questions
  - `modular-builder` - Module implementation
  - `api-contract-designer` - API design questions

---

## Next Steps

1. **Review specifications** - Ensure alignment with vision
2. **Set up project structure** - Create directories per spec
3. **Start Phase 1** - Delegate to modular-builder agent
4. **Iterate based on feedback** - Adjust as reality emerges

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-22 | Initial complete specification |

---

**Status**: Ready for implementation  
**Maintainer**: api-contract-designer agent  
**Last Review**: 2025-10-22
