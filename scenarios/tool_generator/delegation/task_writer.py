"""Task specification writer for Claude Code delegation."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.specification import ToolSpec

logger = logging.getLogger(__name__)


class TaskWriter:
    """
    Writes task.json specification for Claude Code.

    Task format:
    {
        "tool_name": "content_analyzer",
        "requirements": "User's tool description",
        "validation_rules": [...],
        "reference_tools": [...],
        "constraints": {...},
        "working_dir": "/path/to/workspace"
    }
    """

    def write(self, spec: "ToolSpec", task_file: Path, workspace: Path) -> None:
        """
        Write task.json from ToolSpec.

        Args:
            spec: Tool specification
            task_file: Path to task.json
            workspace: Workspace directory path
        """
        task_data = spec.to_dict()
        task_data["working_dir"] = str(workspace)

        # Add generation instructions
        task_data["instructions"] = self._build_instructions(spec)

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Wrote task specification to {task_file}")

    def _build_instructions(self, spec: "ToolSpec") -> str:
        """
        Build detailed instructions for Claude Code.

        Includes:
        - Module structure rules (no duplicate-name nesting)
        - Session management pattern
        - All learnings from scenario-generator failures
        - Validation requirements
        - Reference to example tools
        - Pattern requirements
        """
        return f"""
Generate an amplifier CLI tool following these requirements:

{spec.requirements}

MODULE STRUCTURE RULES (CRITICAL - FOLLOW blog_writer PATTERN):

ALL tools use modular organization with functional modules:

✅ CORRECT - Modular structure (1-9 modules based on complexity):
  {spec.tool_name}/
  ├── main.py              # CLI orchestrator (ALWAYS at root!)
  ├── __init__.py          # Package marker
  ├── state.py             # State management (if stateful)
  ├── extractor/          # Functional module (verb-based naming)
  │   ├── __init__.py     # Exports module interface
  │   └── core.py         # Module implementation
  └── analyzer/           # Another functional module
      ├── __init__.py
      └── core.py

❌ WRONG - Duplicate-name nesting:
  {spec.tool_name}/
  └── {spec.tool_name}/   # ❌ NO! Don't duplicate tool name!
      └── main.py

CRITICAL RULES:
- main.py at tool root (coordinates modules)
- NO root core.py - logic lives in modules
- Functional module names: verb-based (extractor/, analyzer/, NOT pdf/, sentiment/)
- Scale from 1-9 modules based on complexity
- Each module: __init__.py + core.py
- NO duplicate-name nesting

MODULE COUNT GUIDANCE:
- Simple tools: 1-2 modules (e.g., extractor/, formatter/)
- Medium tools: 3-5 modules (e.g., blog_writer has 6)
- Complex tools: 6-9 modules (e.g., transcribe has 9)

RUNTIME DATA STORAGE (CRITICAL):
Generated tools MUST store runtime data in .data/{spec.tool_name}/sessions/

CORRECT directory structure:
```
# Generated tool code (discoverable by Web UI)
scenarios/{spec.tool_name}/
├── main.py              # CLI orchestrator
├── __init__.py          # Package marker
├── extractor/          # Functional module
│   ├── __init__.py
│   └── core.py
└── pyproject.toml

# Generated tool runtime data (when tool is executed)
.data/{spec.tool_name}/sessions/{{timestamp}}_{{guid}}/
├── state.json
├── results/
└── logs/
```

IMPLEMENTATION PATTERN:
```python
from pathlib import Path
from datetime import datetime
import uuid
import json

# Create session directory in .data/
base_dir = Path.cwd() / ".data" / "{spec.tool_name}" / "sessions"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
guid = uuid.uuid4().hex[:8]
session_dir = base_dir / f"{{timestamp}}_{{guid}}"
session_dir.mkdir(parents=True, exist_ok=True)

# Create 'latest' symlink for easy resume
latest_link = base_dir / "latest"
if latest_link.exists():
    latest_link.unlink()
latest_link.symlink_to(session_dir.name)

# Save state after EVERY operation
state_file = session_dir / "state.json"
state_file.write_text(json.dumps(state, indent=2))
```

CRITICAL - DO NOT:
- Store runtime data in scenarios/ directory (code only!)
- Store runtime data in tool's own directory
- Use relative paths (always use Path.cwd())

WORKFLOW VISUALIZATION METADATA (REQUIRED FOR WEB UI):

Add [tool.amplifier.workflow] section to pyproject.toml to enable pre-execution flow visualization in Web UI v2.

This metadata describes the workflow stages for React Flow visualization BEFORE execution.
It complements the runtime logger.stage_transition() calls that happen DURING execution.

EXAMPLE from blog_writer:
```toml
[tool.amplifier.workflow]
stages = [
    {{ id = "input_files", type = "input", label = "Input Files", prompt = "Select input files" }},
    {{ id = "extract_data", type = "process", label = "Extract Data", depends_on = ["input_files"] }},
    {{ id = "analyze", type = "process", label = "Analyze Content", depends_on = ["extract_data"] }},
    {{ id = "generate_output", type = "output", label = "Final Output", depends_on = ["analyze"] }}
]

[tool.amplifier.workflow.layout]
# Optional: Define node positions for flow diagram (x, y coordinates)
positions.input_files = [100, 100]
positions.extract_data = [350, 100]
positions.analyze = [600, 100]
positions.generate_output = [850, 100]
```

