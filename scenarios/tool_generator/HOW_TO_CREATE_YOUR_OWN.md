# How to Create Your Own Generator Tool

**Generator tools are powerful. Here's how to build your own.**

This document teaches you how to create tools like tool_generator - tools that build other tools. We call these "metacognitive recipes" because they capture the *thinking process* for solving a category of problems.

## What Is a Generator Tool?

A generator tool is different from a regular scenario tool:

**Regular Scenario Tool (e.g., blog_writer)**:
- Solves a specific problem: "Turn my brain dump into a blog post"
- Takes user content as input
- Produces user-facing output (a blog post)
- Single-purpose, task-specific

**Generator Tool (e.g., tool_generator)**:
- Solves a meta-problem: "Build tools that solve problems"
- Takes problem descriptions as input
- Produces working code as output (a new tool)
- Multi-purpose, creates solutions for entire categories

Think of it this way:
- **Scenario tool** = A hammer (solves one type of problem well)
- **Generator tool** = A 3D printer for hammers (creates tools that solve problems)

## When to Build a Generator vs. Regular Scenario

### Build a Regular Scenario When:
- You have a specific, well-defined task
- The task is repeatable with different inputs
- The output is user content (documents, summaries, analysis)
- The process is straightforward: input → process → output

**Examples**:
- Blog writer: brain dump → polished post
- Transcribe: audio → text document
- Sentiment analyzer: text files → sentiment report

### Build a Generator Tool When:
- You need to create many similar tools
- Each tool follows the same architectural patterns
- You want to capture and reuse design thinking
- Manual creation is repetitive and error-prone

**Examples**:
- Tool generator: description → working amplifier tool
- Scenario generator: spec → complete scenario
- API client generator: OpenAPI spec → client library
- Test suite generator: code → comprehensive tests

## The Hybrid Architecture: Code + AI

Generator tools use a **hybrid architecture** where code and AI each handle what they do best:

### Code Handles Structure
```python
# Python code orchestrates the workflow
class ToolGenerator:
    def generate(self, description: str) -> Tool:
        # 1. Structure: Parse and validate inputs
        spec = self.parse_description(description)

        # 2. Structure: Set up workspace
        workspace = self.create_workspace(spec.name)

        # 3. Intelligence: Delegate to Claude Code
        result = self.delegate_to_claude(spec, workspace)

        # 4. Structure: Validate outputs
        self.validate_result(result)

        # 5. Structure: Move to final location
        self.install_tool(result, spec.name)

        return Tool(result.path)
```

**Code is good at**:
- File I/O and workspace management
- Validation orchestration and ordering
- Progress tracking and error aggregation
- Deterministic workflows and state machines

### AI Handles Intelligence
```python
# Claude Code SDK handles creative/intelligent work
task = {
    "description": spec.requirements,
    "validation_rules": spec.rules,
    "reference_tools": ["blog_writer", "transcribe"],
    "workspace": workspace.path
}

# Claude Code autonomously:
# - Designs architecture
# - Writes implementation
# - Runs validations
# - Fixes errors
# - Iterates until passing

result = claude_session.run_task(task)
```

**AI is good at**:
- Understanding natural language requirements
- Making architectural design decisions
- Writing code that follows patterns
- Diagnosing and fixing errors
- Iterating based on feedback

### Why This Works

**Separation of concerns**:
- Code provides reliable structure (always runs the same way)
- AI provides intelligent solutions (adapts to each unique case)
- Neither tries to do what the other does better

**Result**: Tools that are both reliable (structured workflow) and creative (intelligent solutions).

## The Metacognitive Recipe Pattern

A metacognitive recipe captures the **thinking process** for solving problems, not just the solution itself.

### Example: Tool Generator's Recipe

**The thinking process for creating tools:**

1. **Understand the intent**
   - What problem are we solving?
   - What should the inputs and outputs be?
   - What patterns should this follow?

