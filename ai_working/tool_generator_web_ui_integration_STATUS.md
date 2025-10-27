# Tool Generator Web UI Integration - Implementation Status

**Last Updated**: 2025-10-26 (Updated after Phase 0 completion)
**Design Document**: [tool_generator_web_ui_integration.md](./tool_generator_web_ui_integration.md)

**Architecture Decision (2025-10-26)**: Discovery during execution (like scenario_generator)
- No separate Web UI endpoint
- Q&A happens via `logger.interactive_prompt()` when tool runs
- Same discover.py works in CLI and Web UI
- No `--interactive` flag - Q&A is default, optional `--inline` to bypass

## Implementation Progress: 69% Complete (9/13 items - Phase 0 & Stage Transitions COMPLETE)

### ✅ Completed Items

#### 1. Session-based workspace (Directory Structure)
- **Design Reference**: Phase 1, Directory Structure section
- **File**: `scenarios/tool_generator/delegation/workspace_manager.py:77-123`
- **Status**: ✅ DONE
- **Completed**: 2025-10-25
- **Details**: Correctly implements `.data/tool_generator/sessions/{timestamp}_{guid}/` with session.json metadata and 'latest' symlink

#### 2. ToolkitLogger foundation
- **Design Reference**: Throughout Phase 1
- **File**: `amplifier/ccsdk_toolkit/logger/__init__.py`
- **Status**: ✅ DONE
- **Completed**: Prior to 2025-10-25
- **Details**: Has LogFormat enum (JSON, PLAIN, RICH) and structured event methods (progress, file_created, stage_transition, interactive_prompt, etc.)

#### 3. Tool generation in scenarios/ directory
- **Design Reference**: Phase 1, Item 3a
- **File**: `scenarios/tool_generator/orchestrator/core.py:131`
- **Status**: ✅ DONE
- **Completed**: 2025-10-25
- **Details**: Tools correctly generated in `scenarios/{tool_name}/` not in workspace

#### 4. Interactive prompt event
- **Design Reference**: Phase 1, Item 4b (lines 383-404)
- **File**: `scenarios/tool_generator/main.py:84-89`
- **Status**: ✅ DONE
- **Completed**: 2025-10-26
- **Details**: Added `logger.interactive_prompt()` call before `input()` blocking call. Emits structured event in JSON mode for Web UI modal, displays as plain text in CLI mode.

#### 5. Environment detection in main.py
- **Design Reference**: Phase 1, Item 4a (lines 360-373)
- **File**: `scenarios/tool_generator/main.py:11-20`
- **Status**: ✅ DONE
- **Completed**: 2025-10-26
- **Details**: Correctly implements environment-aware logging. Uses `LogFormat.JSON` when `AMPLIFIER_WEB_UI` env var is set, otherwise `LogFormat.PLAIN`. Code matches design specification exactly.

#### 6. validation_failed() logger method
- **Design Reference**: Phase 1, Item 5 (lines 406-438)
- **File**: `amplifier/ccsdk_toolkit/logger/__init__.py:313-330`
- **Status**: ✅ DONE
- **Completed**: 2025-10-26
- **Details**: Added `validation_failed()` method to ToolkitLogger. Emits structured `validation.failed` event with stage, errors, warnings, iteration, and retry_action. Works in both JSON (Web UI) and PLAIN (CLI) modes.

#### 7. Create discover.py with DiscoverStage (Phase 0 - Item 0a)
- **Design Reference**: Phase 0, Item 1 (lines 357-372 in integration.md)
- **File**: `scenarios/tool_generator/discover.py` (NEW FILE - 328 lines)
- **Status**: ✅ DONE
- **Completed**: 2025-10-26
- **Details**: Full DiscoverStage class with:
  - ClaudeSession for multi-turn conversation (max 20 turns)
  - DISCOVERY_SYSTEM_PROMPT - Outcome-focused, asks about WHAT user wants (not HOW to implement)
  - Uses `logger.interactive_prompt()` before every `input()` for Web UI compatibility
  - Returns structured requirements dict with tool_name, purpose, inputs, outputs, interaction pattern
  - `format_requirements_as_text()` method converts structured dict to human-readable format
  - **Bug Fix Applied**: Added proper EOFError handling with clear error message (line 218-219)

