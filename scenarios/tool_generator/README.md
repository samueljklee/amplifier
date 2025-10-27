# Tool Generator: Build Amplifier Tools from Descriptions

**Describe what you want. Let AI build it. Get working code.**

## The Problem

Creating new amplifier CLI tools is harder than it should be:

- **Manual boilerplate** - Setting up project structure, dependencies, CLI interfaces
- **Validation failures** - Tools pass linting but fail at runtime with mysterious errors
- **Pattern inconsistencies** - Each tool reinvents common patterns differently
- **Debugging loops** - Fix one error, encounter another, repeat endlessly
- **Knowledge barriers** - You need to understand Click, asyncio, file I/O, error handling

## The Solution

Tool Generator is a metacognitive build system that:

1. **Understands your intent** - Converts natural language descriptions into tool specifications
2. **Delegates to Claude Code** - Leverages Claude Code SDK's built-in intelligence for generation
3. **Validates automatically** - Runs Runtime → Static → Pattern checks in correct order
4. **Fixes autonomously** - Claude Code iterates through validation failures until passing
5. **Preserves learnings** - Applies patterns from blog_writer, transcribe, and other proven tools

**The result**: A working, validated amplifier tool in minutes, not hours.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
# Interactive mode (prompts for description)
make tool-generate

# From description file
make tool-generate SPEC=my_tool_spec.txt

# Inline description
python -m scenarios.tool_generator \
  --inline "Generate a tool that analyzes markdown files for readability"
```

### Your First Tool

1. **Describe what you want**:

```text
Create a tool that analyzes Python files for complexity.

It should:
- Accept a directory path
- Find all .py files recursively
- Calculate cyclomatic complexity for each function
- Generate a summary report showing the most complex functions
- Support filtering by complexity threshold
```

2. **Run the generator**:

```bash
python -m scenarios.tool_generator my_tool_description.txt
```

3. **Watch the process**:
   - ✅ Parsing requirements
   - ✅ Generating tool structure
   - ✅ Writing implementation
   - ✅ Runtime validation (imports, CLI execution)
   - ✅ Static validation (linting, type checking)
   - ✅ Pattern validation (architecture compliance)
   - ✅ Tool ready: `scenarios/complexity_analyzer/`

4. **Use your new tool**:

```bash
python -m scenarios.complexity_analyzer --directory ./my_code
```

## What Gets Generated

Every tool includes:

```
scenarios/{tool_name}/
├── __init__.py              # Package marker
├── main.py                  # CLI entry point with @add_describe_flag
├── models.py                # Data structures (if needed)
├── core.py                  # Business logic
├── README.md                # User documentation
├── HOW_TO_CREATE_YOUR_OWN.md # Teaching guide
├── pyproject.toml           # Dependencies and metadata
└── tests/
    ├── test_core.py         # Unit tests
    └── test_integration.py  # End-to-end tests