2. **Design the structure**
   - How should the code be organized?
   - What modules are needed?
   - How do pieces connect?

3. **Implement the solution**
   - Write the code following proven patterns
   - Use existing libraries appropriately
   - Handle errors defensively

4. **Validate the implementation**
   - Does it import and run? (Runtime)
   - Does it pass static checks? (Linting, types)
   - Does it follow architectural patterns? (Standards)

5. **Fix and iterate**
   - Diagnose failures
   - Apply fixes
   - Revalidate
   - Repeat until passing

6. **Document the result**
   - Explain what it does
   - Provide usage examples
   - Teach others how to extend it

This recipe works for *any* tool. That's why tool_generator can create diverse tools from just descriptions.

### Contrast: Recipe vs. Template

**Template approach** (limited):
```python
# Fill in the blanks, rigid structure
def generate_from_template(name: str, input_type: str):
    return f"""
    def {name}(input: {input_type}):
        # TODO: Implement {name}
        pass
    """
```

**Recipe approach** (flexible):
```python
# Describe the thinking, AI adapts
def generate_from_recipe(description: str):
    recipe = """
    Understand what this tool needs to do.
    Design an appropriate architecture.
    Implement following proven patterns.
    Validate and fix until working.
    """
    return claude_code.execute(description, recipe)
```

The recipe approach is **dramatically more powerful** because it captures *process* not just *structure*.

## File-Based Contracts: The Key Innovation

Tool_generator's architecture centers on **file-based communication** with Claude Code SDK. This is the simple, correct approach.

### The Pattern

```
Python Orchestrator                Claude Code SDK
──────────────────                ───────────────

1. Write task.json      ────────▶  2. Read task spec
                                       ↓
                                   3. Generate tool
                                       ↓
                                   4. Validate & fix
                                       ↓
5. Wait & monitor       ◀────────  6. Write progress.jsonl (streaming)
                                       ↓
7. Read result.json     ◀────────  8. Write result.json (complete)
                                       ↓
9. Install tool                    9. Workspace ready
```

### Why Files Beat Streaming

**Alternative (complex)**: Parse subprocess stdout/stderr
```python
# Fragile, breaks with output format changes
process = subprocess.Popen([...], stdout=PIPE, stderr=PIPE)
for line in process.stdout:
    if "ERROR:" in line:
        error = parse_error(line)  # Regex nightmare
```

**File-based (simple)**: Structured contracts
```python
# Robust, structured data
write_json("task.json", task_spec)
claude_code_sdk.run()
result = read_json("result.json")  # Clean, typed data
```

**Benefits**:
- **Simple** - JSON files are easy to read/write
- **Robust** - No parsing of unstructured text
- **Debuggable** - Inspect files at any point
- **Recoverable** - Resume from intermediate state
- **Type-safe** - Structured data with validation

### The Task Contract

```json
{
  "requirements": "Natural language description of what to build",
  "validation_rules": [
    {
      "name": "recursive_glob",
      "check": "uses_recursive_glob_patterns",
      "required": true,
      "reason": "Prevent shallow file discovery bugs"
    }
  ],
  "reference_tools": [
    "/path/to/blog_writer",
    "/path/to/transcribe"
  ],
  "constraints": {
    "max_files": 10,
    "must_use_toolkit": true
  },
  "working_dir": "/tmp/tool_workspace_XYZ"
}
```

**Key insight**: This is a *declarative specification*, not imperative commands. We describe *what* we want, not *how* to build it.

### The Result Contract

```json
{
  "success": true,
  "tool_name": "content_analyzer",
  "files_created": [
    "main.py",
    "models.py",
    "core.py",
    "pyproject.toml"
  ],
  "validation_passed": true,
  "validation_details": {
    "runtime": {"status": "pass", "duration_ms": 450},
    "static": {"status": "pass", "duration_ms": 1200},
    "pattern": {"status": "pass", "duration_ms": 150}
  },
  "errors": [],
  "iterations": 2
}
```

