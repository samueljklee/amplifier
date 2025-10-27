# Scenario Debug Mode Design

## Overview

A system for debugging and automatically fixing broken scenarios using Claude Code SDK integration. When a scenario fails, the debug mode analyzes the error, identifies the root cause, and suggests or automatically applies fixes.

## User's Request

> "for each scenario (in the UI), do we need a way to debug a scenario, and talk to claude code sdk to actually fix the scenario?"

## Design Goals

1. **Automatic Error Detection**: Catch scenario failures immediately during execution
2. **Intelligent Diagnosis**: Use multiple checks to identify root causes
3. **AI-Assisted Fixing**: Leverage Claude Code SDK to suggest and apply fixes
4. **Minimal User Intervention**: Make fixes automatic when safe, require confirmation for complex changes
5. **Learning System**: Build a knowledge base of common issues and fixes

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Execution   │  │    Debug     │  │     Fix      │      │
│  │    View      │→ │    Panel     │→ │   Controls   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                     Backend API                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Scenario Debug Service                     │  │
│  │  • Error Capture & Analysis                           │  │
│  │  • Diagnostic Tests                                   │  │
│  │  • Claude Code SDK Integration                        │  │
│  │  • Fix Application Engine                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Flow

```
Scenario Execution
       ↓
   [Error Detected]
       ↓
  Run Diagnostics ──────────────┐
       ↓                         │
  Analyze with Claude SDK        │
       ↓                         │
  Generate Fix Suggestions       │
       ↓                         │
  Present to User ←──────────────┘
       ↓
  [User Reviews/Approves]
       ↓
  Apply Fixes
       ↓
  Re-test Scenario
       ↓
  Report Success/Failure
```

## Diagnostic Tests

When a scenario fails, run these diagnostic tests:

### 1. Parameter Discovery Check
```python
def check_parameter_discovery(scenario_dir: Path) -> DiagnosticResult:
    """
    Verify that parameters are discoverable by web UI backend.

    Checks:
    - No @click.argument usage for file inputs
    - All parameters use @click.option
    - Parameters have proper type hints and help text
    """
    # Read main.py
    # Run parameter discovery regex (same as scenario_discovery.py)
    # Report issues with @click.argument usage
    # Return: { "passed": bool, "issues": list[str], "suggestions": list[str] }
```

### 2. CLI Execution Test
```python
def test_cli_execution(scenario_dir: Path) -> DiagnosticResult:
    """
    Test if scenario can be executed via CLI with sample inputs.

    Checks:
    - Python imports work
    - Click command is properly defined
    - --help works without errors
    - Basic execution with dummy inputs succeeds
    """
    # Run: python -m scenarios.{name} --help
    # Parse help output
    # Test with sample parameters
    # Return: { "passed": bool, "error": str, "output": str }
```

### 3. Dependency Check
```python
def check_dependencies(scenario_dir: Path) -> DiagnosticResult:
    """
    Verify all dependencies are installed and compatible.

    Checks:
    - pyproject.toml is valid
    - All dependencies can be imported
    - No version conflicts
    """
    # Parse pyproject.toml
    # Try importing each dependency
    # Check for version mismatches
    # Return: { "passed": bool, "missing": list[str], "conflicts": list[str] }
```

### 4. File Structure Validation
```python
def validate_file_structure(scenario_dir: Path) -> DiagnosticResult:
    """
    Ensure required files exist and are valid.

    Checks:
    - main.py exists and has valid Python syntax
    - __main__.py exists and imports main()
    - __init__.py exists (can be empty)
    - pyproject.toml exists and is valid TOML
    - README.md exists and has content
    """
    # Check file existence
    # Validate Python syntax with compile()
    # Parse TOML
    # Return: { "passed": bool, "missing_files": list[str], "invalid_files": list[str] }
```

### 5. Makefile Target Check
```python
def check_makefile_target(scenario_name: str) -> DiagnosticResult:
    """
    Verify Makefile entry exists and handles parameters correctly.

    Checks:
    - Target exists in Makefile
    - Parameter handling matches discovered parameters
    - Command syntax is correct
    """
    # Read Makefile
    # Find target
    # Validate parameter passing logic
    # Return: { "passed": bool, "issues": list[str] }
```

## Claude Code SDK Integration

### Debug Request Structure

```python
class DebugRequest:
    scenario_name: str
    error_message: str
    error_type: str  # "runtime", "import", "parameter", "syntax"
    diagnostic_results: dict[str, DiagnosticResult]
    scenario_files: dict[str, str]  # filename -> content
    execution_log: str
```