```

**Key features automatically included:**
- Recursive file discovery (`**/*.md` not `*.md`)
- Minimum input validation (fail early)
- Progress visibility (show what's being processed)
- Defensive utilities (retry logic, error handling)
- Web UI compatibility (`@add_describe_flag` decorator)
- State management (checkpoint/resume support)
- Logging configuration (rich output formatting)

## How It Works

### The Hybrid Architecture

```
User Description
      ↓
[Specification Builder] ← LLM converts description to ToolSpec
      ↓
   task.json ──────────────────────────────┐
      ↓                                     ↓
[Python Orchestrator]            [Claude Code SDK]
      │                                     │
      │ ◄──── progress.jsonl ──────────────┤ (streaming updates)
      │                                     │
      │                          ┌──────────▼──────────┐
      │                          │ Generate Structure  │
      │                          │ Write Implementation│
      │                          │ Run Validations     │
      │                          │ Fix Errors          │
      │                          │ Iterate Until Pass  │
      │                          └──────────┬──────────┘
      │                                     │
      │ ◄──── result.json ──────────────────┤ (on completion)
      ↓
Working Tool in scenarios/{name}/
```

### Key Innovation: File-Based Delegation

Instead of manually orchestrating subprocess calls and parsing errors, tool_generator uses a **file-based communication contract** with Claude Code SDK:

**Python writes**: `task.json` (what to build + validation rules)
**Claude reads**: Task specification and context
**Claude writes**: `progress.jsonl` (streaming updates)
**Claude writes**: `result.json` (final outcome)
**Python reads**: Results and moves generated tool to final location

**Why this works:**
- **Simple** - Files are easier than parsing subprocess streams
- **Robust** - No brittle regex error parsing
- **Autonomous** - Claude Code handles all fix loops
- **Powerful** - Claude can call sub-agents (zen-architect, bug-hunter)

### The Metacognitive Recipe

Tool Generator captures the "thinking process" for creating tools:

1. **Understand intent** - Parse natural language into structured requirements
2. **Design structure** - Plan modules, interfaces, data flow
3. **Generate code** - Write implementation following proven patterns
4. **Validate runtime** - Test imports, CLI execution, basic functionality
5. **Validate statically** - Run linting, type checking, formatting
6. **Validate patterns** - Check architecture compliance (recursive glob, input validation)
7. **Fix and iterate** - Autonomously resolve failures, repeat until passing
8. **Document** - Generate README and teaching guide

This is NOT "generate code and hope" - it's a **closed-loop system** that validates and fixes until success.

## Validation: Three Tiers, Correct Order

Tool Generator validates in the **correct order** (learned from scenario_generator failures):

### Tier 1: Runtime Validation (First)

**Why first?** Catches import errors, CLI interface problems, execution failures.

```python
# Can the tool be imported?
import scenarios.{tool_name}

# Does CLI interface work?
python -m scenarios.{tool_name} --help

# Does basic execution succeed?
python -m scenarios.{tool_name} --describe-parameters
```

**Caught at this stage:**
- Missing dependencies (`uv add` fixes automatically)
- Import errors (module structure problems)
- CLI interface failures (Click decorator issues)
- Execution crashes (syntax errors, runtime exceptions)

### Tier 2: Static Validation (Second)

**Why second?** No point linting code that doesn't even import.

```bash
make check  # Runs ruff lint, ruff format, pyright
```

**Caught at this stage:**
- Code style violations
- Type errors
- Unused imports
- Formatting issues

### Tier 3: Pattern Validation (Third)

**Why third?** Checks architecture compliance after basic functionality works.

**Validation rules:**
- ✅ Uses recursive glob patterns (`**/*.md`)
- ✅ Validates minimum inputs (fails early)
- ✅ Shows progress visibility (logs what's processing)
- ✅ Uses defensive utilities (retry logic, error handling)
- ✅ Web UI compatible (`@add_describe_flag` decorator)
- ✅ Proper default values (JSON-serializable, no Path objects)
- ✅ Named options only (no `@click.argument`)

## Philosophy: Metacognitive Recipes

Tool Generator embodies "metacognitive recipes" - capturing **how to think about building tools**:

### Code Handles Structure
- File I/O and workspace management
- Validation orchestration and ordering
- Progress tracking and reporting
- Error aggregation and presentation

### AI Handles Intelligence
- Understanding natural language requirements
- Designing modular architecture
- Writing implementation code
- Diagnosing and fixing validation failures
- Iterating until all checks pass

This separation means the tool is both **reliable** (structured workflow) and **creative** (intelligent implementation).

### Trust in Emergence

Simple orchestration + powerful delegation = complex capabilities emerge naturally.

## Usage Examples

### Example 1: Content Analyzer

**Description**:
```text
Create a tool that analyzes markdown content for readability.

Features:
- Accept directory of markdown files
- Calculate Flesch Reading Ease score
- Identify complex sentences (>30 words)
- Generate summary report with recommendations
```

**Generated tool includes**:
- Recursive markdown file discovery
- Text analysis using textstat library
- Progress bars showing files being processed
- JSON and markdown output formats
- Web UI compatibility

### Example 2: Code Metrics Extractor

**Description**:
```text
Build a tool that extracts metrics from Python codebases.

Metrics:
- Lines of code per module
- Function count and average complexity
- Import dependency graph
- Test coverage gaps
```

**Generated tool includes**:
- AST parsing for Python analysis
- Graph visualization using graphviz
- Checkpoint/resume for large codebases
- Configurable thresholds via CLI flags

### Example 3: Documentation Generator

**Description**:
```text
Generate API documentation from Python docstrings.

Process:
- Scan Python modules recursively
- Extract docstrings from classes and functions
- Generate markdown documentation
- Create navigation index
```

**Generated tool includes**:
- AST-based docstring extraction
- Markdown formatting with syntax highlighting
- Automatic cross-referencing
- TOC generation

## Configuration

### Command-Line Options

```bash
# Required (one of)
--inline TEXT           # Inline tool description
--spec-file PATH        # Path to requirements file
--interactive          # Prompt for description (default)

# Optional
--output-dir PATH      # Where to create tool (default: scenarios/)
--max-iterations N     # Fix loop limit (default: 5)
--reference-tools PATH # Additional exemplar tools to reference
--constraints JSON     # Custom validation constraints
--verbose             # Detailed logging
--dry-run             # Show plan without generating
```

### Specification File Format

Simple text file describing your tool:

```text
Tool Name: sentiment_analyzer