**Key insight**: Rich structured data, not "exit code 0 or 1". We get *details* about what happened.

### Progress Streaming

```jsonl
{"timestamp": "2025-01-24T10:00:00", "stage": "parsing", "status": "complete"}
{"timestamp": "2025-01-24T10:00:05", "stage": "generating", "status": "in_progress", "files_count": 0}
{"timestamp": "2025-01-24T10:00:12", "stage": "generating", "status": "in_progress", "files_count": 3}
{"timestamp": "2025-01-24T10:00:20", "stage": "validating", "status": "in_progress", "phase": "runtime"}
{"timestamp": "2025-01-24T10:00:25", "stage": "validating", "status": "in_progress", "phase": "static"}
{"timestamp": "2025-01-24T10:00:30", "stage": "complete", "status": "success"}
```

**JSONL = JSON Lines**: One JSON object per line, perfect for streaming updates.

## Architecture Patterns

### Pattern 1: Workspace Isolation

Each generation gets its own temporary workspace:

```python
class WorkspaceManager:
    def create_workspace(self, tool_name: str) -> Path:
        """Create isolated workspace for generation"""
        workspace = Path(tempfile.mkdtemp(prefix=f"tool_{tool_name}_"))

        # Set up structure
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()

        # Copy reference tools for context
        self._copy_references(workspace)

        return workspace

    def cleanup(self, workspace: Path):
        """Clean up after generation (success or failure)"""
        shutil.rmtree(workspace)
```

**Why isolation matters**:
- No interference between concurrent generations
- Clean slate for each attempt
- Easy cleanup on failure
- Parallel generation possible

### Pattern 2: Validation Ordering

Validation must run in **correct order** (Runtime → Static → Pattern):

```python
class ValidationOrchestrator:
    def validate(self, tool_path: Path) -> ValidationResult:
        """Run validations in dependency order"""

        # Phase 1: Runtime (most critical)
        runtime = self.runtime_validator.validate(tool_path)
        if not runtime.passed:
            return ValidationResult(phase="runtime", errors=runtime.errors)

        # Phase 2: Static (depends on Runtime passing)
        static = self.static_validator.validate(tool_path)
        if not static.passed:
            return ValidationResult(phase="static", errors=static.errors)

        # Phase 3: Pattern (depends on basic functionality)
        pattern = self.pattern_validator.validate(tool_path)
        return ValidationResult(
            phase="pattern",
            passed=pattern.passed,
            errors=pattern.errors
        )
```

**Why order matters**:
- Runtime catches import/execution errors (no point linting broken code)
- Static catches style/type errors (requires working imports)
- Pattern validates architecture (requires passing basic checks)

### Pattern 3: Autonomous Fix Loops

Claude Code iterates until validation passes:

```python
class GenerationOrchestrator:
    def generate_with_validation(
        self,
        spec: ToolSpec,
        max_iterations: int = 5
    ) -> GenerationResult:
        """Generate tool with autonomous fix loops"""

        for iteration in range(max_iterations):
            # Generate or fix
            if iteration == 0:
                self.delegate_generation(spec)
            else:
                self.delegate_fixes(spec, previous_errors)

            # Validate
            validation = self.validate(spec.workspace)

            if validation.passed:
                return GenerationResult(
                    success=True,
                    iterations=iteration + 1,
                    validation=validation
                )

            previous_errors = validation.errors

        # Failed after max iterations
        return GenerationResult(
            success=False,
            iterations=max_iterations,
            final_errors=previous_errors
        )
```

**Why autonomy matters**:
- No human in the loop for mechanical fixes
- Claude Code understands error messages naturally
- Faster iteration (seconds not minutes)
- Learns patterns across iterations

## Creating Your Own Generator

### Step 1: Identify the Pattern

What category of problems do you solve repeatedly?

**Questions to ask**:
- Do I create similar tools/components often?
- Do these follow common architectural patterns?
- Would automating this save significant time?
- Can I describe the creation process clearly?