STAGE TYPES:
- "input": Initial data/parameter collection stages
- "process": Data processing/transformation stages
- "interaction": User review/approval checkpoints
- "output": Final result generation

CRITICAL RULES:
- Stage IDs must match logger.stage_transition() calls in code
- Use depends_on to define stage dependencies (creates edges in flow diagram)
- Layout positions are optional but improve visualization
- Flow left-to-right: inputs → processing → outputs

CRITICAL - WEB UI OUTPUT PATH HANDLING:

Tools receive output paths from Web UI in /tmp/amplifier_scenario_inputs/.
MUST create parent directories before writing to avoid silent failures.

✅ CORRECT - Always create parent dirs for user-provided output paths:
```python
# Handle output path parameter
if output_path is not None:
    output_path = Path(output_path)
    # REQUIRED: Create parent directory (Web UI doesn't pre-create it)
    output_path.parent.mkdir(parents=True, exist_ok=True)
else:
    # Default to session directory for CLI usage
    output_path = session_dir / "output.md"

# Now safe to write - parent directory exists
output_path.write_text(content)
```

❌ WRONG - Assuming parent directory exists (WILL FAIL WITH WEB UI):
```python
# Parent directory might not exist!
Path(output_path).write_text(content)  # ❌ Fails silently in async context
```

DATA LOCATION GUIDE:
- Session data (state, logs, intermediate files): .data/{{tool_name}}/sessions/{{id}}/
  - Persistent, tool-managed, survives execution
  - Use for: state.json, extracted_text.txt, intermediate_results.json
- Final output: Use path from --output parameter
  - Web UI provides: /tmp/amplifier_scenario_inputs/{{uuid}}/output.md (temporary)
  - CLI users provide: Custom paths or defaults to session_dir
  - ALWAYS create parent.mkdir(parents=True, exist_ok=True) before writing
- Both locations are valid and serve different purposes!

CRITICAL PATTERNS TO FOLLOW:
1. Use recursive file discovery: glob("**/*.ext") NOT glob("*.ext")
2. Validate minimum inputs: Check and fail early if insufficient
3. Show progress: Use logger.info() for each major step
4. Use defensive utilities: Import from amplifier.ccsdk_toolkit.defensive
5. Runtime validation FIRST: Test imports before static checks
6. DEFENSIVE LLM PARSING: Always type-guard parse_llm_json() results

CRITICAL - LLM RESPONSE PARSING WITH TYPE GUARDS:

When using parse_llm_json() from defensive utilities, ALWAYS add isinstance() check:

✅ CORRECT - Type guard immediately after parsing:
```python
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json

result = parse_llm_json(response)

# REQUIRED: Type guard before using result
if not isinstance(result, dict):
    logger.error("Expected dict from LLM, got invalid format")
    return None

# Now safe to use dict operations
if "field" not in result:
    logger.error("Missing required field")
    return None

value = result.get("key", "default")
```

❌ WRONG - Using result without type check (WILL FAIL TYPE CHECKING):
```python
result = parse_llm_json(response)  # Returns dict | list | None

# Type error! result could be list or None
if "field" not in result:  # ❌ Breaks with list/None
    return None

value = result.get("key")  # ❌ list has no .get() method
```

WHY THIS MATTERS:
- parse_llm_json() returns Union[dict, list, None] for defensive parsing
- You MUST check isinstance(result, dict) before dict operations
- Prevents type errors and runtime crashes
- pyright validation will fail without type guard

VALIDATION REQUIREMENTS:
{self._format_validation_rules(spec.validation_rules)}

REFERENCE TOOLS:
Study these examples for patterns:
{self._format_references(spec.reference_tools)}

WORKFLOW:
1. Generate tool structure (main.py at root, modules if needed, pyproject.toml)
2. Implement core functionality
3. Run validation loop:
   a. Install dependencies: cd <tool> && uv sync
   b. Test imports: python -c 'import <module>'
   c. Test CLI: python -m <tool> --help
   d. Check formatting: uv run ruff format --check .
   e. Check linting: uv run ruff check .
   f. Check types: uv run pyright .
   g. If errors, FIX THEM and retry
4. Iterate until all validations pass
5. Write result.json when complete

Use sub-agents as needed:
- zen-architect: Design decisions
- modular-builder: Code implementation
- bug-hunter: Debugging errors

Return result.json with:
- success: bool
- files_created: List[str]
- validation_passed: bool
- errors: List[str]
"""

    def _format_validation_rules(self, rules: list) -> str:
        """Format validation rules for instructions."""
        lines = []
        for rule in rules:
            req = "REQUIRED" if rule.required else "RECOMMENDED"
            lines.append(f"- [{req}] {rule.name}: {rule.check}")
        return "\n".join(lines)

    def _format_references(self, refs: list[Path]) -> str:
        """Format reference tool paths for instructions."""
        return "\n".join(f"- {ref.name} at {ref}" for ref in refs)
