"""Core orchestrator for tool generation workflow."""

import json
import os
from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions, ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat

from ..delegation.result_reader import ResultReader
from ..delegation.task_writer import TaskWriter
from ..delegation.workspace_manager import WorkspaceManager
from ..models.generation import GenerationResult
from ..models.generation import ValidationResult
from ..models.specification import ToolSpec
from ..validation.amplifier_validator import AmplifierPatternValidator
from ..validation.dependency_validator import DependencyValidator
from ..validation.pattern_validator import PatternValidator
from ..validation.runtime_validator import RuntimeValidator
from ..validation.static_validator import StaticValidator
from .specification_builder import SpecificationBuilder

# Environment-aware logging: JSON for Web UI, plain text for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger("tool_generator.orchestrator", format=log_format)


class ToolGenerationOrchestrator:
    """
    Orchestrates end-to-end tool generation workflow.

    Workflow:
    1. Parse requirements → ToolSpec (SpecificationBuilder)
    2. Create workspace (WorkspaceManager)
    3. Write task.json (TaskWriter)
    4. Delegate to Claude Code SDK (ccsdk_toolkit)
    5. Monitor progress (progress.jsonl)
    6. Read results (ResultReader)
    7. Validate generated tool (RuntimeValidator, StaticValidator, PatternValidator)
    8. Iterate if needed (up to max_iterations)
    """

    def __init__(
        self: "ToolGenerationOrchestrator",
        scenarios_dir: Path,
        workspace_base: Path | None = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            scenarios_dir: Path to scenarios/ directory
            workspace_base: Base directory for workspaces
        """
        self.scenarios_dir = scenarios_dir
        self.workspace_mgr = WorkspaceManager(workspace_base)
        self.spec_builder = SpecificationBuilder(scenarios_dir)
        self.task_writer = TaskWriter()
        self.result_reader = ResultReader()

        logger.info("ToolGenerationOrchestrator initialized")

    async def generate(
        self: "ToolGenerationOrchestrator", requirements: str, max_iterations: int = 2
    ) -> GenerationResult:
        """
        Generate tool from requirements with iterative refinement.

        Args:
            requirements: User's tool description
            max_iterations: Maximum refinement iterations

        Returns:
            GenerationResult with final status
        """
        logger.info("=" * 60)
        logger.info("Starting tool generation")
        logger.info("=" * 60)

        # Stage transition: Starting → Specification
        logger.stage_transition(None, "specification", estimated_duration=15)

        # 1. Build specification
        logger.info("Phase 1: Building specification")
        spec = await self.spec_builder.build(requirements)
        logger.info(f"Tool name: {spec.tool_name}")
        logger.info(f"Validation rules: {len(spec.validation_rules)}")
        logger.info(f"Reference tools: {len(spec.reference_tools)}")

        # Stage transition: Specification → Workspace
        logger.stage_transition("specification", "workspace", estimated_duration=5)

        # 2. Create session-based workspace
        logger.info("Phase 2: Creating session workspace")
        workspace = self.workspace_mgr.create_session_workspace(spec.tool_name)
        logger.info(f"Session workspace: {workspace}")
        logger.info(f"  references/ -> {workspace / 'references'}")
        logger.info(f"  logs/ -> {workspace / 'logs'}")

        # Copy reference tools
        self.workspace_mgr.copy_reference_tools(workspace, spec.reference_tools)

        # 3. Iterative generation loop
        validation = ValidationResult(
            passed=False, stage="not_started", errors=["Generation not attempted"]
        )

        for iteration in range(1, max_iterations + 1):
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Iteration {iteration}/{max_iterations}")
            logger.info("=" * 60)

            # Write task specification
            task_file = self.workspace_mgr.get_task_file(workspace)
            self.task_writer.write(spec, task_file, workspace)

            # Stage transition: Workspace → Generation
            logger.stage_transition("workspace", "generation", estimated_duration=180)

            # Delegate to CCSDK agent
            logger.info("Phase 3: Delegating to CCSDK agent")
            success = await self._delegate_to_claude_code(workspace, spec, iteration)

            if not success:
                logger.error("CCSDK agent delegation failed")
                continue

            # Read result
            logger.info("Phase 4: Reading generation result")
            result_file = self.workspace_mgr.get_result_file(workspace)
            result = self.result_reader.read(result_file)

            if not result.success:
                logger.warning(f"Generation failed: {result.errors}")
                spec = self._refine_spec_with_errors(spec, result.errors or [])
                continue

            # Stage transition: Generation → Validation
            logger.stage_transition("generation", "validation", estimated_duration=30)

            # Validate generated tool (now in scenarios/ directly)
            logger.info("Phase 5: Validating generated tool")
            tool_path = self.scenarios_dir / spec.tool_name

            validation = await self._validate_tool(tool_path, spec)

            if validation.passed:
                # Stage transition: Validation → Complete
                logger.stage_transition("validation", "complete", estimated_duration=0)

                logger.info("")
                logger.info("=" * 60)
                logger.info("✅ TOOL GENERATION SUCCESSFUL")
                logger.info("=" * 60)
                logger.info(f"Tool: {spec.tool_name}")
                logger.info(f"Location: {tool_path}")
                logger.info(f"Iterations: {iteration}")

                # Emit file.created events for generated code files (exclude build artifacts)
                BUILD_ARTIFACT_PATTERNS = [
                    ".venv/",
                    "__pycache__/",
                    ".pytest_cache/",
                    ".ruff_cache/",
                    "node_modules/",
                    ".git/",
                ]

                for file_path in tool_path.rglob("*.py"):
                    rel_path = file_path.relative_to(self.scenarios_dir.parent)
                    path_str = str(rel_path)

                    # Skip build artifacts
                    if any(pattern.rstrip("*") in path_str for pattern in BUILD_ARTIFACT_PATTERNS):
                        continue

                    logger.info(f"Generated file: {rel_path}")

                return GenerationResult(
                    success=True,
                    tool_path=tool_path,
                    validation=validation,
                    iterations=iteration,
                    files_created=result.files_created,
                )

            # Validation failed - clean up and retry
            logger.warning(f"Validation failed: {validation.errors}")

            # Clean up failed tool from scenarios/
            import shutil

            if tool_path.exists():
                logger.info(f"Cleaning up failed tool from: {tool_path}")
                shutil.rmtree(tool_path)

            spec = self._refine_spec_with_errors(spec, validation.errors)

        # Max iterations reached
        logger.error("")
        logger.error("=" * 60)
        logger.error("❌ TOOL GENERATION FAILED")
        logger.error("=" * 60)
        logger.error(f"Max iterations ({max_iterations}) reached")

        return GenerationResult(
            success=False,
            tool_path=None,
            validation=validation,
            iterations=max_iterations,
            errors=["Max refinement iterations reached without success"],
        )

    async def _delegate_to_claude_code(
        self: "ToolGenerationOrchestrator",
        workspace: Path,
        spec: ToolSpec,
        iteration: int = 1,
    ) -> bool:
        """
        Delegate tool generation to CCSDK toolkit agent.

        Uses ccsdk_toolkit to invoke Claude agent with the task specification.
        The agent will:
        - Read task.json
        - Generate code files directly in scenarios/
        - Run validations
        - Fix errors

        This method then writes result.json based on what Claude created.

        Args:
            workspace: Session workspace directory (for metadata/logs)
            spec: Tool specification
            iteration: Current iteration number (for session tracking)

        Returns:
            True if delegation succeeded and files were created
        """
        logger.info("Invoking CCSDK agent for tool generation...")

        # Read task specification
        task_file = self.workspace_mgr.get_task_file(workspace)
        with open(task_file) as f:
            task_content = f.read()

        # Target directory for generated tool (in scenarios/)
        tool_target = self.scenarios_dir / spec.tool_name

        # Build prompt for Claude Code SDK
        prompt = f"""Generate an amplifier CLI tool: {spec.tool_name}

⭐ CRITICAL: Model your implementation after @scenarios/blog_writer/ - THE exemplar ⭐

WORKSPACE SETUP:
- Session workspace: {workspace} (for metadata and reference tools)
- Create tool files in: {tool_target}/
- Reference exemplars in: {workspace}/references/ (blog_writer, transcribe, web_to_md)
- Tool will be created directly in scenarios/ directory (final location)

CRITICAL STRUCTURE RULES (FOLLOW blog_writer - 100% of tools use this pattern):
✅ CORRECT - Modular structure (NO root core.py):
  {spec.tool_name}/
  ├── main.py              # CLI orchestrator (ALWAYS at root!)
  ├── __init__.py          # Package marker
  ├── extractor/          # Functional module (verb-based naming)
  │   ├── __init__.py
  │   └── core.py         # Logic lives HERE, not at root!
  └── analyzer/           # Another functional module
      ├── __init__.py
      └── core.py

❌ WRONG - Duplicate-name nesting:
  {spec.tool_name}/
  └── {spec.tool_name}/   # ❌ NO! Don't duplicate tool name!
      └── main.py

CRITICAL: NO root core.py - All tools use modular pattern (1-9 modules)

TASK SPECIFICATION:
{task_content}

═══════════════════════════════════════════════════════════════════════════════
STEP 1: QUICK STUDY (30 seconds - SKIM ONLY, don't read entire files)
═══════════════════════════════════════════════════════════════════════════════

QUICKLY skim these key patterns from references/blog_writer/:

1. main.py - Look for:
   - @add_describe_flag decorator
   - @click.option patterns (NEVER @click.argument)
   - String defaults only

2. core.py - Look for:
   - ClaudeSession import and usage
   - async with pattern

DO NOT read entire files - just note the import statements and decorator patterns.
SPEND NO MORE THAN 2-3 Read tool calls here. Then IMMEDIATELY start creating files.

═══════════════════════════════════════════════════════════════════════════════
STEP 1.5: DESIGN YOUR MODULES (Modular Design Philosophy)
═══════════════════════════════════════════════════════════════════════════════

Following the "bricks and studs" philosophy, ALL tools use modular organization:

**THE CANONICAL PATTERN (used by 100% of existing tools):**
  ```
  {spec.tool_name}/
  ├── main.py              # CLI orchestrator (coordinates modules)
  ├── __init__.py          # Package marker
  ├── state.py             # State management (if stateful)
  ├── module_1/           # Functional module (verb-based name)
  │   ├── __init__.py
  │   └── core.py
  └── module_2/           # Another functional module
      ├── __init__.py
      └── core.py
  ```

**MODULE COUNT GUIDANCE:**
Scale your tool from 1-9 modules based on complexity:

- **Simple tools: 1-2 modules**
  - Example: `extractor/`, `formatter/`
  - Total < 300 lines of logic

- **Medium tools: 3-5 modules**
  - Example: blog_writer has 6 modules
  - Each module has distinct responsibility

- **Complex tools: 6-9 modules**
  - Example: transcribe has 9 modules
  - Multiple processing stages

**blog_writer example (6 modules - reference this structure):**
```
blog_writer/
├── main.py                 # Orchestrator (coordinates modules)
├── blog_writer/           # Core writing logic
├── style_extractor/       # Extract style patterns
├── source_reviewer/       # Review source materials
├── style_reviewer/        # Review against style guide
└── user_feedback/         # Handle user interaction
```

**MODULE DESIGN PRINCIPLES:**
1. **Functional naming** - Verb-based: extractor/, analyzer/, formatter/ (NOT pdf/, sentiment/)
2. **Each module is a "brick"** - Self-contained, regeneratable independently
3. **Interfaces are "studs"** - `__init__.py` exports what others use
4. **One clear responsibility** - If you can name it clearly, it's a module

**MODULE INTERFACE PATTERN:**
Each module's `__init__.py` should export its primary class/function:
```python
# my_module/__init__.py
from .core import MyModuleClass

__all__ = ["MyModuleClass"]
```

**YOUR MODULE PLAN:**
Based on the task specification, decide how many modules (1-9):
- List functional responsibilities (e.g., "extract data", "analyze content", "format output")
- Each responsibility becomes a module with verb-based name
- Example: extractor/, analyzer/, formatter/

═══════════════════════════════════════════════════════════════════════════════
STEP 2: CREATE MODULAR TOOL STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

Create these files following the canonical pattern:

1. {spec.tool_name}/__init__.py
   - Empty or minimal exports

2. {spec.tool_name}/__main__.py
   - Import and call main()

3. {spec.tool_name}/main.py - CLI ORCHESTRATOR
   Coordinates modules. **CRITICAL PATTERNS** (from blog_writer):
   ```python
   import click
   from amplifier.ccsdk_toolkit.cli_utils import add_describe_flag
   from amplifier.utils.logger import get_logger

   # Import your modules
   from .extractor import Extractor
   from .analyzer import Analyzer

   @click.command()
   @add_describe_flag  # REQUIRED for Web UI introspection
   @click.option("--input", required=True, help="Input description")
   @click.option("--output", default="output.json", help="Output file")
   # NEVER use @click.argument - breaks Web UI
   # NEVER use default=Path() - breaks introspection, use strings
   def main(input: str, output: str):
       \"\"\"Clear, focused tool description.\"\"\"
       # Coordinate modules
       extractor = Extractor()
       analyzer = Analyzer()

       data = asyncio.run(extractor.extract(input))
       results = asyncio.run(analyzer.analyze(data))
   ```

4. FOR EACH MODULE: Create subdirectory with __init__.py and core.py
   Example: {spec.tool_name}/extractor/

   **Module __init__.py**:
   ```python
   from .core import Extractor
   __all__ = ["Extractor"]
   ```

   **Module core.py** (with LLM logic):
   ```python
   from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
   from amplifier.utils.logger import get_logger

   class Extractor:
       async def extract(self, input_data):
           options = SessionOptions(system_prompt="Extract data")
           async with ClaudeSession(options) as claude:
               response = await claude.query(f"Extract: {{input_data}}")
               return response.content
   ```

5. {spec.tool_name}/pyproject.toml
   **REQUIRED DEPENDENCIES**:
   ```toml
   [project]
   name = "{spec.tool_name}"
   version = "0.1.0"
   dependencies = [
       "amplifier",
       "click>=8.0",
       "pydantic>=2.0"
   ]

   [tool.uv.sources]
   amplifier = {{ path = "../../", editable = true }}
   ```

6. {spec.tool_name}/README.md
   **Match blog_writer quality**: purpose, quick start, examples, troubleshooting

7. {spec.tool_name}/HOW_TO_CREATE_YOUR_OWN.md
   **Learning guide**: why tool exists, key patterns, how to adapt

**KEY BENEFITS OF THIS PATTERN:**
- Each module is a regeneratable "brick"
- Clear separation of concerns
- Easier to test and maintain
- Scales from 1-9 modules seamlessly
- Modules can be reused in other tools
- Perfect alignment with "bricks and studs" philosophy

═══════════════════════════════════════════════════════════════════════════════
STEP 3: VALIDATION LOOP
═══════════════════════════════════════════════════════════════════════════════

After creating files, validate and fix:

1. cd {spec.tool_name} && uv sync
2. python -c "import {spec.tool_name}"
3. python -m {spec.tool_name} --help
4. uv run ruff format --check .
5. uv run ruff check .
6. uv run pyright .

If ANY validation fails:
- Read the error carefully
- Fix the specific issue with Edit tool
- Re-run validation
- Repeat until ALL pass

═══════════════════════════════════════════════════════════════════════════════
CRITICAL REMINDERS
═══════════════════════════════════════════════════════════════════════════════

❌ NEVER - THESE WILL CAUSE VALIDATION FAILURE:
- Use @click.argument (breaks Web UI)
- Use Path() as default value (breaks introspection)
- Skip @add_describe_flag decorator
- Create placeholder/stub/mock code
- Use TODO comments or "implement this later" notes
- Comment out imports with "# TODO: install library"
- Use NotImplementedError or pass as implementation
- Skip README.md or HOW_TO_CREATE_YOUR_OWN.md
- Forget to run `uv sync` after creating pyproject.toml

✅ ALWAYS - PRODUCTION-READY CODE ONLY:
- Study blog_writer patterns first (2-3 Read calls maximum)
- Use @click.option for ALL parameters
- Use ClaudeSession from ccsdk_toolkit
- Include defensive parsing (parse_llm_json)
- Import ALL required libraries in pyproject.toml
- Run `uv sync` immediately after creating pyproject.toml
- Test imports work: `python -c "import {spec.tool_name}"`
- Write COMPLETE, WORKING implementations
- Match blog_writer documentation quality
- Fix ALL validation errors before finishing

CRITICAL: This tool must solve the user's problem completely.
No mocks, no placeholders, no "TODO: implement". Working code only.

After creating files, IMMEDIATELY run validation checks:
1. cd {spec.tool_name} && uv sync               # Install dependencies
2. python -c "import {spec.tool_name}"          # Test imports
3. python -m {spec.tool_name} --help            # Test CLI
4. uv run ruff format --check .                 # Check formatting
5. uv run ruff check .                          # Check linting
6. uv run pyright .                             # Check types

START BY READING blog_writer files, THEN create your tool following those exact patterns."""

        try:
            # Configure CCSDK agent session with full tool access
            # Iteration-based escalation: Start conservative (50), double if needed (100)
            # Override via TOOL_GEN_MAX_TURNS env var for testing/special cases
            try:
                env_max_turns = os.getenv("TOOL_GEN_MAX_TURNS")
                if env_max_turns:
                    max_turns = int(env_max_turns)
                    logger.info(f"Using TOOL_GEN_MAX_TURNS override: {max_turns}")
                else:
                    # Pragmatic escalation: 50 → 100
                    max_turns = 50 if iteration == 1 else 100
                    estimated_cost = max_turns * 0.03
                    logger.info(
                        f"Iteration {iteration}: max_turns={max_turns} (~${estimated_cost:.2f} budget)"
                    )
            except ValueError:
                logger.warning(
                    "Invalid TOOL_GEN_MAX_TURNS value, using iteration-based default"
                )
                max_turns = 50 if iteration == 1 else 100

            progress_buffer = []
            turn_indicators = {
                "turn_count": 0,
                "last_action": "starting",
                "max_turns": max_turns,
            }

            def log_progress(text: str) -> None:
                """Log agent progress, buffering until complete sentences."""
                progress_buffer.append(text)
                full_text = "".join(progress_buffer)

                # Estimate turn by detecting tool action patterns
                # Each tool mention likely indicates a turn boundary
                tool_patterns = [
                    "Let me",
                    "I'll",
                    "Now let me",
                    "Now create",
                    "Now run",
                ]
                if any(pattern in text for pattern in tool_patterns):
                    turn_indicators["turn_count"] += 1
                    turn_indicators["last_action"] = text[:50]

                    # Warn when approaching turn limit
                    max_turns_val = turn_indicators.get("max_turns", 50)
                    current_turn = turn_indicators["turn_count"]
                    if current_turn > int(max_turns_val * 0.8):  # 80% threshold
                        logger.warning(
                            f"⚠️  Approaching turn limit: {current_turn}/{max_turns_val} "
                            f"({int(current_turn / max_turns_val * 100)}% used)"
                        )

                # Log complete sentences (ending with period, colon, or newline)
                if text.endswith((".", ":", "\n")) or len(full_text) > 200:
                    turn_est = turn_indicators["turn_count"]
                    max_turns_val = turn_indicators.get("max_turns", 50)
                    logger.info(
                        f"[Agent Turn ~{turn_est}/{max_turns_val}] {full_text.strip()}"
                    )
                    progress_buffer.clear()

            options = SessionOptions(
                system_prompt="You are an expert at generating well-structured, tested CLI tools.",
                max_turns=max_turns,  # Configurable via TOOL_GEN_MAX_TURNS env var (default: 50)
                retry_attempts=3,
                allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"],
                permission_mode="bypassPermissions",
                cwd=str(self.scenarios_dir.parent),  # Changed: work from project root
                stream_output=False,  # Disable stdout streaming (use progress callback instead)
                progress_callback=log_progress,
            )

            async with ClaudeSession(options) as session:
                response = await session.query(prompt)

                logger.info("CCSDK agent completed generation")
                logger.info(f"Response success: {response.success}")
                logger.info(f"Response error: {response.error}")
                logger.info(f"Response metadata: {response.metadata}")

                # Extract and save session_id for potential resume
                session_id = response.metadata.get("session_id")
                if session_id:
                    logger.info(f"Claude session ID: {session_id}")
                    session_info_file = workspace / "session_info.json"
                    message_count = response.metadata.get("message_count", 0)
                    session_info = {
                        "session_id": session_id,
                        "tool_name": spec.tool_name,
                        "iteration": iteration,
                        "cost_usd": response.metadata.get("total_cost_usd", 0.0),
                        "duration_ms": response.metadata.get("duration_ms", 0),
                        "message_count": message_count,
                        "max_turns": max_turns,
                        "turn_utilization_pct": int(message_count / max_turns * 100)
                        if max_turns > 0
                        else 0,
                        "hit_turn_limit": message_count >= max_turns,
                    }
                    with open(session_info_file, "w") as f:
                        json.dump(session_info, f, indent=2)
                    logger.info(f"Session info saved to: {session_info_file}")
                else:
                    logger.warning("No session_id in response metadata")

                logger.info(
                    f"Response content length: {len(response.content) if response.content else 0}"
                )
                logger.info(
                    f"Message count: {response.metadata.get('message_count', 'unknown')}"
                )
                logger.info(
                    f"Response content (first 500 chars):\n{response.content[:500] if response.content else 'None'}..."
                )
                if len(response.content) > 500:
                    logger.info(
                        f"Response content (last 500 chars):\n...{response.content[-500:]}"
                    )
                else:
                    logger.warning(
                        "⚠️  Response content is very short - agent may not have completed execution"
                    )

                # Check what files were actually created (in scenarios/ directly)
                tool_dir = tool_target  # Changed: check in scenarios/ not workspace
                files_created = []
                errors = []
                success = False

                # Patterns for build artifacts to exclude from user-facing count
                BUILD_ARTIFACT_PATTERNS = [
                    ".venv/",
                    "__pycache__/",
                    ".pytest_cache/",
                    "*.pyc",
                    ".ruff_cache/",
                    "uv.lock",
                ]

                if tool_dir.exists():
                    # Categorize files: source vs build artifacts
                    source_files = []
                    build_artifacts = []

                    for file_path in tool_dir.rglob("*"):
                        if not file_path.is_file():
                            continue

                        rel_path = file_path.relative_to(self.scenarios_dir.parent)
                        path_str = str(rel_path)

                        # Check if this is a build artifact
                        is_build_artifact = any(
                            pattern.rstrip("*") in path_str
                            for pattern in BUILD_ARTIFACT_PATTERNS
                        )

                        if is_build_artifact:
                            build_artifacts.append(path_str)
                        else:
                            source_files.append(path_str)

                    # Use source files as the primary count
                    files_created = source_files

                    if source_files:
                        success = True
                        logger.info(
                            f"Found {len(source_files)} source files, "
                            f"{len(build_artifacts)} build artifacts"
                        )
                    else:
                        errors.append(f"Tool directory {tool_dir} exists but is empty")
                        logger.warning("Tool directory exists but contains no files")
                else:
                    errors.append(f"Tool directory {tool_dir} was not created")
                    logger.error(f"Tool directory was not created: {tool_dir}")

                # Check response for error indicators
                if response.error:
                    errors.append(f"Agent error: {response.error}")
                    success = False

                # Write result.json for the orchestrator to read
                result_file = self.workspace_mgr.get_result_file(workspace)
                result_data = {
                    "success": success,
                    "tool_name": spec.tool_name,
                    "files_created": files_created,
                    "validation_passed": False,  # Will be validated in next phase
                    "validation_details": {},
                    "errors": errors,
                }

                with open(result_file, "w") as f:
                    json.dump(result_data, f, indent=2)

                logger.info(f"Wrote result.json: {result_file}")
                return success

        except Exception as e:
            logger.error(f"CCSDK agent delegation failed: {e}")

            # Write error result.json
            result_file = self.workspace_mgr.get_result_file(workspace)
            result_data = {
                "success": False,
                "tool_name": spec.tool_name,
                "files_created": [],
                "validation_passed": False,
                "validation_details": {},
                "errors": [f"Exception during generation: {str(e)}"],
            }

            with open(result_file, "w") as f:
                json.dump(result_data, f, indent=2)

            return False

    async def _validate_tool(
        self: "ToolGenerationOrchestrator", tool_path: Path, spec: ToolSpec
    ) -> ValidationResult:
        """
        Run four-tier validation on generated tool.

        Order: Runtime → Amplifier Patterns → Static → Custom Pattern (fail fast)

        Args:
            tool_path: Path to generated tool
            spec: Tool specification with validation rules

        Returns:
            ValidationResult from first failing stage or success
        """
        # 1. Runtime validation (FIRST - most critical)
        runtime_validator = RuntimeValidator()
        runtime_result = await runtime_validator.validate(tool_path)

        if not runtime_result.passed:
            logger.error("Runtime validation failed")
            return runtime_result

        # 2. Amplifier pattern validation (SECOND - critical patterns)
        amplifier_validator = AmplifierPatternValidator()
        amplifier_result = await amplifier_validator.validate(
            tool_path, uses_llm=spec.uses_llm
        )

        if not amplifier_result.passed:
            logger.error("Amplifier pattern validation failed")
            return amplifier_result

        # 2.5. Dependency validation (catches import mismatches early)
        dependency_validator = DependencyValidator()
        dependency_result = await dependency_validator.validate(tool_path)

        if not dependency_result.passed:
            logger.error("Dependency validation failed")
            return dependency_result

        # 3. Static validation
        static_validator = StaticValidator()
        static_result = await static_validator.validate(tool_path)

        if not static_result.passed:
            logger.error("Static validation failed")
            return static_result

        # 4. Custom pattern validation
        pattern_validator = PatternValidator(spec.validation_rules)
        pattern_result = await pattern_validator.validate(tool_path)

        if not pattern_result.passed:
            logger.error("Pattern validation failed")
            return pattern_result

        logger.info("✓ All validations passed")
        return ValidationResult(passed=True, stage="complete", errors=[])

    def _refine_spec_with_errors(
        self: "ToolGenerationOrchestrator", spec: ToolSpec, errors: list[str]
    ) -> ToolSpec:
        """
        Refine specification with detailed, actionable error feedback.

        Args:
            spec: Current tool specification
            errors: Errors from previous iteration

        Returns:
            Updated ToolSpec with specific fix instructions
        """
        # Build detailed error feedback with specific fixes
        error_feedback = "\n\n" + "=" * 80 + "\n"
        error_feedback += "PREVIOUS ITERATION HAD ERRORS - FIX THESE SPECIFIC ISSUES:\n"
        error_feedback += "=" * 80 + "\n\n"

        for i, error in enumerate(errors, 1):
            error_feedback += f"{i}. {error}\n\n"

        # Add guidance based on error types
        error_types = self._categorize_errors(errors)

        if "missing_files" in error_types:
            error_feedback += "MISSING FILES ACTION:\n"
            error_feedback += "- Use Write tool to create each missing file\n"
            error_feedback += "- Follow blog_writer structure exactly\n"
            error_feedback += "- Check references/blog_writer/ for templates\n\n"

        if "pattern_violations" in error_types:
            error_feedback += "PATTERN VIOLATIONS ACTION:\n"
            error_feedback += "- Read references/blog_writer/main.py for CLI patterns\n"
            error_feedback += (
                "- Read references/blog_writer/core.py for ClaudeSession patterns\n"
            )
            error_feedback += "- Use Edit tool to fix each violation\n\n"

        if "validation_failures" in error_types:
            error_feedback += "VALIDATION FAILURES ACTION:\n"
            error_feedback += "- Run: cd {tool_name} && uv sync\n"
            error_feedback += "- Test: python -c 'import {tool_name}'\n"
            error_feedback += "- Fix import errors with Edit tool\n"
            error_feedback += "- Re-run validation after each fix\n\n"

        error_feedback += "=" * 80 + "\n"
        error_feedback += "CRITICAL: Review references/blog_writer/ before fixing!\n"
        error_feedback += "=" * 80 + "\n"

        refined_requirements = spec.requirements + error_feedback

        return ToolSpec(
            tool_name=spec.tool_name,
            requirements=refined_requirements,
            reference_tools=spec.reference_tools,
            validation_rules=spec.validation_rules,
            constraints=spec.constraints,
        )

    def _categorize_errors(
        self: "ToolGenerationOrchestrator", errors: list[str]
    ) -> set[str]:
        """Categorize errors to provide targeted guidance."""
        categories = set()

        for error in errors:
            error_lower = error.lower()

            if (
                "missing" in error_lower
                or "not found" in error_lower
                or "does not exist" in error_lower
            ):
                categories.add("missing_files")

            if (
                "click.argument" in error_lower
                or "path(" in error_lower
                or "describe_flag" in error_lower
                or "claudesession" in error_lower
            ):
                categories.add("pattern_violations")

            if (
                "import" in error_lower
                or "make check" in error_lower
                or "validation" in error_lower
                or "failed" in error_lower
            ):
                categories.add("validation_failures")

        return categories