**Example patterns worth capturing**:
- API client generators (OpenAPI spec → client code)
- Test suite generators (code → comprehensive tests)
- Documentation generators (code → user docs)
- Migration generators (schema changes → migration code)

### Step 2: Extract the Recipe

What's the **thinking process** for creating these tools?

**Write it down in plain language**:
```text
Recipe for API Client Generator:

1. Parse the OpenAPI specification
2. Identify all endpoints and their parameters
3. Design client class structure with methods
4. Generate typed request/response models
5. Implement error handling for each endpoint
6. Add retry logic for transient failures
7. Create authentication handling
8. Generate usage documentation
9. Write integration tests
10. Validate against the spec
```

This is your **metacognitive recipe** - the process, not the code.

### Step 3: Design the Hybrid Architecture

Decide what code does vs. what AI does:

**Code responsibilities** (orchestrator):
```python
class YourGenerator:
    def generate(self, input_spec: InputSpec) -> Output:
        # 1. Parse and validate input
        parsed = self.parse_input(input_spec)

        # 2. Set up workspace
        workspace = self.workspace_manager.create(parsed.name)

        # 3. Delegate to AI
        task = self.build_task_spec(parsed, workspace)
        result = self.claude_session.run_task(task)

        # 4. Validate result
        validation = self.validator.validate(result)

        # 5. Finalize
        if validation.passed:
            self.install(result)

        return Output(result, validation)
```

**AI responsibilities** (delegated via Claude Code SDK):
- Understanding the input specification
- Making design decisions
- Writing implementation code
- Running validations
- Fixing errors autonomously
- Documenting the result

### Step 4: Implement File-Based Contracts

Design your `task.json` and `result.json` formats:

```python
# Task specification for AI
@dataclass
class TaskSpec:
    description: str              # Natural language requirements
    validation_rules: list[Rule]  # What to check
    reference_examples: list[Path] # Exemplar patterns
    constraints: dict[str, Any]   # Custom constraints
    workspace: Path               # Where to work

# Result from AI
@dataclass
class GenerationResult:
    success: bool
    artifacts: list[Path]         # What was created
    validation: ValidationResult  # How it passed
    errors: list[str]             # What failed (if any)
    iterations: int               # How many fix loops
```

### Step 5: Build Validators

Create validators for your domain:

```python
class RuntimeValidator:
    """Can the generated artifact run?"""
    def validate(self, artifact: Path) -> ValidationResult:
        try:
            # Import check
            importlib.import_module(artifact.stem)

            # Execution check
            subprocess.run([...], check=True)

            return ValidationResult(passed=True)
        except Exception as e:
            return ValidationResult(passed=False, error=str(e))

class PatternValidator:
    """Does it follow our architectural patterns?"""
    def validate(self, artifact: Path) -> ValidationResult:
        code = artifact.read_text()

        checks = [
            self.check_recursive_glob(code),
            self.check_input_validation(code),
            self.check_error_handling(code),
        ]

        return ValidationResult(
            passed=all(c.passed for c in checks),
            details=checks
        )
```

### Step 6: Test With Real Examples

Start with simple cases:

```python
# Test 1: Simplest possible generation
def test_minimal_generation():
    generator = YourGenerator()
    result = generator.generate(InputSpec(
        description="Create a minimal working example"
    ))
    assert result.success
    assert result.validation.passed

# Test 2: Real-world complexity
def test_realistic_generation():
    generator = YourGenerator()
    result = generator.generate(InputSpec(
        description=load_realistic_spec()
    ))
    assert result.success
    assert len(result.artifacts) > 3

# Test 3: Error recovery
def test_fix_loops():
    generator = YourGenerator()
    # Intentionally vague/problematic spec
    result = generator.generate(InputSpec(
        description="Make it work but requirements unclear"
    ))
    # Should succeed after multiple iterations
    assert result.success
    assert result.iterations > 1
```

### Step 7: Document the Recipe

