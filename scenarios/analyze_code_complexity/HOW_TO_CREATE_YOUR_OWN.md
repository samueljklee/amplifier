# How to Create Your Own Code Analysis Tool

This guide explains the architecture of `analyze_code_complexity` and how to adapt it for your own code analysis needs.

## Why This Tool Exists

Code complexity analysis is essential for maintaining healthy codebases. This tool:
- Provides objective metrics for code quality discussions
- Identifies technical debt and refactoring opportunities
- Helps teams prioritize improvements
- Integrates seamlessly with development workflows

## Architecture Overview

### Modular "Bricks and Studs" Design

The tool uses a modular architecture with 4 functional modules:

```
analyze_code_complexity/
├── main.py              # Orchestrator (coordinates modules)
├── scanner/            # Discovers code files
├── metrics_analyzer/   # Calculates complexity metrics
├── quality_analyzer/   # Identifies quality issues
└── report_generator/   # Creates markdown reports
```

Each module is a self-contained "brick" with a clear interface ("studs").

### Module Responsibilities

**scanner/**
- Discovers code files recursively using `glob("**/*.ext")`
- Identifies programming language by extension
- Filters out large/unreadable files
- Returns structured file metadata

**metrics_analyzer/**
- Uses LLM to calculate complexity metrics
- Analyzes cyclomatic complexity, LOC, nesting depth
- Evaluates maintainability index
- Parses responses with defensive type guards

**quality_analyzer/**
- Uses LLM to identify code smells
- Detects security vulnerabilities
- Finds duplication and best practice violations
- Returns structured issue reports

**report_generator/**
- Aggregates results from all analyzers
- Generates comprehensive markdown report
- Provides executive summary and detailed findings
- Creates actionable recommendations

## Key Patterns to Follow

### 1. Recursive File Discovery
```python
# Use glob with ** for recursive search
for file_path in directory.glob(f"**/*{ext}"):
    if file_path.is_file():
        # Process file
```

### 2. Progress Logging
```python
# Show progress for long operations
logger.info(f"Analyzing: {i + 1}-{min(i + batch_size, len(files))} of {len(files)}")
```

### 3. Defensive LLM Parsing
```python
result = parse_llm_json(response.content)

# REQUIRED: Type guard before using as dict
if not isinstance(result, dict):
    logger.error("Expected dict from LLM, got invalid format")
    return None

# Now safe to use dict operations
value = result.get("key", "default")
```

### 4. Session Data Management
```python
# Store runtime data in .data/
base_dir = Path.cwd() / ".data" / "tool_name" / "sessions"
session_dir = base_dir / f"{timestamp}_{guid}"
session_dir.mkdir(parents=True, exist_ok=True)

# Save intermediate results
results_dir = session_dir / "results"
(results_dir / "metrics.json").write_text(json.dumps(data))
```

### 5. Output Path Handling
```python
# Handle Web UI output paths (create parent directories!)
if output_path is None:
    output_path = session_dir / "output.md"
else:
    output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(content)
```

### 6. Batch Processing with Progress
```python
batch_size = 5
for i in range(0, len(items), batch_size):
    batch = items[i:i + batch_size]
    logger.info(f"Processing: {i + 1}-{min(i + batch_size, len(items))}")
    # Process batch
```

## Adapting for Your Use Case

### Create a Security-Focused Analyzer

Replace `quality_analyzer` with a specialized security module:

```python
class SecurityAnalyzer:
    """Specialized security vulnerability scanner."""

    def __init__(self):
        self.system_prompt = """You are a security expert. Focus on:
        - SQL injection vulnerabilities
        - XSS attack vectors
        - Authentication/authorization issues
        - Cryptographic weaknesses
        - Dependency vulnerabilities
        """

    async def analyze_security(self, files):
        # Focus solely on security issues
        pass
```

### Create a Performance Analyzer

Add a new module for performance analysis:

```python
class PerformanceAnalyzer:
    """Analyzes code for performance issues."""

    async def analyze_performance(self, files):
        # Check for:
        # - Inefficient algorithms (O(n²) loops)
        # - Memory leaks
        # - Database query optimization
        # - Caching opportunities
        pass
```

### Create a Documentation Analyzer

Analyze documentation quality:

```python
class DocAnalyzer:
    """Analyzes code documentation quality."""

    async def analyze_docs(self, files):
        # Check for:
        # - Missing docstrings
        # - Outdated comments
        # - API documentation completeness
        # - Example code quality
        pass
```

## CLI Integration Best Practices

### Use @click.option (Never @click.argument)
```python
@click.option("--directory", type=click.Path(exists=True), required=True)
@click.option("--output", type=click.Path(), default=None)
def main(directory, output):
    # Web UI can introspect options but not arguments
    pass
```

### Add @add_describe_flag
```python
@add_describe_flag(version="1.0", display_name="Your Tool Name")
@click.command()
def main():
    # Enables Web UI integration
    pass
```

### String Defaults Only
```python
# ✅ CORRECT
@click.option("--output", default="output.json")

# ❌ WRONG - breaks Web UI introspection
@click.option("--output", default=Path("output.json"))
```

## Validation Checklist

Before considering your tool complete, ensure:

1. **Imports work** - `python -c "import your_tool"`
2. **CLI works** - `python -m your_tool --help`
3. **Formatting** - `uv run ruff format --check .`
4. **Linting** - `uv run ruff check .`
5. **Types** - `uv run pyright .`
6. **File discovery** - Uses `glob("**/*.ext")`
7. **Progress logging** - Shows progress for long operations
8. **Input validation** - Checks for minimum required inputs
9. **Defensive parsing** - Type guards after `parse_llm_json()`
10. **Output directories** - Creates parent directories for outputs

## Common Pitfalls

### ❌ Don't: Use root core.py
```
analyze_code_complexity/
└── core.py  # Wrong! Logic should be in modules
```

### ✅ Do: Use functional modules
```
analyze_code_complexity/
├── main.py         # Orchestrator only
└── analyzer/       # Logic here
    └── core.py
```

### ❌ Don't: Skip type guards
```python
result = parse_llm_json(response)
value = result.get("key")  # TypeError if result is list/None!
```

### ✅ Do: Add type guards
```python
result = parse_llm_json(response)
if not isinstance(result, dict):
    return None
value = result.get("key")  # Safe!
```

### ❌ Don't: Forget parent directories
```python
Path(output_path).write_text(content)  # Fails if parent doesn't exist!
```

### ✅ Do: Create parent directories
```python
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(content)
```

## Testing Your Tool

### Manual Testing
```bash
# Test with a small project first
python -m scenarios.analyze_code_complexity \
    --directory ./test_project \
    --verbose
```

### Check Output
```bash
# Verify session data
ls -la .data/analyze_code_complexity/sessions/latest/

# View report
cat .data/analyze_code_complexity/sessions/latest/complexity_report.md
```

### Integration Testing
```bash
# Test with Web UI
export AMPLIFIER_WEB_UI=1
python -m scenarios.analyze_code_complexity --directory ./src
```

## Further Reading

- **blog_writer** - Example of multi-stage stateful tool with user interaction
- **transcribe** - Example of complex pipeline with 9 modules
- **web_to_md** - Example of simple 2-module tool

## Questions?

Study the existing tools in `scenarios/` for inspiration. They all follow the same modular "bricks and studs" pattern demonstrated here.
