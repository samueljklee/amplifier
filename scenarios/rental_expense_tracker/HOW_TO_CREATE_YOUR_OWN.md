# How to Create Your Own Expense Tracker Tool

This document explains the architecture and design patterns used in the Rental Expense Tracker, so you can adapt it for your own use cases.

## Why This Tool Exists

Short-term rental property managers deal with numerous receipts and invoices from various vendors (cleaners, maintenance workers, utility companies, platforms like Airbnb/VRBO). Manually categorizing and summarizing these expenses is time-consuming and error-prone.

This tool automates:
1. Text extraction from PDF receipts
2. Intelligent parsing of expense and time data
3. Categorization into meaningful buckets
4. Report generation with summaries and details

## Architecture Overview

The tool follows a modular "bricks and studs" architecture with 5 functional modules:

```
rental_expense_tracker/
├── main.py                    # Orchestrator - coordinates modules
├── pdf_extractor/            # Extract text from PDFs
│   ├── __init__.py
│   └── core.py
├── expense_parser/           # Parse expense data using LLM
│   ├── __init__.py
│   └── core.py
├── time_parser/              # Parse time entries using LLM
│   ├── __init__.py
│   └── core.py
├── categorizer/              # Categorize expenses using LLM
│   ├── __init__.py
│   └── core.py
└── report_generator/         # Generate markdown/PDF reports
    ├── __init__.py
    └── core.py
```

### Why This Structure?

- **Modular**: Each module is a "brick" - regeneratable independently
- **Testable**: Can test each module in isolation
- **Reusable**: `pdf_extractor` could be used in other PDF processing tools
- **Scalable**: Easy to add new modules (e.g., `receipt_validator`, `tax_calculator`)

## Key Patterns

### 1. Module Structure

Each module follows this pattern:

**`__init__.py`** - Exports the module interface:
```python
from .core import ExpenseParser
__all__ = ["ExpenseParser"]
```

**`core.py`** - Implements the logic:
```python
class ExpenseParser:
    async def parse_expenses(self, text: str, source_name: str) -> list[dict]:
        # Implementation here
        pass
```

### 2. CLI Orchestration (`main.py`)

The main file:
- Uses `@click.command()` for CLI interface
- Uses `@add_describe_flag` for Web UI introspection
- Coordinates modules in the pipeline
- Handles session management and logging

Critical patterns:
```python
@add_describe_flag(version="1.0", display_name="Tool Name")
@click.command()
@click.option("--input", required=True, help="...")  # Always use @click.option
def main(input: str, ...):  # String parameters for introspection
    # Create session directory in .data/
    session_dir = Path.cwd() / ".data" / "tool_name" / "sessions" / f"{timestamp}_{guid}"

    # Coordinate modules
    pipeline = Pipeline(session_dir)
    success = asyncio.run(pipeline.run(...))
```

### 3. LLM Integration with Defensive Parsing

All LLM interactions use the defensive pattern:

```python
from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json

async def parse_data(self, text: str) -> list[dict]:
    system_prompt = "You are an assistant that..."
    prompt = f"Extract data from: {text}"

    options = SessionOptions(system_prompt=system_prompt)
    async with ClaudeSession(options) as claude:
        response = await claude.query(prompt)
        parsed = parse_llm_json(response.content)

        # CRITICAL: Type guard after parsing
        if not isinstance(parsed, list):
            logger.error(f"Expected list, got {type(parsed).__name__}")
            return []

        # Process results safely
        return [item for item in parsed if isinstance(item, dict)]
```

### 4. Progress Logging

Use structured logging for visibility:

```python
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat

logger = ToolkitLogger(name="tool_name", format=LogFormat.JSON)

# Stage transitions for workflow tracking
logger.stage_transition(None, "extract_pdfs", estimated_duration=30)
logger.info("📄 Extracting PDFs...")

# File creation events
logger.file_created(str(output_path), metadata={"type": "report"})

# Preview events for Web UI
logger.preview_available(preview_type="markdown", preview_data=str(path))
```