Create HOW_TO_CREATE_YOUR_OWN.md (like this file!) explaining:
- What your generator does
- When to use it vs. alternatives
- The hybrid architecture you chose
- The file-based contracts you designed
- How others can extend/adapt it

## Real-World Example: tool_generator Itself

Let's examine tool_generator's architecture as a concrete example:

### The Recipe (Metacognitive Process)

```
1. Understand intent
   → Parse user description into structured requirements

2. Design structure
   → Choose module organization, identify needed components

3. Generate implementation
   → Write Python code following amplifier patterns

4. Validate runtime
   → Test imports, CLI execution, basic functionality

5. Validate statically
   → Run linting, type checking, formatting

6. Validate patterns
   → Check recursive glob, input validation, web UI compatibility

7. Fix and iterate
   → Autonomously resolve failures, repeat validation

8. Document result
   → Generate README and teaching guide
```

### The Hybrid Split

**Python orchestrator** (structural):
```python
class ToolGenerationOrchestrator:
    def generate_tool(self, description: str) -> Tool:
        # Structure: Parse input
        spec = self.spec_builder.build(description)

        # Structure: Set up workspace
        workspace = self.workspace_mgr.create(spec.name)

        # Intelligence: Delegate to Claude Code
        task = TaskSpec(
            requirements=spec.requirements,
            validation_rules=AMPLIFIER_PATTERNS,
            reference_tools=[blog_writer, transcribe],
            workspace=workspace.path
        )
        self.task_writer.write(task, workspace / "task.json")

        # Structure: Monitor progress
        for update in self.progress_reader.stream(workspace):
            self.display_progress(update)

        # Structure: Read result
        result = self.result_reader.read(workspace / "result.json")

        # Structure: Validate and install
        if result.success:
            self.install_tool(workspace, f"scenarios/{spec.name}")

        return Tool(spec.name, result)
```

**Claude Code SDK** (intelligent):
- Reads `task.json` specification
- Understands requirements in natural language
- Designs modular architecture
- Writes implementation code
- Runs `uv sync`, `make check`, tests
- Diagnoses failures (import errors, type errors, pattern violations)
- Applies fixes autonomously
- Iterates until all validations pass
- Writes `result.json` with details
- Can call sub-agents (zen-architect, bug-hunter, modular-builder)

### The File Contracts

**task.json** (orchestrator → Claude Code):
```json
{
  "requirements": "Create a tool that analyzes Python complexity...",
  "validation_rules": [
    {"name": "recursive_glob", "required": true},
    {"name": "input_validation", "required": true},
    {"name": "web_ui_compat", "required": true}
  ],
  "reference_tools": [
    "/path/to/blog_writer",
    "/path/to/transcribe"
  ],
  "constraints": {
    "max_files": 10,
    "must_use_toolkit": true
  },
  "working_dir": "/tmp/tool_complexity_analyzer_XYZ"
}
```

**result.json** (Claude Code → orchestrator):
```json
{
  "success": true,
  "tool_name": "complexity_analyzer",
  "files_created": [
    "main.py",
    "core.py",
    "models.py",
    "pyproject.toml",
    "README.md"
  ],
  "validation_passed": true,
  "validation_details": {
    "runtime": {"status": "pass", "duration_ms": 420},
    "static": {"status": "pass", "duration_ms": 1150},
    "pattern": {"status": "pass", "duration_ms": 180}
  },
  "errors": [],
  "iterations": 2,
  "learnings": [
    "Initially used Path as default value, fixed to string",
    "Added missing recursive glob in file discovery"
  ]
}
```

### Validation Pipeline