Purpose: Analyze sentiment in text documents

Inputs:
- Directory of text files
- Optional sentiment model choice

Processing:
- Load each file
- Run sentiment analysis
- Aggregate results by category

Outputs:
- JSON summary with sentiment scores
- CSV export for spreadsheet analysis
- Visualization chart (optional)

Special Requirements:
- Support batch processing (100+ files)
- Show progress with estimated time remaining
- Handle non-English text gracefully
```

### Validation Constraints (Advanced)

Customize pattern validation rules:

```json
{
  "max_files": 15,
  "required_patterns": [
    "recursive_glob",
    "input_validation",
    "progress_visibility"
  ],
  "forbidden_patterns": [
    "click.argument",
    "path_as_default"
  ],
  "must_use_toolkit": true
}
```

## Learnings Applied

### From scenario_generator Failures

1. **Runtime validation FIRST** - Don't lint code that doesn't import
2. **Closed-loop fixing** - Iterate until passing, not one-shot attempts
3. **Automatic dependency management** - `uv add` for missing imports
4. **Pattern enforcement** - Validate architecture compliance automatically

### From amplifier-cli-architect Analysis

1. **Delegate don't duplicate** - Use Claude Code SDK, not manual subprocess orchestration
2. **File-based contracts** - Simpler than parsing streaming output
3. **Hybrid architecture** - Python orchestrates, Claude implements
4. **Sub-agent integration** - Let Claude call specialized agents

### From blog_writer Patterns

1. **Recursive file discovery** - `Path.glob("**/*.md")` not `Path.glob("*.md")`
2. **Progress visibility** - Always show what's being processed
3. **Defensive utilities** - Retry logic, error handling, LLM response parsing
4. **State management** - Checkpoint and resume support

## Troubleshooting

### "Claude Code SDK not found"

**Problem**: Claude Code SDK not installed or not accessible.

**Solution**:
```bash
# Install Claude Code SDK
pip install anthropic-code-sdk

# Or if using uv (recommended)
uv pip install anthropic-code-sdk
```

### "Validation failed after max iterations"

**Problem**: Tool keeps failing validation despite fix attempts.

**Solution**:
- Review the validation errors in the log
- Check if requirements are contradictory
- Simplify the tool description
- Increase `--max-iterations` if close to passing

### "Generated tool uses @click.argument"

**Problem**: Tool has positional arguments that break Web UI compatibility.

**Solution**: This should be caught by pattern validation. If it passed validation but still has the issue, file a bug report - the pattern validator needs improvement.

### "Import errors on generated tool"

**Problem**: Generated tool fails to import.

**Solution**: Runtime validation should catch this. If it passes validation but fails when you run it:
- Check if you're running from correct directory
- Verify virtual environment is activated
- Run `uv sync` in the tool directory

## What Makes This Different?

### vs. Manual Tool Creation

| Aspect | Manual | tool_generator |
|--------|--------|----------------|
| Time to working tool | Hours/days | Minutes |
| Pattern consistency | Varies by developer | Enforced automatically |
| Validation coverage | Manual testing | Automated 3-tier validation |
| Error fixing | Manual debugging | Autonomous iteration |
| Best practices | Must remember | Applied automatically |

### vs. scenario_generator

| Aspect | scenario_generator | tool_generator |
|--------|-------------------|----------------|
| Architecture | Manual orchestration | Claude Code delegation |
| Validation order | Static first (wrong) | Runtime first (correct) |
| Fix loops | Limited (Static phase only) | Full (all phases) |
| Error parsing | Brittle regex | Claude understands naturally |
| Dependency management | Manual | Automatic (`uv add`) |
| Complexity | ~2000+ lines | ~500 lines |

### vs. Generic Code Generators

| Aspect | Generic generators | tool_generator |
|--------|-------------------|----------------|
| Domain knowledge | None | Amplifier patterns built-in |
| Validation | None or basic | 3-tier specialized validation |
| Fix loops | None | Autonomous iteration |
| Pattern enforcement | None | Architecture rules validated |
| Learning | No | Incorporates discoveries |

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Build your own generator tools
- **[Amplifier](../../README.md)** - The framework that powers these tools
- **[Scenario Tools](../)** - More tools like this one
- **[DISCOVERIES.md](../../DISCOVERIES.md)** - Learnings that informed this design

## What's Next?

This tool demonstrates metacognitive recipes in action:

1. **Use it** - Generate your own amplifier tools from descriptions
2. **Learn from it** - See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)
3. **Extend it** - Add custom validation rules for your patterns
4. **Share back** - Contribute generated tools that others might use

---

**Built using metacognitive recipes** - The tool captures the "thinking process" for building tools, then executes that process autonomously. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for how to create your own generator tools.
