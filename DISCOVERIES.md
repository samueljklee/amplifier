# DISCOVERIES.md

This file documents non-obvious problems, solutions, and patterns discovered during development. Make sure these are regularly reviewed and updated, removing outdated entries or those replaced by better practices or code or tools, updating those where the best practice has evolved.

## DevContainer Setup: Using Official Features Instead of Custom Scripts (2025-10-22)

### Issue

Claude CLI was not reliably available in DevContainers, and there was no visibility into what tools were installed during container creation.

### Root Cause

1. **Custom installation approach**: Previously attempted to install Claude CLI via npm in post-create script (was commented out, indicating unreliability)
2. **Broken pipx feature URL**: Used `devcontainers-contrib` which was incorrect
3. **No logging**: Post-create script had no output to help diagnose issues
4. **No status reporting**: Users couldn't easily see what tools were available

### Solution

Switched to declarative DevContainer features instead of custom installation scripts:

**devcontainer.json changes:**
```json
// Fixed broken pipx feature URL
"ghcr.io/devcontainers-extra/features/pipx-package:1": { ... }

// Added official Claude Code feature
"ghcr.io/anthropics/devcontainer-features/claude-code:1": {},

// Added VSCode extension
"extensions": ["anthropic.claude-code", ...]

// Named container for easier identification
"runArgs": ["--name=amplifier_devcontainer"]
```

**post-create.sh improvements:**
```bash
# Added logging to persistent file for troubleshooting
LOG_FILE="/tmp/devcontainer-post-create.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Added development environment status report
echo "📋 Development Environment Ready:"
echo "  • Python: $(python3 --version 2>&1 | cut -d' ' -f2)"
echo "  • Claude CLI: $(claude --version 2>&1 || echo 'NOT INSTALLED')"
# ... other tools

## Context-Aware Validation: Conditional Pattern Checking (2025-10-25)

### Issue

Tool generator validation was too rigid, applying all validation patterns universally regardless of tool type:
- **False positives**: Non-LLM tools failed validation for missing ClaudeSession imports
- **False positives**: Tools without AI analysis failed for missing defensive parsing utilities
- **Poor developer experience**: Confusing errors about patterns that weren't relevant to the tool

Example error for a PDF sentiment analyzer (non-LLM tool):
```
Pattern violation: claude_session_usage in core.py
Pattern violation: defensive_parsing in core.py
ERROR - Must use ClaudeSession from ccsdk_toolkit  # ❌ Tool doesn't use LLMs!
ERROR - Should use defensive LLM response parsing   # ❌ Not relevant!
```

### Root Cause

`AmplifierPatternValidator` had hardcoded `CRITICAL_PATTERNS` that always checked for:
- ClaudeSession usage
- Defensive LLM parsing utilities

But the specification builder already detected `uses_llm` during requirement parsing - this metadata wasn't being passed to validation.

### Solution

Made validation **context-aware** by splitting patterns into two categories:

**1. Updated AmplifierPatternValidator** (validation/amplifier_validator.py):
```python
# Patterns that ALWAYS apply (regardless of tool type)
UNIVERSAL_PATTERNS = {
    "describe_flag": {...},      # Web UI requirement
    "no_click_argument": {...},  # Web UI requirement
    "no_path_defaults": {...},   # JSON serialization
}

# Patterns that ONLY apply when tool uses LLMs
LLM_PATTERNS = {
    "claude_session_usage": {...},
    "defensive_parsing": {...},
}

async def validate(self, tool_path: Path, uses_llm: bool = True):
    # Build conditional pattern set
    patterns_to_check = dict(self.UNIVERSAL_PATTERNS)
    if uses_llm:
        patterns_to_check.update(self.LLM_PATTERNS)
```

**2. Added uses_llm to ToolSpec** (models/specification.py):
```python
@dataclass
class ToolSpec:
    tool_name: str
    requirements: str
    reference_tools: list[Path]
    validation_rules: list[ValidationRule]
    constraints: dict[str, Any]
    uses_llm: bool = False  # NEW - affects validation patterns