```python
# Phase 1: Runtime Validation
class RuntimeValidator:
    def validate(self, tool_path: Path) -> ValidationResult:
        # Can we import it?
        try:
            import scenarios.complexity_analyzer
        except ImportError as e:
            return ValidationResult(False, f"Import failed: {e}")

        # Does CLI work?
        result = subprocess.run(
            ["python", "-m", "scenarios.complexity_analyzer", "--help"],
            capture_output=True
        )
        if result.returncode != 0:
            return ValidationResult(False, f"CLI failed: {result.stderr}")

        # Does describe-parameters work?
        result = subprocess.run(
            ["python", "-m", "scenarios.complexity_analyzer", "--describe-parameters"],
            capture_output=True
        )
        if result.returncode != 0:
            return ValidationResult(False, "Web UI compatibility failed")

        return ValidationResult(True)

# Phase 2: Static Validation
class StaticValidator:
    def validate(self, tool_path: Path) -> ValidationResult:
        # Run make check
        result = subprocess.run(
            ["make", "check"],
            cwd=tool_path,
            capture_output=True
        )

        if result.returncode != 0:
            errors = self.parse_check_output(result.stderr)
            return ValidationResult(False, errors)

        return ValidationResult(True)

# Phase 3: Pattern Validation
class PatternValidator:
    def validate(self, tool_path: Path) -> ValidationResult:
        code = (tool_path / "main.py").read_text()

        issues = []

        # Check recursive glob
        if ".glob(\"*.md\")" in code:
            issues.append("Uses non-recursive glob - should be **/*.md")

        # Check input validation
        if "if len(files) <" not in code:
            issues.append("Missing minimum input validation")

        # Check Web UI compatibility
        if "@click.argument" in code:
            issues.append("Uses @click.argument - Web UI requires @click.option only")

        if "default=Path(" in code:
            issues.append("Uses Path as default - Web UI requires JSON-serializable defaults")

        return ValidationResult(
            passed=len(issues) == 0,
            errors=issues
        )
```

### Key Learnings Applied

1. **Runtime validation first** - Catches import/execution errors before linting
2. **File-based contracts** - Simpler than subprocess output parsing
3. **Autonomous fix loops** - Claude Code iterates until passing
4. **Pattern enforcement** - Validates architectural standards automatically
5. **Reference tools** - Provides exemplar code for learning patterns

## Philosophy Alignment

Generator tools embody the core amplifier philosophies:

### Ruthless Simplicity

**Simple orchestration** (file-based contracts beat streaming output):
```python
# This is simple - write file, read file
write_json("task.json", task)
result = read_json("result.json")
```

**vs. Complex orchestration** (parsing subprocess streams):
```python
# This is complex - regex parsing, state tracking
for line in process.stdout:
    if match := re.match(r"ERROR: (.+)", line):
        handle_error(match.group(1))
```

### Modular Design (Bricks and Studs)

Each component is a clear "brick" with defined interfaces:

```
Orchestrator Brick
├── Contract: TaskSpec → GenerationResult
├── Internal: Workflow state machine
└── Dependencies: WorkspaceManager, TaskWriter, ResultReader

Workspace Manager Brick
├── Contract: create(name) → Path, cleanup(path) → void
├── Internal: Tempdir management
└── Dependencies: None (stdlib only)

Task Writer Brick
├── Contract: write(spec, path) → void
├── Internal: JSON serialization
└── Dependencies: Models (dataclasses)
```

**Each brick can be regenerated independently** as long as contracts stay stable.

### Trust in Emergence

Simple pieces → complex capabilities:

- **Simple**: File-based contracts (task.json, result.json)
- **Simple**: Three validators (Runtime, Static, Pattern)
- **Simple**: Orchestrate: write task → wait → read result

**Emergent complexity**:
- Claude Code calls sub-agents (zen-architect designs, modular-builder implements)
- Autonomous fix loops (validates, diagnoses, fixes, repeats)
- Pattern learning (incorporates DISCOVERIES.md lessons)
- Parallel generation (multiple workspaces simultaneously)

We didn't program these capabilities - they **emerged** from simple, well-designed components.

## Common Pitfalls

### Pitfall 1: Doing Too Much in Code