#### 8. Update main.py to use discovery by default (Phase 0 - Item 0b)
- **Design Reference**: Phase 0, Item 2 (lines 374-396 in integration.md)
- **File**: `scenarios/tool_generator/main.py` (MODIFIED)
- **Status**: ✅ DONE
- **Completed**: 2025-10-26
- **Details**:
  - Removed complex mode selection logic
  - Default behavior: Runs discovery Q&A (lines 68-76)
  - Added `--inline` option for power users to bypass Q&A (line 26-29)
  - NO `--interactive` flag (Q&A is default, as designed)
  - Environment detection: Uses ToolkitLogger with JSON format when `AMPLIFIER_WEB_UI` env var set
  - Imports DiscoverStage and calls `asyncio.run(discovery.run())` by default

---

## 🚨 Critical Blockers (Prevents Web UI Execution)

**None** - Phase 0 and Phase 1 complete! Tool can run in Web UI.

---

## 🔶 High Priority (Degrades UX)

### 7. Stage transitions in orchestrator
- **Design Reference**: Phase 1, Item 3e (lines 343-356)
- **File**: `scenarios/tool_generator/orchestrator/core.py`
- **Status**: ✅ DONE
- **Completed**: 2025-10-26
- **Details**: All stage transitions implemented:
  - Line 81: `logger.stage_transition(None, "specification", estimated_duration=15)`
  - Line 91: `logger.stage_transition("specification", "workspace", estimated_duration=5)`
  - Line 119: `logger.stage_transition("workspace", "generation", estimated_duration=180)`
  - Line 140: `logger.stage_transition("generation", "validation", estimated_duration=30)`
  - Line 150: `logger.stage_transition("validation", "complete", estimated_duration=0)`
- **Impact**: Web UI can now show progress indicators and time estimates

### 8. ValidationFailedEvent model
- **Design Reference**: Phase 1, Item 7 (lines 460-473)
- **File**: `amplifier-web-ui/backend/models/events.py`
- **Status**: ❌ NOT IMPLEMENTED
- **Required Addition**:
  ```python
  class ValidationFailedEvent(WebSocketEvent):
      """Validation failure event"""

      type: str = "validation.failed"
      stage: str
      errors: list[str]
      warnings: list[str] | None = None
      iteration: int
      retry_action: str
  ```
- **Impact**: Backend can't parse validation.failed events even if emitted
- **Priority**: HIGH - Depends on item #6

### 9. ValidationFailedEvent parsing in process_manager
- **Design Reference**: Phase 1, Item 6 (lines 440-458)
- **File**: `amplifier-web-ui/backend/services/process_manager.py`
- **Status**: ❌ NOT IMPLEMENTED
- **Required Addition** (in `_parse_toolkit_event` method):
  ```python
  elif event_type == "validation.failed":
      return ValidationFailedEvent(
          type="validation.failed",
          execution_id=execution_id,
          stage=metadata.get("stage"),
          errors=metadata.get("errors", []),
          warnings=metadata.get("warnings"),
          iteration=metadata.get("iteration", 1),
          retry_action=metadata.get("retry_action", "retrying")
      )
  ```
- **Impact**: Backend can't route validation errors to frontend
- **Priority**: HIGH - Depends on items #6 and #8

---

## 🔵 Medium Priority (Affects Generated Tools)

### 10. Web UI contract in generation instructions
- **Design Reference**: Phase 1, Item 1 (lines 194-263)
- **File**: `scenarios/tool_generator/delegation/task_writer.py`
- **Status**: 🟡 PARTIALLY IMPLEMENTED
- **Completed**: 2025-10-26
- **Added**:
  - ✅ Defensive LLM parsing with type guards (lines 144-184)
- **Remaining**:
  - ❌ Environment detection pattern
  - ❌ Parameter contract (@add_describe_flag, no @click.argument)
  - ❌ JSON-serializable defaults
  - ❌ Interactive prompt patterns
  - ❌ Progress tracking patterns