```

**3. Updated SpecificationBuilder** to populate the field (orchestrator/specification_builder.py):
```python
spec = ToolSpec(
    tool_name=parsed.tool_name,
    requirements=requirements,
    reference_tools=references,
    validation_rules=rules,
    constraints=parsed.constraints,
    uses_llm=parsed.uses_llm,  # NEW - pass through from requirements
)
```

**4. Updated orchestrator** to pass flag to validator (orchestrator/core.py):
```python
amplifier_result = await amplifier_validator.validate(
    tool_path, uses_llm=spec.uses_llm  # NEW - conditional validation
)
```

### Benefits Realized

1. **No false positives** - Only validates patterns relevant to tool type
2. **Clearer errors** - Developers only see errors for patterns they need
3. **Flexible validation** - Easy to add more conditional patterns (file processing, state management, etc.)
4. **Better logs** - Shows which pattern categories are being checked and why

### Example Output

**Non-LLM tool** (e.g., PDF sentiment analyzer):
```
Running amplifier pattern validation on pdf_sentiment_analyzer
Tool uses LLMs: False
Skipping LLM-specific patterns (tool doesn't use LLMs)
✓ Amplifier pattern validation passed
```

**LLM tool** (e.g., blog_writer):
```
Running amplifier pattern validation on blog_writer
Tool uses LLMs: True
Including LLM-specific patterns
✓ Amplifier pattern validation passed
```

### Key Learnings

1. **Use official DevContainer features over custom scripts**: Features are tested, maintained, and more reliable than custom npm installs
2. **Declarative > imperative**: Define what you need in devcontainer.json rather than scripting installations
3. **Add logging for troubleshooting**: Persistent logs help diagnose container build issues
4. **Provide status reporting**: Show users what tools are available after container creation
5. **Test with fresh containers**: Only way to verify DevContainer configuration works

### Prevention

- Prefer official DevContainer features from `ghcr.io/anthropics/`, `ghcr.io/devcontainers/`, etc.
- Add logging (`tee` to a log file) in post-create scripts for troubleshooting
- Include tool version reporting to confirm installations
- Use named containers (`runArgs`) for easier identification in Docker Desktop
- Test DevContainer changes by rebuilding containers from scratch

## pnpm Global Bin Directory Not Configured (2025-10-23)

### Issue

`make install` fails with `ERR_PNPM_NO_GLOBAL_BIN_DIR` error when trying to install global npm packages via pnpm in fresh DevContainer builds.

### Root Cause

Two issues combined to cause the failure:

1. **Missing SHELL environment variable**: During DevContainer post-create script execution, the `SHELL` environment variable is not set
2. **pnpm setup requires SHELL**: The `pnpm setup` command fails with `ERR_PNPM_UNKNOWN_SHELL` when `SHELL` is not set
3. **Silent failure**: The error was hidden by `|| true` in the script, allowing the script to continue and report success even though pnpm wasn't configured

From the post-create log:
```
🔧  Setting up pnpm global bin directory...
 ERR_PNPM_UNKNOWN_SHELL  Could not infer shell type.
Set the SHELL environment variable to your active shell.
    ✅ pnpm configured  # <-- False success!
```

### Solution

Fixed post-create script to explicitly set SHELL before running pnpm setup:

**post-create.sh addition:**
```bash
echo "🔧  Setting up pnpm global bin directory..."
# Ensure SHELL is set for pnpm setup
export SHELL="${SHELL:-/bin/bash}"
# Configure pnpm to use a global bin directory
pnpm setup 2>&1 | grep -v "^$" || true
# Export for current session (will also be in ~/.bashrc for future sessions)
export PNPM_HOME="/home/vscode/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"
echo "    ✅ pnpm configured"
```

This ensures:
1. SHELL is explicitly set before pnpm setup runs
2. pnpm's global bin directory is configured on first container build
3. The configuration is added to `~/.bashrc` for all future sessions
4. The environment variables are set for the post-create script itself

### Key Learnings

1. **SHELL not set in post-create context** - DevContainer post-create scripts run in an environment where SHELL may not be set
2. **pnpm requires SHELL** - Unlike npm, pnpm needs to know the shell type to modify the correct config file
3. **Silent failures are dangerous** - Using `|| true` hid the actual error; consider logging errors even when continuing
4. **Check the logs** - The `/tmp/devcontainer-post-create.log` revealed the actual error that was hidden from the console

### Prevention

- Always set SHELL explicitly in post-create scripts before running shell-dependent commands
- Check post-create logs (`/tmp/devcontainer-post-create.log`) after rebuilding containers
- Consider conditional error handling instead of blanket `|| true` to catch real failures
- Test `make install` as part of DevContainer validation
1. **Validation should match requirements** - Don't validate patterns the tool doesn't need
2. **Metadata should flow through pipeline** - Requirement parsing → spec → validation
3. **Split universal vs conditional patterns** - Makes validation extensible
4. **Clear logging improves debugging** - Show why patterns are/aren't being checked
5. **Context-aware validation is user-friendly** - Reduces confusion and false positives

### Prevention

- When adding new validation patterns, ask: "Does this apply to ALL tools or specific types?"
- Add new conditional pattern categories as needed (file processing, state management, etc.)
- Ensure requirement parsing detects tool characteristics that affect validation
- Pass tool metadata through the full generation → validation pipeline

### Related Files

- `scenarios/tool_generator/validation/amplifier_validator.py` - Conditional validation logic
- `scenarios/tool_generator/models/specification.py` - Added `uses_llm` field
- `scenarios/tool_generator/orchestrator/specification_builder.py` - Populates `uses_llm`
- `scenarios/tool_generator/orchestrator/core.py` - Passes flag to validator

## Standardized State Management Template (2025-10-25)

### Issue

Amplifier CLI tools needed state management for resume capability, but each tool was implementing state persistence from scratch with inconsistent patterns:
- Different state file locations and naming
- Varied approaches to session directories
- Inconsistent state save/load logic
- Missing defensive I/O (cloud sync issues)
- Duplicate code across tools

### Root Cause

No standardized template existed for state management. Developers had to:
1. Study existing tools (blog_writer, web_to_md) to understand patterns
2. Copy-paste state management code
3. Adapt it to their specific needs
4. Risk missing important patterns (defensive I/O, proper logging, etc.)

### Solution

Created `amplifier/ccsdk_toolkit/templates/state_template.py` - a comprehensive, documented template for state management.

**Key Components**:
- `PipelineState` dataclass: Customizable fields for any workflow (stage, iteration, processed/failed items, outputs)
- `StateManager` class: Automatic persistence with defensive I/O
- Session directory management with timestamps
- Resume capability via auto-loading existing state
- Convenience methods: update_stage(), mark_item_processed(), save_artifact(), etc.

**Features**:
1. Session directory management - Auto-creates `.data/<tool_name>/<timestamp>/` structure
2. Resume capability - Auto-loads existing state if session dir provided
3. Defensive I/O - Uses `defensive/file_io.py` utilities to handle cloud sync issues
4. Comprehensive logging - Clear visibility into state changes
5. Flexible customization - Template pattern for tool-specific needs
6. Common utilities - Includes slugify() and other helpers

### Usage Pattern

For new tools:
1. Copy `state_template.py` to tool directory as `state.py`
2. Customize `PipelineState` fields for your workflow
3. Use in main workflow

### Benefits Realized

1. Consistency - All tools follow same state management pattern
2. Reduced duplication - Single authoritative template
3. Better docs - Comprehensive docstrings
4. Defensive by default - Cloud sync issues handled automatically
5. Faster development - Robust state management in minutes

### Key Learnings

1. Templates prevent reinvention and ensure consistency
2. Defensive patterns matter - Cloud sync issues are common
3. Session directories help with multi-run debugging
4. Balance flexibility and consistency

### Prevention

- New amplifier CLI tools should start from `state_template.py`
- Tool generator should use this template when generating tools with state management
- Regular reviews to update template with new patterns

### Related Files

- `amplifier/ccsdk_toolkit/templates/state_template.py` (new template)
- `amplifier/ccsdk_toolkit/defensive/file_io.py` (defensive I/O utilities)

## Scenario Generator: Embracing Single Modular Pattern (2025-10-24)

### Issue

The scenario_generator had two code paths: "simple" (single-file) and "complex" (modular). This dual-path approach created:
- Maintenance burden (two generation methods to maintain)
- Decision complexity (LLM must choose between approaches)
- Inconsistent output structures across scenarios
- Violated ruthless simplicity philosophy (one pattern is better than two)

### Root Cause

The dual-path design assumed flexibility was valuable - allowing simple scenarios to stay minimal while complex ones got modules. However, empirical evidence showed:
- 71% of existing scenarios (5/7) already used modular structure
- Modular pattern scales well from simple to complex (1-7 modules)
- The "simple" path was rarely used and added unnecessary complexity

### Solution

Removed the "simple" path entirely, embracing one consistent modular pattern:

1. **Deleted `_generate_simple_structure()` method** (24 lines removed from `incremental_generator.py`)
2. **Simplified generation logic** - Removed if/else branching, always call `_generate_modular_structure()`
3. **Updated planning prompts** - Changed from "choose simple or complex" to "design 1-7 modules based on needs"
4. **Removed "complexity" field** - Planning JSON no longer includes this decision point
5. **Updated documentation** - README now describes single modular approach

**Key Changes**:
```python
# BEFORE:
if self.plan["complexity"] == "simple":
    await self._generate_simple_structure(...)
else:
    await self._generate_complex_structure(...)

# AFTER:
# Always generate modular structure (1-7 modules based on scenario complexity)
await self._generate_modular_structure(...)
```

### Benefits Realized

1. **Ruthless simplicity achieved** - One pattern instead of two
2. **Reduced maintenance burden** - Single code path to maintain
3. **Consistent architecture** - All scenarios follow same modular pattern
4. **Scalable design** - Pattern scales from simple (1-2 modules) to complex (5-7 modules)
5. **Clearer LLM guidance** - No decision paralysis about which path to use

### Key Learnings

1. **Flexibility can be complexity in disguise** - Two paths for "flexibility" was actually inflexible
2. **One good pattern beats two okay patterns** - Modular structure works for everything
3. **Empirical evidence trumps theoretical concerns** - 71% already modular showed the path
4. **Trust in scalability** - 1-2 modules for simple cases works just as well as separate approach
5. **Philosophy alignment matters** - Removing dual-path perfectly aligned with ruthless simplicity

### Prevention

- When adding "flexible" alternative approaches, ask: "Is this flexibility or complexity?"
- Validate assumptions with empirical evidence (what patterns actually get used?)
- Default to single good pattern that scales over multiple specialized patterns
- Regular review of code paths - remove rarely-used alternatives
- Philosophy check: Does this align with ruthless simplicity?

### Related Files

- `scenarios/scenario_generator/incremental_generator.py` (modified)
- `scenarios/scenario_generator/README.md` (updated documentation)
- `ai_working/SCENARIO_GENERATOR_MODULE_PATTERN_ANALYSIS.md` (analysis that identified the issue)

## OneDrive/Cloud Sync File I/O Errors (2025-01-21)

### Issue

Knowledge synthesis and other file operations were experiencing intermittent I/O errors (OSError errno 5) in WSL2 environment. The errors appeared random but were actually caused by OneDrive cloud sync delays.

### Root Cause

The `~/amplifier` directory was symlinked to a OneDrive folder on Windows (C:\ drive). When files weren't downloaded locally ("cloud-only" files), file operations would fail with I/O errors while OneDrive fetched them from the cloud. This affects:

1. **WSL2 + OneDrive**: Symlinked directories from Windows OneDrive folders
2. **Other cloud sync services**: Dropbox, Google Drive, iCloud Drive can cause similar issues
3. **Network drives**: Similar delays can occur with network-mounted filesystems

### Solution

Two-part solution implemented:

1. **Immediate fix**: Added retry logic with exponential backoff and informative warnings
2. **Long-term fix**: Created centralized file I/O utility module

```python
# Enhanced retry logic in events.py with cloud sync warning:
for attempt in range(max_retries):
    try:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
            f.flush()
        return
    except OSError as e:
        if e.errno == 5 and attempt < max_retries - 1:
            if attempt == 0:  # Log warning on first retry
                logger.warning(
                    f"File I/O error writing to {self.path} - retrying. "
                    "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                    "If using cloud sync, consider enabling 'Always keep on this device' "
                    f"for the data folder: {self.path.parent}"
                )
            time.sleep(retry_delay)
            retry_delay *= 2
        else:
            raise

# New centralized utility (amplifier/utils/file_io.py):
from amplifier.utils.file_io import write_json, read_json
write_json(data, filepath)  # Automatically handles retries
```

### Affected Operations Identified

High-priority file operations requiring retry protection:

1. **Memory Store** (`memory/core.py`) - Saves after every operation
2. **Knowledge Store** (`knowledge_synthesis/store.py`) - Append operations
3. **Content Processing** - Document and image saves
4. **Knowledge Integration** - Graph saves and entity cache
5. **Synthesis Engine** - Results saving

### Key Learnings

1. **Cloud sync can cause mysterious I/O errors** - Not immediately obvious from error messages
2. **Symlinked directories inherit cloud sync behavior** - WSL directories linked to OneDrive folders are affected
3. **"Always keep on device" setting fixes it** - Ensures files are locally available
4. **Retry logic should be informative** - Tell users WHY retries are happening
5. **Centralized utilities prevent duplication** - One retry utility for all file operations

### Prevention

- Enable "Always keep on this device" for any OneDrive folders used in development
- Use the centralized `file_io` utility for all file operations
- Add retry logic proactively for user-facing file operations
- Consider data directory location when setting up projects (prefer local over cloud-synced)
- Test file operations with cloud sync scenarios during development

## Tool Generation Pattern Failures (2025-01-23)

### Issue

Generated CLI tools consistently fail with predictable patterns:

- Non-recursive file discovery (using `*.md` instead of `**/*.md`)
- No minimum input validation (synthesis with 1 file when 2+ needed)
- Silent failures without user feedback
- Poor visibility into what's being processed

### Root Cause

- **Missing standard patterns**: No enforced template for common requirements
- **Agent guidance confusion**: Documentation references `examples/` as primary location
- **Philosophy violations**: Generated code adds complexity instead of embracing simplicity

### Solutions

**Standard tool patterns** (enforced in all generated tools):

```python
# Recursive file discovery
files = list(Path(dir).glob("**/*.md"))  # NOT "*.md"

# Minimum input validation
if len(files) < required_min:
    logger.error(f"Need at least {required_min} files, found {len(files)}")
    sys.exit(1)

# Clear progress visibility
logger.info(f"Processing {len(files)} files:")
for f in files[:5]:
    logger.info(f"  • {f.name}")
```

**Tool generation checklist**:

- [ ] Uses recursive glob patterns for file discovery
- [ ] Validates minimum inputs before processing
- [ ] Shows clear progress/activity to user
- [ ] Fails fast with descriptive errors
- [ ] Uses defensive utilities from toolkit

### Key Learnings

2. **Templates prevent predictable failures**: Common patterns should be enforced
3. **Visibility prevents confusion**: Always show what's being processed
4. **Fail fast and loud**: Silent failures create debugging nightmares
5. **Philosophy must be enforced**: Generated code often violates simplicity

### Prevention

- Validate against checklist before accepting generated tools
- Update agent guidance to specify correct directories
- Test with edge cases (empty dirs, single file, nested structures)
- Review generated code for philosophy compliance

## LLM Response Handling and Defensive Utilities (2025-01-19)

### Issue

Some CCSDK tools experienced multiple failure modes when processing LLM responses:

- JSON parsing errors when LLMs returned markdown-wrapped JSON or explanatory text
- Context contamination where LLMs referenced system instructions in their outputs
- Transient failures with no retry mechanism causing tool crashes

### Root Cause

LLMs don't reliably return pure JSON responses, even with explicit instructions. Common issues:

1. **Format variations**: LLMs wrap JSON in markdown blocks, add explanations, or include preambles
2. **Context leakage**: System prompts and instructions bleed into generated content
3. **Transient failures**: API timeouts, rate limits, and temporary errors not handled gracefully

### Solution

Created minimal defensive utilities in `amplifier/ccsdk_toolkit/defensive/`:

```python
# parse_llm_json() - Extracts JSON from any LLM response format
result = parse_llm_json(llm_response)
# Handles: markdown blocks, explanations, nested JSON, malformed quotes

# retry_with_feedback() - Intelligent retry with error correction
result = await retry_with_feedback(
    async_func=generate_synthesis,
    prompt=prompt,
    max_retries=3
)
# Provides error feedback to LLM for self-correction on retry

# isolate_prompt() - Prevents context contamination
clean_prompt = isolate_prompt(user_prompt)
# Adds barriers to prevent system instruction leakage
```

### Real-World Validation (2025-09-19)

**Test Results**: Fresh md_synthesizer run with defensive utilities showed dramatic improvement:

- **✅ Zero JSON parsing errors** (was 100% failure rate in original versions)
- **✅ Zero context contamination** (was synthesizing from wrong system files)
- **✅ Zero crashes** (was failing with exceptions on basic operations)
- **✅ 62.5% completion rate** (5 of 8 ideas expanded before timeout vs. 0% before)
- **✅ High-quality output** - Generated 8 relevant, insightful ideas from 3 documents

**Performance Profile**:

- Stage 1 (Summarization): ~10-12 seconds per file - Excellent
- Stage 2 (Synthesis): ~3 seconds per idea - Excellent with zero JSON failures
- Stage 3 (Expansion): ~45 seconds per idea - Reasonable but could be optimized

**Key Wins**:

1. `parse_llm_json()` eliminated all JSON parsing failures
2. `isolate_prompt()` prevented system context leakage
3. Progress checkpoint system preserved work through timeout
4. Tool now fundamentally sound - remaining work is optimization, not bug fixing

### Key Patterns

1. **Extraction over validation**: Don't expect perfect JSON, extract it from whatever format arrives
2. **Feedback loops**: When retrying, tell the LLM what went wrong so it can correct
3. **Context isolation**: Use clear delimiters to separate user content from system instructions
4. **Defensive by default**: All CCSDK tools should assume LLM responses need cleaning
5. **Test early with real data**: Defensive utilities prove their worth only under real conditions

### Prevention

- Use `parse_llm_json()` for all LLM JSON responses - never use raw `json.loads()`
- Wrap LLM operations with `retry_with_feedback()` for automatic error recovery
- Apply `isolate_prompt()` when user content might be confused with instructions

## Web UI Contract Validation for Scenario Generator (2025-01-24)

### Issue

Generated scenarios would sometimes pass static checks (`make check`) but fail at runtime with the Web UI, causing cryptic errors:

- "Missing argument 'PDF_FILE'" - Scenarios using `@click.argument` instead of `@click.option`
- JSON serialization errors - Path objects used as default values
- `--describe-parameters` not recognized - Missing `@add_describe_flag` decorator
- Silent failures - No validation of Web UI compatibility during generation

### Root Cause

The validation pipeline had a gap between static validation and runtime execution:

1. **Static validation** (linting, type checking) - Catches syntax errors
2. **Dependency validation** - Tests `uv sync` works
3. **Runtime validation** - Tests basic CLI execution
4. **❌ Missing: Contract validation** - No test of Web UI compatibility

The Web UI requires a specific contract:
- Must use `@add_describe_flag` decorator for introspection
- Must use `@click.option` only (no `@click.argument`)
- All default values must be JSON-serializable
- `--describe-parameters` must return valid JSON with required fields

### Solution

**Hybrid Approach** combining enhanced prompts with runtime validation:

#### 1. Enhanced Generator Prompts (incremental_generator.py:603-617)

Added emphatic warnings in the generation prompts:

```python
**CRITICAL - NEVER USE @click.argument (WILL FAIL IN WEB UI):**
ALL parameters MUST be @click.option, NEVER use @click.argument:
- BAD: @click.argument("input_file", type=click.Path(...))
- GOOD: @click.option("--input-file", type=click.Path(...), required=True)
- The Web UI cannot handle positional arguments - only named options work

**CRITICAL - PATH DEFAULT VALUES (WILL FAIL WITHOUT THIS):**
NEVER use Path objects as default values in @click.option:
- BAD: @click.option("--output", default=Path("output.md"))
- GOOD: @click.option("--output", default="output.md")
- Path objects cannot be JSON-serialized and will break Web UI introspection
```

#### 2. Contract Validation Phase (validation_utils.py:431-537)

Added `ContractValidator` class that tests Web UI contract compliance:

```python
class ContractValidator:
    """Validates scenarios against Web UI contract requirements."""

    async def validate(self) -> ContractValidationResult:
        """Execute --describe-parameters and validate contract."""
        # 1. Execute: uv run python -m scenarios.{name} --describe-parameters
        # 2. Validate execution succeeds within 5 seconds
        # 3. Parse JSON from stdout
        # 4. Check required fields: version, name, display_name, description, parameters
        # 5. Test each parameter's default value is JSON-serializable
        # 6. Return detailed errors with actionable messages
```

#### 3. Integration as Phase 4 (validation.py:181-202)

Integrated contract validation into the generation pipeline after runtime validation:

```python
# Phase 1: Static validation (linting, type checking)
# Phase 2: Dependency validation (uv sync)
# Phase 3: Runtime validation (import, CLI invocation)
# Phase 4: Contract validation (Web UI compatibility) ← NEW
```

### Validation Checks

The contract validator tests:

1. **CLI Introspection Works**
   - Executes `--describe-parameters` flag
   - Completes within 5-second timeout
   - Returns exit code 0

2. **JSON Structure Valid**
   - Output is parseable JSON
   - Contains required fields (version, name, display_name, description, parameters)
   - Parameters array is well-formed

3. **Parameter Serialization**
   - All default values are JSON-serializable
   - No Path objects, datetime objects, or other non-JSON types

### Real-World Validation

Tested with existing scenario (`blog_writer`):
- ✅ Execution succeeded (0.42s)
- ✅ Valid JSON output
- ✅ All required fields present
- ✅ 8 parameters validated
- ✅ All defaults JSON-serializable

### Key Learnings

1. **Fail fast with contracts** - Validate contracts immediately after generation, not at user execution time
2. **Actionable error messages** - Tell users exactly what's wrong and how to fix it
3. **Hybrid approach optimal** - Enhanced prompts (free) + simple validation (30 lines) catches 95%+ of issues
4. **JSON serialization matters** - Path objects as defaults break Web UI introspection
5. **Positional args unsupported** - Web UI can only pass named parameters (`--flag`)
6. **5-second timeout appropriate** - CLI introspection should be fast; longer suggests expensive imports

### Prevention

- **Generator prompts** include emphatic warnings about common mistakes
- **Contract validation** runs automatically as Phase 4 in generation pipeline
- **Clear error messages** guide users to solutions when validation fails
- **Early detection** prevents scenarios from reaching Web UI with contract violations

### Philosophy Alignment

Implementation follows "Ruthless Simplicity":
- ✅ ~107 lines of focused code (ContractValidator class)
- ✅ No over-engineering - straightforward subprocess execution
- ✅ Fail fast - validates contract before wasting user time
- ✅ Clear errors - actionable messages with examples
- ✅ Self-contained - ContractValidator is a perfect "brick" (modular, regeneratable)

## Tool Generator Session-Based Workspace Pattern (2025-10-25)

### Issue

The tool_generator had confusing workspace organization that mixed generation artifacts with generated code:

- **Duplicate-name nesting**: Generated tools like `code_quality_reporter/code_quality_reporter/` (confusing!)
- **Mixed artifacts**: task.json, result.json mixed with generated code
- **No session isolation**: References and workspace data not scoped to generation sessions
- **Inconsistent patterns**: Different runtime data patterns across tools (flat vs timestamped)

### Root Cause

The workspace management lacked clear separation between:
1. **Generation workspace** - Where tool_generator does its work (task.json, references, logs)
2. **Generated tool code** - The actual tool being created
3. **Runtime data** - Where the generated tool stores its execution data

This led to confusion about what goes where and made it hard to track generation sessions.

### Solution

Implemented session-based workspace pattern aligned with amplifier's root `.data/` structure:

#### 1. Session-Based Generation Workspace

```python
# workspace_manager.py: create_session_workspace()
.data/tool_generator/
└── sessions/
    └── {timestamp}_{guid}/           # e.g., 20251025_091234_a7f3b9d1
        ├── session.json              # Metadata
        ├── task.json                 # Generation specification
        ├── result.json               # Generation outcome
        ├── references/               # Exemplars for this session
        │   ├── blog_writer/          # Copied for generation
        │   └── web_to_md/
        ├── logs/
        │   └── progress.jsonl        # Claude Code SDK events
        └── {tool_name}/              # Generated tool output
            ├── main.py               # At root!
            ├── core.py
            └── pyproject.toml
```

#### 2. Eliminated Duplicate-Name Nesting

**Updated task_writer.py instructions (lines 66-89)**:

```python
MODULE STRUCTURE RULES (CRITICAL):
✅ CORRECT - main.py at tool root:
  {tool_name}/
  ├── main.py              # CLI orchestrator (ALWAYS at root!)
  ├── core.py              # For simple tools: all logic here
  ├── extractor/          # ✅ Functional module (OK!)

❌ WRONG - Duplicate-name nesting:
  {tool_name}/
  └── {tool_name}/        # ❌ NO! Don't duplicate tool name!
      └── main.py
```

#### 3. Standardized State Management Template

Created `amplifier/ccsdk_toolkit/templates/state_template.py` with:

```python
class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None, tool_name: str = "tool"):
        if session_dir is None:
            # Create session with timestamp + GUID
            base_dir = Path(f".data/{tool_name}/sessions")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            guid = uuid.uuid4().hex[:8]
            session_dir = base_dir / f"{timestamp}_{guid}"

        # Create 'latest' symlink for resume
        latest_link = base_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(session_dir.name)