**Wrong**: Try to implement AI logic in Python
```python
# Bad: Trying to generate code with string templates
def generate_function(name: str, params: list[str]) -> str:
    param_str = ", ".join(params)
    return f"""
    def {name}({param_str}):
        # TODO: Implement
        pass
    """
```

**Right**: Delegate intelligence to AI
```python
# Good: Describe what you want, let AI generate
task = TaskSpec(
    description=f"Create a function named {name} with parameters {params}",
    constraints={"style": "pythonic", "include_docs": True}
)
result = claude_session.run_task(task)
```

### Pitfall 2: Complex Communication Protocols

**Wrong**: Parse subprocess output with regex
```python
# Bad: Fragile parsing
process = subprocess.Popen([...], stdout=PIPE)
for line in process.stdout:
    if "Generating file:" in line:
        file_name = re.search(r"Generating file: (.+)", line).group(1)
```

**Right**: Use structured file contracts
```python
# Good: Read structured data
progress = read_jsonl("progress.jsonl")
for event in progress:
    if event["stage"] == "generating":
        file_name = event["file_name"]
```

### Pitfall 3: Wrong Validation Order

**Wrong**: Static checks before runtime
```python
# Bad: Lint code that might not even import
run_linter()  # Fails with import errors
run_runtime_tests()  # Never reached
```

**Right**: Runtime → Static → Pattern
```python
# Good: Catch big issues first
if not runtime_validator.validate():
    return  # No point linting broken code

if not static_validator.validate():
    return  # No point checking patterns yet

pattern_validator.validate()
```

### Pitfall 4: One-Shot Generation

**Wrong**: Generate once, hope it works
```python
# Bad: No iteration
result = generate_tool(spec)
if not result.success:
    print("Failed!")  # User has to fix manually
```

**Right**: Autonomous fix loops
```python
# Good: Iterate until passing
for i in range(max_iterations):
    result = generate_tool(spec)
    if result.success:
        break

    # AI fixes based on validation errors
    spec.add_context(result.errors)
```

### Pitfall 5: No Pattern Enforcement

**Wrong**: Generate code without standards
```python
# Bad: No validation rules
result = claude_session.generate(description)
# Hope it follows patterns...
```

**Right**: Explicit pattern validation
```python
# Good: Validate patterns automatically
validation_rules = [
    Rule("recursive_glob", required=True),
    Rule("input_validation", required=True),
    Rule("web_ui_compat", required=True),
]

result = claude_session.generate(
    description,
    validation_rules=validation_rules
)
```

## Next Steps

### If You're New to Generators

1. **Use tool_generator** - Generate a simple tool to see it in action
2. **Study the code** - Read the implementation to understand patterns
3. **Identify a need** - What category of tools do you create repeatedly?
4. **Start simple** - Build a minimal generator for one use case first

### If You're Ready to Build

1. **Extract your recipe** - Write down the thinking process
2. **Design contracts** - Define task.json and result.json formats
3. **Build orchestrator** - Write the Python structural code
4. **Create validators** - Implement domain-specific validation
5. **Test iteratively** - Start simple, add complexity gradually
6. **Document thoroughly** - Help others learn from your work

### Resources

- **[tool_generator implementation](.)** - Study the actual code
- **[Claude Code SDK docs](../../ai_context/claude_code/)** - Learn the delegation API
- **[DISCOVERIES.md](../../DISCOVERIES.md)** - Learnings that informed this design
- **[IMPLEMENTATION_PHILOSOPHY.md](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md)** - Core design principles

## Remember

**Generator tools are not about writing more code.** They're about:
- Capturing thinking processes (metacognitive recipes)
- Leveraging AI for intelligence (Claude Code delegation)
- Using code for structure (orchestration, validation)
- Enforcing patterns automatically (architectural standards)
- Enabling rapid iteration (autonomous fix loops)

The result: **Create tools faster, with better quality, following proven patterns.**

---

**You've now learned the pattern.** Go build generators for the tools **you** wish you had.