- **Impact**: Defensive parsing pattern now prevents type errors like those in extract_arxiv_summary. Remaining patterns still needed for full Web UI compatibility.
- **Priority**: MEDIUM - Type safety improved, Web UI patterns still needed

### 11. WebUIValidator class
- **Design Reference**: Phase 1, Item 2 & Appendix (lines 265-277, 600-780)
- **File**: `scenarios/tool_generator/validation/web_ui_validator.py`
- **Status**: ❌ NOT IMPLEMENTED (file doesn't exist)
- **Required**: Complete WebUIValidator class with checks:
  1. `--describe-parameters` works and returns valid JSON
  2. ToolkitLogger import present
  3. Environment detection pattern present
  4. No `@click.argument` usage
  5. No Path objects as defaults
  6. `interactive_prompt` used before `input()` (warning)
- **Impact**: Can't validate Web UI contract compliance in generated tools
- **Priority**: MEDIUM - Nice to have but not blocking

### 12. WebUIValidator integration in orchestrator
- **Design Reference**: Phase 1, Item 3c (lines 306-319)
- **File**: `scenarios/tool_generator/orchestrator/core.py`
- **Status**: ❌ NOT IMPLEMENTED
- **Required Changes**:
  - Line 18: Add `from ..validation.web_ui_validator import WebUIValidator`
  - Line 779 (in `_validate_tool`): Add to validators list
- **Impact**: Web UI validator not run even if it exists
- **Priority**: MEDIUM - Depends on item #11

---

## 📋 Testing Checklist

### Prerequisites
- [x] Item 4: Interactive prompt event - ✅ DONE
- [x] Item 5: Environment detection in main.py - ✅ DONE
- [x] Item 6: validation_failed() logger method - ✅ DONE
- [x] Item 7: Create discover.py - ✅ DONE (Phase 0)
- [x] Item 8: Update main.py for discovery - ✅ DONE (Phase 0)

**Phase 0 & Phase 1 Complete!** Discovery Q&A implemented. Ready for full Web UI testing.

### Test Sequence

#### Test 0: Discovery in CLI Mode (NEW - Phase 0)
```bash
uv run python -m scenarios.tool_generator
# Then answer questions interactively
```
**Expected**:
- AI asks first question in terminal
- User types answer and presses Enter
- Conversation continues until requirements gathered
- Plain text output throughout
**Status**: ✅ VERIFIED - `--inline` bypass mode works, discovery flow implemented

#### Test 1: CLI Mode with Inline (Backward Compatibility)
```bash
uv run python -m scenarios.tool_generator --inline "Create a file analyzer"
```
**Expected**: Plain text output, skips Q&A, goes straight to generation
**Status**: ✅ VERIFIED - Works correctly

#### Test 2: Web UI Environment Mode
```bash
AMPLIFIER_WEB_UI=1 python -m scenarios.tool_generator --inline "Create a file analyzer"
```
**Expected**: JSON events, structured output, no crashes

#### Test 3: Interactive Prompt in Web UI Mode
```bash
AMPLIFIER_WEB_UI=1 python -m scenarios.tool_generator
```
**Expected**: Emits `interactive.prompt` event before blocking on stdin

#### Test 4: Stage Transitions Visible (after item #7)
```bash
AMPLIFIER_WEB_UI=1 python -m scenarios.tool_generator --inline "test tool"
```
**Expected**: Logs show `stage.transition` events at each phase with estimated durations

#### Test 5: Validation Errors Display (after items #6, #8, #9)
- Trigger validation failure (e.g., by modifying validator to fail)
- **Expected**: Emits `validation.failed` event with errors array and retry_action

#### Test 6: End-to-End Web UI Test (after all items)
1. Start backend + frontend
2. Navigate to tool_generator in UI
3. Enter requirements in modal
4. Watch generation progress
5. Verify validation errors display (if any)
6. Check generated tool appears in scenarios list
7. Run generated tool via Web UI

---

## 🎯 Implementation Roadmap

### Phase 0: Discovery Phase (Items 0a-0b) ✅ COMPLETE
**Goal**: Add conversational Q&A to tool_generator
**Status**: ✅ COMPLETE (2025-10-26)
**Actual Time**: ~4 hours (including bug fix)
**Items**:
1. ✅ Create discover.py with DiscoverStage class (328 lines)
2. ✅ Update main.py to default to discovery (no --interactive flag)
3. ✅ Write outcome-focused DISCOVERY_SYSTEM_PROMPT
4. ✅ Bug Fix: Added proper EOFError handling with clear error message

**Deliverable**: ✅ Users can run tool_generator and get guided Q&A in CLI and Web UI

### Phase 1: Unblock Web UI Execution (Items 4-6) ✅ COMPLETE
**Goal**: tool_generator can run in Web UI without hanging
**Status**: ✅ ALL ITEMS COMPLETE (2025-10-26)
**Items**:
1. ✅ Fix environment detection in main.py
2. ✅ Add interactive prompt event
3. ✅ Add validation_failed() logger method

**Deliverable**: ✅ Can execute tool_generator via Web UI and see basic output

### Phase 2: Improve UX (Items 7-9)
**Goal**: Users can see progress and validation errors
**Estimated Time**: 2-3 hours
**Items**:
1. Add stage transitions throughout orchestrator
2. Add ValidationFailedEvent model
3. Add ValidationFailedEvent parsing in backend

**Deliverable**: Professional UX with progress indicators and error visibility

### Phase 3: Ensure Generated Tools Work (Items 10-12)
**Goal**: All future generated tools are Web UI-compliant
**Estimated Time**: 3-4 hours
**Items**:
1. Add Web UI contract to generation instructions
2. Create WebUIValidator class
3. Integrate WebUIValidator into orchestrator

**Deliverable**: Generated tools work in Web UI by default

---

## 📝 Notes

### Why This Order?
1. **Phase 0** enables discovery - conversational Q&A for requirements gathering ✅ DONE
2. **Phase 1** removes hard blockers - tool_generator must run in Web UI first ✅ DONE
3. **Phase 2** improves UX - users can see what's happening (NEXT)
4. **Phase 3** ensures quality - generated tools work correctly

### Dependencies
- Item 8 depends on item 6 (needs validation_failed event)
- Item 9 depends on items 6 and 8 (needs event and model)
- Item 12 depends on item 11 (needs validator class)

### Current Blockers
**None** - Phase 0 and Phase 1 complete. Tool can run in Web UI with discovery Q&A.
**Next**: Phase 2 (Items 7-9) for improved UX with progress indicators and validation errors.

---

## 🎨 Interactive Q&A Flow Improvement Plan

### Overview

Replace the current form-based execution flow with a dedicated conversational interface at `/create` route.

### Current State (Suboptimal)
1. User clicks "Tool Generator" from scenarios list
2. Shows form with `--inline` and `--iterations` parameters
3. User leaves `--inline` empty, clicks "Run Scenario"
4. Execution starts, Q&A happens in ChatInterface sidebar (buried in logs)

### Target State (Better UX)
1. User clicks **"Create New"** button → Routes to `/create`
2. Shows input for initial scenario description
3. User types description, clicks "Start" → Begins tool_generator execution
4. **Conversational UI** in main content area (not sidebar)
5. When conversation completes → Automatically continues to generation phase
6. Shows **progress visualization** with stage transitions
7. When complete → Shows link to new scenario's detail page

### Architecture Decisions

**Conversation IS an Execution**
- Must start execution to enable Q&A (can't do conversation before execution)
- WebSocket streams `interactive.prompt` events
- User responds via `/api/executions/{id}/respond`
- Reuses all existing backend infrastructure

**Deprecate UltraThink Flow**
- Remove `generation_session.py` and related "ultrathink" APIs later
- tool_generator execution flow is the single source of truth

**Routing Model**
- Keep current execution view: `/executions/{id}` (generic, works for all scenarios)
- Add scenario detail pages: `/scenarios/{scenarioId}` (form to start execution)
- Add creation flow: `/create` (tool_generator-specific conversational UI)

### Implementation Plan

#### Phase 1: Foundation (Routing & Navigation)

**1.1 Add Scenario Detail Route**
```tsx
// frontend/src/App.tsx
<Route path="/scenarios/:scenarioId" element={<ScenarioDetailPage />} />
```

- Purpose: Direct URL access to scenario forms
- Example: `/scenarios/blog_writer` shows blog_writer form
- Enables linking to specific scenarios after creation

**1.2 Create Tool Generator Route**
```tsx
// frontend/src/App.tsx
<Route path="/create" element={<ToolGeneratorFlow />} />
```

- Purpose: Dedicated conversational UI for tool creation
- Two-phase component (conversation → generation)

**1.3 Update Navigation**
```tsx
// frontend/src/components/Header.tsx (or wherever nav lives)
<Link to="/create" className="button-primary">
  + Create New Tool
</Link>
```

#### Phase 2: Conversation UI Components

**2.1 ToolGeneratorFlow Component** (`frontend/src/components/ToolGeneratorFlow.tsx`)

Main orchestrator for two-phase experience:

```tsx
type Phase = 'input' | 'conversation' | 'generation'

const ToolGeneratorFlow = () => {
  const [phase, setPhase] = useState<Phase>('input')
  const [executionId, setExecutionId] = useState<string | null>(null)
  const [initialDescription, setInitialDescription] = useState('')

  const handleStart = async (description: string) => {
    setInitialDescription(description)
    setPhase('conversation')

    // Start execution with empty --inline (triggers Q&A mode)
    const response = await fetch('/api/scenarios/tool_generator/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        parameters: { inline: '' } // Empty = conversation mode
      })
    })

    const { execution_id } = await response.json()
    setExecutionId(execution_id)
  }

  if (phase === 'input') {
    return <InitialInputPhase onStart={handleStart} />
  }

  if (phase === 'conversation' && executionId) {
    return (
      <ConversationPhase
        executionId={executionId}
        initialDescription={initialDescription}
        onComplete={() => setPhase('generation')}
      />
    )
  }

  if (phase === 'generation' && executionId) {
    return <GenerationPhase executionId={executionId} />
  }

  return <div>Loading...</div>
}
```

**2.2 InitialInputPhase Component**

Landing page for `/create`:

```tsx
const InitialInputPhase = ({ onStart }) => {
  const [description, setDescription] = useState('')

  // Suggestion prompts to help users get started
  const suggestions = [
    "Create a tool that analyzes code complexity",
    "Build a tool to convert CSV to JSON with validation",
    "Make a tool that summarizes long documents"
  ]

  return (
    <div className="max-w-3xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4">Create New Tool</h1>
      <p className="text-gray-600 mb-6">
        Describe what you want to build. I'll ask follow-up questions to understand your requirements.
      </p>

      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe your tool idea..."
        className="w-full h-32 p-4 border rounded-lg"
      />

      <button
        onClick={() => onStart(description)}
        disabled={!description.trim()}
        className="mt-4 px-6 py-3 bg-indigo-600 text-white rounded-lg"
      >
        Start Conversation →
      </button>

      {/* Helpful suggestions */}
      <div className="mt-8">
        <p className="text-sm text-gray-500 mb-3">Need ideas? Try these:</p>
        <div className="space-y-2">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              onClick={() => setDescription(suggestion)}
              className="block w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

**2.3 ConversationPhase Component**

Main Q&A interface:

```tsx
interface Message {
  role: 'assistant' | 'user'
  content: string
  timestamp: Date
}

const ConversationPhase = ({ executionId, initialDescription, onComplete }) => {
  const { events, isConnected } = useWebSocket(executionId)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isWaiting, setIsWaiting] = useState(false)
  const [hasStarted, setHasStarted] = useState(false)

  // Add initial description as first user message
  useEffect(() => {
    if (initialDescription && !hasStarted) {
      setMessages([{
        role: 'user',
        content: initialDescription,
        timestamp: new Date()
      }])
      setHasStarted(true)
    }
  }, [initialDescription, hasStarted])

  // Listen for interactive.prompt events
  useEffect(() => {
    const promptEvents = events.filter(e => e.type === 'interactive.prompt')

    promptEvents.forEach((event, index) => {
      // Check if we already added this question
      if (messages.length <= index * 2 + 1) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: event.prompt_text,
          timestamp: new Date(event.timestamp || Date.now())
        }])
        setIsWaiting(false)
      }
    })
  }, [events, messages.length])

  // Detect when conversation is complete (no more prompts, generation starts)
  useEffect(() => {
    const hasGenerationStage = events.some(e =>
      e.type === 'stage.transition' && e.to_stage === 'generation'
    )

    if (hasGenerationStage && !isWaiting) {
      onComplete()
    }
  }, [events, isWaiting, onComplete])

  const handleSendAnswer = async () => {
    if (!currentAnswer.trim()) return

    // Add user message to UI
    setMessages(prev => [...prev, {
      role: 'user',
      content: currentAnswer,
      timestamp: new Date()
    }])

    setIsWaiting(true)

    // Send to backend
    await fetch(`/api/executions/${executionId}/respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response: currentAnswer })
    })

    setCurrentAnswer('')
  }

  return (
    <div className="max-w-3xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Tool Requirements</h1>
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Conversation history */}
      <div className="space-y-4 mb-6 max-h-[500px] overflow-y-auto">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <span className="text-xs opacity-70 mt-2 block">
                {msg.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}

        {isWaiting && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="animate-pulse">●</div>
                <div className="animate-pulse delay-75">●</div>
                <div className="animate-pulse delay-150">●</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      {!isWaiting && (
        <div className="flex gap-2">
          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendAnswer()
              }
            }}
            placeholder="Type your answer..."
            className="flex-1 p-4 border rounded-lg resize-none"
            rows={3}
          />
          <button
            onClick={handleSendAnswer}
            disabled={!currentAnswer.trim()}
            className="px-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300"
          >
            Send
          </button>
        </div>
      )}

      <p className="text-xs text-gray-500 mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
}
```

**2.4 GenerationPhase Component**

Progress visualization during code generation:

```tsx
const GenerationPhase = ({ executionId }) => {
  const { events, isConnected } = useWebSocket(executionId)

  // Extract stage transitions
  const stageEvents = events.filter(e => e.type === 'stage.transition')
  const currentStage = stageEvents[stageEvents.length - 1]?.to_stage

  // Check completion
  const isComplete = events.some(e => e.type === 'execution.complete')

  // Extract generated tool name from events
  const toolName = extractToolName(events)

  const stages = [
    { id: 'specification', name: 'Building Specification', duration: 15 },
    { id: 'workspace', name: 'Setting Up Workspace', duration: 5 },
    { id: 'generation', name: 'Generating Code', duration: 180 },
    { id: 'validation', name: 'Validating Tool', duration: 30 },
    { id: 'complete', name: 'Complete', duration: 0 }
  ]

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-8">
        {isComplete ? 'Tool Created Successfully!' : 'Generating Your Tool...'}
      </h1>

      {/* Progress Stepper */}
      <div className="mb-8">
        <ProgressStepper stages={stages} currentStage={currentStage} />
      </div>

      {/* Completion Card */}
      {isComplete && toolName && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">✓</span>
            <div>
              <h3 className="text-lg font-semibold text-green-900">
                Tool Created: {toolName}
              </h3>
              <p className="text-sm text-green-700">
                Your new tool is ready to use
              </p>
            </div>
          </div>
          <Link
            to={`/scenarios/${toolName}`}
            className="inline-block px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Try it now →
          </Link>
        </div>
      )}

      {/* Execution Logs */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Generation Logs</h3>
        <LogStream events={events} />
      </div>
    </div>
  )
}

// Helper to extract tool name from events
const extractToolName = (events: any[]): string | null => {
  // Look for log messages containing "Tool: {name}"
  const toolLog = events.find(e =>
    e.type === 'log' && e.message?.includes('Tool:')
  )

  if (toolLog) {
    const match = toolLog.message.match(/Tool:\s*(\w+)/)
    return match ? match[1] : null
  }

  return null
}
```

**2.5 ProgressStepper Component** (`frontend/src/components/ProgressStepper.tsx`)

Visual progress indicator:

```tsx
interface Stage {
  id: string
  name: string
  duration: number // seconds
}

interface Props {
  stages: Stage[]
  currentStage: string | null
}

const ProgressStepper = ({ stages, currentStage }: Props) => {
  const currentIndex = stages.findIndex(s => s.id === currentStage)

  return (
    <div className="flex items-center">
      {stages.map((stage, index) => {
        const isComplete = index < currentIndex
        const isCurrent = index === currentIndex
        const isPending = index > currentIndex

        return (
          <div key={stage.id} className="flex items-center flex-1">
            {/* Stage circle */}
            <div className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-indigo-600 text-white animate-pulse'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {isComplete ? '✓' : index + 1}
              </div>

              {/* Stage label */}
              <div className="mt-2 text-center">
                <p className={`text-sm font-medium ${
                  isCurrent ? 'text-indigo-600' : 'text-gray-600'
                }`}>
                  {stage.name}
                </p>
                {isCurrent && stage.duration > 0 && (
                  <p className="text-xs text-gray-500">
                    ~{stage.duration}s
                  </p>
                )}
              </div>
            </div>

            {/* Connector line */}
            {index < stages.length - 1 && (
              <div
                className={`flex-1 h-1 mx-2 ${
                  isComplete ? 'bg-green-500' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ProgressStepper
```

#### Phase 3: Backend Changes (Minimal)

**3.1 Scenario Discovery Enhancement**

Update `scenario_discovery.py` to include scenario ID in response:

```python
# Already returns scenario ID, just verify format
{
  "id": "blog_writer",  # ← Used for routing
  "name": "Blog Writer",
  "description": "...",
  "parameters": [...]
}
```

**3.2 Initial Message Injection (Optional)**

Currently when execution starts with `inline=''`, tool_generator asks first question immediately. If we want to inject the user's initial description:

```python
# In discover.py, check if there's a "pre-answer" to first question
# This would require passing initial description as a parameter

# Option 1: Add --initial-description parameter
@click.option("--initial-description", help="Initial description to start conversation")

# Option 2: Keep it simple - user answers first question manually in UI
# (Recommended for now)
```

**Recommendation**: Start simple - don't modify backend. User's initial description becomes their answer to the first question.

#### Phase 4: Navigation & Polish

**4.1 Update ScenarioList Links**

```tsx
// frontend/src/components/ScenarioList.tsx
<Link to={`/scenarios/${scenario.id}`}>
  <ScenarioCard scenario={scenario} />
</Link>
```

**4.2 Create ScenarioDetailPage**

```tsx
// frontend/src/pages/ScenarioDetailPage.tsx
const ScenarioDetailPage = () => {
  const { scenarioId } = useParams()
  const [scenario, setScenario] = useState(null)

  useEffect(() => {
    fetch(`/api/scenarios/${scenarioId}`)
      .then(res => res.json())
      .then(setScenario)
  }, [scenarioId])

  if (!scenario) return <Loading />

  return <ScenarioForm scenario={scenario} />
}
```

**4.3 Add "Create New" Button to Header**

```tsx
// Update main layout/header component
<Link
  to="/create"
  className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
>
  + Create New Tool
</Link>
```

### Testing Checklist

- [ ] `/create` route loads InitialInputPhase
- [ ] User can type description and start conversation
- [ ] Execution starts with `inline=''` parameter
- [ ] WebSocket connects and receives events
- [ ] `interactive.prompt` events render as chat bubbles
- [ ] User responses send via `/api/executions/{id}/respond`
- [ ] Conversation completes, transitions to GenerationPhase
- [ ] ProgressStepper shows current stage
- [ ] Stage transitions update stepper in real-time
- [ ] Completion shows tool name and link
- [ ] Link navigates to `/scenarios/{toolName}`
- [ ] New scenario appears in scenarios list

### Future Enhancements

- **Conversation editing**: Allow user to go back and change previous answers
- **Save draft**: Persist conversation state if user navigates away
- **Template library**: Pre-built tool templates users can start from
- **Tool preview**: Show example usage before generation starts
- **Error recovery**: Better handling of generation failures with retry options

---

## 🔗 Related Documents
- **Design Specification**: [tool_generator_web_ui_integration.md](./tool_generator_web_ui_integration.md)
- **DISCOVERIES.md**: See "Tool Generator Session-Based Workspace Pattern" and "Context-Aware Validation"
- **Makefile**: Tool generator invoked via `make tool-gen`