### 5. Session Management

Store runtime data in `.data/tool_name/sessions/`:

```python
# Create unique session directory
base_dir = Path.cwd() / ".data" / "tool_name" / "sessions"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
guid = uuid.uuid4().hex[:8]
session_dir = base_dir / f"{timestamp}_{guid}"
session_dir.mkdir(parents=True, exist_ok=True)

# Create 'latest' symlink for easy access
latest_link = base_dir / "latest"
if latest_link.exists():
    latest_link.unlink()
latest_link.symlink_to(session_dir.name)

# Save intermediate results
results_file = session_dir / "results.json"
results_file.write_text(json.dumps(data, indent=2))
```

### 6. Web UI Output Path Handling

When receiving output paths from Web UI:

```python
if output_path is None:
    # Default to session directory
    output_path = session_dir / "output.md"
else:
    output_path = Path(output_path)
    # CRITICAL: Create parent directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

# Now safe to write
output_path.write_text(content)
```

## Adapting for Your Use Case

### To Create a Similar Document Processing Tool:

1. **Identify functional modules** (3-7 modules typically):
   - Input processing (e.g., `pdf_reader`, `image_ocr`)
   - Data extraction (e.g., `field_extractor`, `table_parser`)
   - Processing (e.g., `validator`, `enricher`)
   - Output generation (e.g., `formatter`, `exporter`)

2. **Create module structure**:
   ```bash
   mkdir -p tool_name/{module1,module2,module3}
   # Each module gets __init__.py and core.py
   ```

3. **Implement CLI in `main.py`**:
   - Use `@click.option` for all parameters (never `@click.argument`)
   - Use string defaults (never `Path()` or other objects)
   - Add `@add_describe_flag` decorator
   - Create session directory in `.data/`

4. **Add dependencies to `pyproject.toml`**:
   ```toml
   [project]
   dependencies = [
       "amplifier",
       "click>=8.0",
       # Add your specific libraries
   ]

   [tool.uv.sources]
   amplifier = { path = "../../", editable = true }
   ```

5. **Add workflow metadata** for Web UI visualization:
   ```toml
   [tool.amplifier.workflow]
   stages = [
       { id = "input", type = "input", label = "Input Data", ... },
       { id = "process", type = "process", label = "Process", ... },
       { id = "output", type = "output", label = "Results", ... }
   ]
   ```

## Validation Checklist

Before considering your tool complete:

- [ ] All imports work: `python -c 'import tool_name'`
- [ ] CLI works: `python -m tool_name --help`
- [ ] Uses recursive glob: `glob("**/*.ext")`
- [ ] Validates minimum inputs
- [ ] Uses defensive LLM parsing with type guards
- [ ] Progress logging with `logger.info()`
- [ ] Session directory in `.data/tool_name/sessions/`
- [ ] Output path parent directory creation
- [ ] Formatting passes: `uv run ruff format --check .`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Type checking passes: `uv run pyright .`

## Common Pitfalls to Avoid

1. **Don't use `@click.argument`** - breaks Web UI introspection
2. **Don't use object defaults** like `default=Path()` - use strings
3. **Don't forget type guards** after `parse_llm_json()`
4. **Don't store runtime data** in tool's own directory - use `.data/`
5. **Don't assume parent directories exist** when writing output files
6. **Don't skip validation** - run the full validation loop

## Example Adaptations

### Invoice Parser for Different Industries

Replace categories in `categorizer/core.py`:
```python
EXPENSE_CATEGORIES = [
    "materials",
    "labor",
    "equipment",
    "subcontractors",
    "permits",
    "other"
]
```

### Receipt Scanner for Personal Finances

Modify `expense_parser/core.py` prompts:
```python
system_prompt = """Extract personal expense information.
Categories: groceries, dining, transportation, entertainment, utilities, other."""
```

### Time Tracking for Freelancers

Focus on `time_parser/` module, enhance with:
- Project/client assignment
- Billable vs non-billable hours
- Time period summaries

The modular structure makes these adaptations straightforward!