### SDK Prompt Template

```python
DEBUG_SYSTEM_PROMPT = """You are a scenario debugging expert for Amplifier CLI tools.

Analyze the scenario error and diagnostic results below, then provide:
1. Root cause analysis
2. Specific fix instructions
3. Code patches if needed

CRITICAL RULES:
- Use @click.option for all file parameters (NEVER @click.argument)
- Ensure parameters are discoverable by scenario_discovery.py
- Generate complete, working code - no stubs or TODOs
- Test fixes against parameter discovery validation

Error Context:
{error_message}

Diagnostic Results:
{diagnostic_results}

Scenario Files:
{scenario_files}

Provide fixes as structured patches that can be automatically applied.
"""
```

### Fix Application

```python
class ScenarioFix:
    fix_type: str  # "code_patch", "makefile_update", "dependency_add", "file_create"
    target_file: str
    action: str  # "replace", "insert", "delete", "create"
    old_content: str | None
    new_content: str
    description: str
    requires_confirmation: bool

async def apply_fix(fix: ScenarioFix, scenario_dir: Path) -> bool:
    """Apply a fix to a scenario."""
    # Validate fix is safe
    # Apply changes to files
    # Run validation tests
    # Return success/failure
```

## Web UI Components

### 1. Debug Panel (appears when error detected)

```typescript
interface DebugPanel {
  // Error Summary
  errorMessage: string;
  errorType: string;

  // Diagnostic Results
  diagnostics: DiagnosticResult[];

  // AI Analysis
  rootCause: string;
  suggestedFixes: Fix[];

  // Actions
  onApplyFix: (fixId: string) => void;
  onRetest: () => void;
  onAskClaude: (question: string) => void;
}
```

Visual mockup:
```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Debug Mode                                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ⚠️ Error: Got unexpected extra argument (...)           │
│                                                          │
│ Diagnostics:                                             │
│   ✗ Parameter Discovery: Found @click.argument usage    │
│   ✓ File Structure: All files present                   │
│   ✓ Dependencies: All installed                         │
│                                                          │
│ 🤖 AI Analysis:                                          │
│ The scenario uses @click.argument for the input file,   │
│ but the web UI can only discover @click.option          │
│ parameters. This causes file uploads to fail.           │
│                                                          │
│ Suggested Fixes:                                         │
│   1. [Auto-fix] Convert @click.argument to @click.option│
│      → Changes main.py parameter definition             │
│      → Updates Makefile to pass --input flag            │
│                                                          │
│   [Apply All Fixes]  [Retest]  [Ask Claude ↓]          │
└─────────────────────────────────────────────────────────┘
```

### 2. Interactive Claude Chat

```typescript
interface ClaudeChat {
  conversationHistory: Message[];
  onSendMessage: (message: string) => Promise<string>;
  contextFiles: string[];  // Files Claude has access to
}
```

Visual mockup:
```
┌─────────────────────────────────────────────────────────┐
│ 💬 Chat with Claude about this scenario                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ You: Why is the parameter not being discovered?         │
│                                                          │
│ Claude: The parameter uses @click.argument which        │
│ scenario_discovery.py cannot detect. The backend only   │
│ looks for @click.option decorators using regex pattern. │
│                                                          │
│ [Type your question...]                    [Send]       │
└─────────────────────────────────────────────────────────┘
```

## Backend API Endpoints

### 1. Trigger Debug Mode
```python
POST /api/scenarios/{scenario_id}/debug
Request:
{
  "execution_id": "exec-123",
  "error": {
    "message": "...",
    "type": "runtime",
    "stack_trace": "..."
  }
}

Response:
{
  "debug_session_id": "debug-456",
  "diagnostics": [...],
  "ai_analysis": {...},
  "suggested_fixes": [...]
}
```

### 2. Apply Fix
```python
POST /api/scenarios/{scenario_id}/debug/{session_id}/apply-fix
Request:
{
  "fix_id": "fix-789",
  "confirm": true
}

Response:
{
  "success": bool,
  "applied_changes": [...],
  "validation_results": {...}
}
```

### 3. Chat with Claude
```python
POST /api/scenarios/{scenario_id}/debug/{session_id}/chat
Request:
{
  "message": "Why is the parameter not working?",
  "include_context": ["main.py", "Makefile"]
}

Response:
{
  "response": "...",
  "suggested_actions": [...]
}
```

