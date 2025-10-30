# Terminal Mode Migration Complete

## Summary

The amplifier-web-ui frontend has been successfully updated to use terminal mode exclusively, removing the legacy standard execution path that relied on conversation_manager and scenario-specific execution endpoints.

## Changes Made

### 1. Removed /create Route (App.tsx)
- **File**: `frontend/src/App.tsx`
- **Changes**:
  - Removed `/create` route that mapped to ToolGeneratorFlow
  - Removed "Create New" navigation link
  - Removed unused `CreateIcon` import
  - Kept only essential routes: `/`, `/scenarios/:scenarioId`, `/executions/:executionId`

### 2. Deleted ToolGeneratorFlow.tsx
- **File**: `frontend/src/components/ToolGeneratorFlow.tsx`
- **Action**: Deleted (no longer used after /create route removal)
- **Reason**: This component handled dual-mode execution (standard vs terminal), which is no longer needed

### 3. Simplified ConversationPhase.tsx
- **File**: `frontend/src/components/ConversationPhase.tsx`
- **Changes**:
  - Removed all standard mode WebSocket logic
  - Removed conversation history UI (messages, scroll handling)
  - Removed event processing for interactive.prompt, stream.output, progress, etc.
  - Removed execution logs rendering section (lines 360-471)
  - Kept only terminal mode: TerminalProxy component
  - Removed `onComplete` prop (no longer needed without generation phase transition)
  - Simplified to: Input textarea → Send button → TerminalProxy output

### 4. Key Behavioral Changes
- **Before**: Dual mode (standard execution with logs OR terminal mode)
- **After**: Terminal mode only
  - User enters tool description
  - Sends to `/api/claude/execute` with `/ultrathink-task` prefix
  - Output rendered in xterm.js terminal (TerminalProxy)
  - No more conversation history bubbles
  - No more parsed event logs
  - No more generation phase transition

## Architecture After Changes

```
User Input (textarea)
    ↓
/api/claude/execute endpoint
    ↓
Claude CLI (PTY)
    ↓
WebSocket stream (/api/claude/terminal/{execution_id}/ws)
    ↓
TerminalProxy (xterm.js)
    ↓
User sees live terminal output
```

## What Was Removed

1. **Standard execution path**: `/api/scenarios/{scenario}/execute` endpoints
2. **Conversation manager logic**: WebSocket event parsing, interactive prompts
3. **Generation phase**: Transition from conversation to generation stage
4. **Dual-mode support**: Query params like `?customCreateScenario`
5. **Event log rendering**: Detailed log viewer with expandable messages
6. **Message history UI**: Chat-like conversation bubbles

## What Remains

1. **Terminal mode only**: Clean, direct integration with Claude CLI
2. **Simple input**: Single textarea for tool description
3. **Live terminal output**: Real-time PTY streaming via xterm.js
4. **Scenario list**: Browse and execute existing scenarios
5. **Execution views**: View past executions (blog_writer, generic)

## Benefits

- **Ruthless simplicity**: One code path instead of two
- **Direct integration**: Claude CLI handles all conversation logic
- **Better UX**: Real terminal experience with ANSI colors, progress indicators
- **Easier maintenance**: Less code to maintain and debug
- **Clearer architecture**: Web UI is just a viewer/launcher, not a conversation manager

## Testing

To verify the changes:

1. Start the web UI: `cd amplifier-web-ui && make run`
2. Navigate to home page
3. Verify:
   - ✅ /create route is gone (404 if accessed directly)
   - ✅ "Create New" nav button removed
   - ✅ Scenario list loads and displays
   - ✅ Scenario execution uses terminal mode
   - ✅ Terminal output displays with ANSI colors
   - ✅ No conversation manager errors in logs

## Files Modified

- `frontend/src/App.tsx` - Removed /create route and CreateIcon
- `frontend/src/components/ConversationPhase.tsx` - Simplified to terminal-only
- `frontend/src/components/ToolGeneratorFlow.tsx` - DELETED

## Related Documentation

- `INTERACTIVE_PROMPT_FIX.md` - Terminal mode implementation details
- `CLAUDE_TERMINAL_INTEGRATION.md` - Claude CLI integration architecture

## Next Steps

Consider:
1. Remove GenerationPhase.tsx (unused after ToolGeneratorFlow deletion)
2. Clean up unused WebSocket event types in `types/api.ts`
3. Update Web UI documentation to reflect terminal-only mode
4. Remove conversation_manager references from backend (separate task)

---

**Migration completed**: 2025-01-30
**Philosophy**: Ruthless simplicity - one pattern that works beats two patterns that "might be needed"