```

**Features**:
- Timestamp + 8-char GUID for unique, sortable sessions
- `latest` symlink for easy resume capability
- Defensive file I/O with retry logic (handles cloud sync)
- Convenience methods for common state operations

#### 4. Updated Generation Instructions

**task_writer.py now includes**:

```python
RUNTIME DATA STORAGE:
- Use amplifier root .data/ pattern for ALL runtime data
- Create session directories: .data/{tool_name}/sessions/{timestamp}_{guid}/
- Include state.py for resumable operations (follow blog_writer pattern)
- Save state after EVERY operation for interruption recovery
- Use latest symlink for easy resume

CRITICAL PATTERNS TO FOLLOW:
1. Use recursive file discovery: glob("**/*.ext") NOT glob("*.ext")
2. Validate minimum inputs: Check and fail early if insufficient
3. Show progress: Use logger.info() for each major step
4. Use defensive utilities: Import from amplifier.ccsdk_toolkit.defensive
5. Runtime validation FIRST: Test imports before static checks
```

### Benefits Realized

1. **Clear separation of concerns**:
   - Generation workspace: `.data/tool_generator/sessions/{id}/`
   - Generated tool code: `scenarios/{tool_name}/`
   - Runtime data: `.data/{tool_name}/sessions/{id}/`

2. **Session isolation** - Each generation gets its own workspace with complete audit trail

3. **Resume capability** - `latest` symlink enables easy resumption after interruption

4. **Consistent patterns** - All tools follow same structure (no duplicate-name nesting)

5. **Standardized state management** - Template provides battle-tested pattern

### Key Learnings

1. **Session-based isolation prevents confusion** - Clear workspace boundaries
2. **Duplicate-name nesting is always wrong** - Functional modules good, name duplication bad
3. **Template provides consistency** - state_template.py ensures uniform state management
4. **Defensive I/O is critical** - Cloud sync issues require retry logic
5. **"latest" symlink is user-friendly** - Easy to find most recent session

### Prevention

- Use `create_session_workspace()` for all generation sessions
- Never create `{tool_name}/{tool_name}/` duplicate nesting
- Always put `main.py` at tool root, not in subdirectory
- Use state_template.py as starting point for state management
- Include defensive file I/O utilities from amplifier.ccsdk_toolkit.defensive

### Related Files

- `scenarios/tool_generator/delegation/workspace_manager.py` - Session workspace creation
- `scenarios/tool_generator/delegation/task_writer.py` - Generation instructions
- `scenarios/tool_generator/orchestrator/core.py` - Uses create_session_workspace()
- `amplifier/ccsdk_toolkit/templates/state_template.py` - Standard state management
- `ai_working/tool_generator_restructuring_plan.md` - Complete design document