### 4. Retest Scenario
```python
POST /api/scenarios/{scenario_id}/debug/{session_id}/retest
Request:
{
  "test_parameters": {"input": "/path/to/test.json"}
}

Response:
{
  "success": bool,
  "output": "...",
  "error": "..." | null
}
```

## Implementation Phases

### Phase 1: Core Diagnostics (Week 1)
- Implement 5 diagnostic tests
- Create DiagnosticResult model
- Add debug endpoint to backend
- Basic UI panel to show diagnostic results

### Phase 2: Claude SDK Integration (Week 2)
- Integrate Claude Code SDK for analysis
- Implement fix suggestion generation
- Create fix application engine
- Add fix preview to UI

### Phase 3: Interactive Chat (Week 3)
- Add Claude chat interface
- Context management for conversation
- File viewing in chat context
- Iterative fix refinement

### Phase 4: Auto-Fix Patterns (Week 4)
- Build common fix pattern library
- Implement safe auto-fix for known issues
- Add fix confirmation UI for complex changes
- Create fix history and rollback

## Common Issue Patterns & Fixes

### Pattern 1: @click.argument for file input
**Detection**: Regex finds `@click.argument.*type=click.Path`
**Fix**:
```python
# Before
@click.argument("input_file", type=click.Path(exists=True))

# After
@click.option("--input", "-i", type=click.Path(exists=True), required=True, help="Input file")
```

### Pattern 2: Makefile missing parameter handling
**Detection**: Makefile target exists but has no conditional parameter passing
**Fix**: Add conditional logic:
```makefile
CMD="uv run python -m scenarios.{name}";
if [ -n "$(INPUT)" ]; then CMD="$$CMD --input \"$(INPUT)\""; fi;
eval $$CMD
```

### Pattern 3: Missing dependencies
**Detection**: ImportError in execution
**Fix**:
```bash
uv add {missing_package}
```

### Pattern 4: Invalid Python syntax
**Detection**: compile() raises SyntaxError
**Fix**: Parse error location, show context, let Claude suggest fix

## Success Metrics

1. **Fix Success Rate**: % of issues automatically resolved
2. **Time to Resolution**: Average time from error to fixed
3. **User Intervention**: How often fixes require manual approval
4. **Pattern Coverage**: % of errors matching known patterns

## Future Enhancements

1. **Learning from Fixes**: Build ML model to predict fixes
2. **Proactive Validation**: Run diagnostics before execution
3. **Community Patterns**: Share fix patterns across installations
4. **Visual Diff View**: Show before/after code side-by-side
5. **Test Case Generation**: Auto-generate tests for fixed scenarios

## Example: Complete Debug Flow

```
User uploads JSON file in web UI → Error occurs
↓
System detects error: "Got unexpected extra argument"
↓
Debug mode activates automatically
↓
Runs diagnostics:
  - Parameter Discovery: FAILED (found @click.argument)
  - File Structure: PASSED
  - Dependencies: PASSED
  - Makefile: WARNING (no parameter handling)
↓
Sends to Claude SDK:
  - Error message
  - Diagnostic results
  - main.py content
  - Makefile excerpt
↓
Claude analyzes and returns:
  {
    "root_cause": "@click.argument not discoverable by web UI",
    "fixes": [
      {
        "type": "code_patch",
        "file": "main.py",
        "change": "Replace @click.argument with @click.option",
        "requires_confirmation": false
      },
      {
        "type": "makefile_update",
        "change": "Add parameter handling logic",
        "requires_confirmation": false
      }
    ]
  }
↓
UI shows debug panel with fixes
↓
User clicks "Apply All Fixes"
↓
System applies fixes:
  - Updates main.py
  - Updates Makefile
  - Validates changes
↓
Automatically retests scenario
↓
Success! Shows "✓ Scenario fixed and working"
```

## Implementation Priority

**High Priority** (must-have for MVP):
- Core diagnostics (parameter discovery, CLI test)
- Basic Claude SDK integration for analysis
- Fix suggestion generation
- Manual fix application

**Medium Priority** (nice-to-have for v1):
- Auto-fix for known patterns
- Interactive Claude chat
- Fix history and rollback
- Visual diff view

**Low Priority** (future enhancements):
- Pattern learning system
- Proactive validation
- Test case generation
- Community pattern sharing

## Next Steps

1. Review this design with team
2. Get user feedback on UI mockups
3. Prioritize features for MVP
4. Create implementation tasks
5. Build Phase 1 (Core Diagnostics)
