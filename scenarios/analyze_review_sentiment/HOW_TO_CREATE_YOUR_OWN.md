# How to Create Your Own Review Analysis Tool

This guide explains how the `analyze_review_sentiment` tool works and how you can adapt it for your own needs.

## Why This Tool Exists

Businesses receive customer feedback in many forms: reviews, surveys, support tickets, social media comments. This tool helps by:
1. **Automating sentiment analysis** across large volumes of feedback
2. **Prioritizing actionable items** so teams focus on high-impact improvements
3. **Providing concrete suggestions** to turn feedback into action

## Architecture Overview

This tool follows the **modular "bricks and studs" pattern** used by all Amplifier tools:

```
analyze_review_sentiment/
├── main.py                    # Orchestrator (coordinates modules)
├── extractor/                 # Module: PDF text extraction
│   ├── __init__.py
│   └── core.py
├── analyzer/                  # Module: Sentiment & actionability
│   ├── __init__.py
│   └── core.py
└── formatter/                 # Module: Report generation
    ├── __init__.py
    └── core.py
```

### Why 3 Modules?

Each module has a **single responsibility**:
- **extractor/**: Handles PDF parsing (can be swapped for other formats)
- **analyzer/**: Contains AI logic (isolated for testing/tuning)
- **formatter/**: Generates output (easy to change format)

This makes the tool **maintainable, testable, and adaptable**.

## Key Patterns to Learn

### 1. Module Interface Pattern

Each module exports its main class through `__init__.py`:

```python
# analyzer/__init__.py
from .core import SentimentAnalyzer

__all__ = ["SentimentAnalyzer"]
```

This is the "studs" - the connection point other modules use.

### 2. Orchestrator Pattern (main.py)

The `main.py` **coordinates** modules but doesn't contain business logic:

```python
class ReviewAnalysisPipeline:
    def __init__(self, session_dir: Path):
        self.extractor = PDFExtractor()      # Initialize modules
        self.analyzer = SentimentAnalyzer()
        self.formatter = ReportFormatter()

    async def run(self, pdf_path: Path, output_path: Path | None = None):
        # Coordinate the workflow
        text = await self.extractor.extract_text(pdf_path)
        analysis = await self.analyzer.analyze(text)
        report = self.formatter.format_report(analysis)
```

### 3. Defensive LLM Parsing

**CRITICAL**: Always type-guard LLM responses:

```python
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json

# Parse LLM response
result = parse_llm_json(response.content)

# ✅ REQUIRED: Type guard before dict operations
if not isinstance(result, dict):
    logger.error("Expected dict from LLM, got invalid format")
    return None

# Now safe to use dict operations
if "field" not in result:
    logger.error("Missing required field")
    return None
```

**Why**: `parse_llm_json()` returns `dict | list | None`, so you must check the type before using dict-specific operations.

### 4. Session Management

Store runtime data in `.data/{tool_name}/sessions/`:

```python
from datetime import datetime
import uuid

# Create session directory
base_dir = Path.cwd() / ".data" / "analyze_review_sentiment" / "sessions"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
guid = uuid.uuid4().hex[:8]
session_dir = base_dir / f"{timestamp}_{guid}"
session_dir.mkdir(parents=True, exist_ok=True)

# Create 'latest' symlink
latest_link = base_dir / "latest"
if latest_link.exists():
    latest_link.unlink()
latest_link.symlink_to(session_dir.name)
```

### 5. Web UI Output Path Handling

**CRITICAL**: Always create parent directories for output paths:

```python
if output_path is None:
    output_path = self.session_dir / "sentiment_report.md"
else:
    # ✅ REQUIRED: Create parent directory for Web UI paths
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

# Now safe to write
output_path.write_text(report_content)
```

**Why**: Web UI provides paths like `/tmp/amplifier_scenario_inputs/{uuid}/output.md`, but doesn't pre-create parent directories.

### 6. Stage Transitions for Web UI

Use `logger.stage_transition()` to show progress in Web UI:

```python
logger.stage_transition(None, "extract_text", estimated_duration=10)
logger.info("📄 Extracting text from PDF...")

# ... do work ...

logger.stage_transition("extract_text", "analyze_sentiment", estimated_duration=30)
logger.info("🔍 Analyzing sentiment...")
```

Stage IDs must match `pyproject.toml` workflow metadata.

### 7. Click CLI Options (Never Arguments!)

**✅ CORRECT** - Use @click.option:
```python
@click.option("--pdf", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--output", type=str, default=None)
def main(pdf: Path, output: str | None):
    pass
```

**❌ WRONG** - Never use @click.argument (breaks Web UI):
```python
@click.argument("pdf")  # ❌ Breaks Web UI introspection
```

### 8. Workflow Metadata for Web UI

Add workflow visualization to `pyproject.toml`:

```toml
[tool.amplifier.workflow]
stages = [
    { id = "pdf_input", type = "input", label = "PDF Input", prompt = "Select PDF..." },
    { id = "extract_text", type = "process", label = "Extract Text", depends_on = ["pdf_input"] },
    { id = "analyze_sentiment", type = "process", label = "Analyze", depends_on = ["extract_text"] },
    { id = "generate_report", type = "output", label = "Report", depends_on = ["analyze_sentiment"] }
]

[tool.amplifier.workflow.layout]
positions.pdf_input = [100, 150]
positions.extract_text = [350, 150]
positions.analyze_sentiment = [600, 150]
positions.generate_report = [850, 150]
```

## How to Adapt This Tool

### Change Input Format (e.g., CSV instead of PDF)

Replace the `extractor/` module:

```python
# extractor/core.py
import csv

class CSVExtractor:
    async def extract_text(self, csv_path: Path) -> str:
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            reviews = [row['review_text'] for row in reader]
            return "\n\n".join(reviews)
```

Update `main.py` imports - that's it! The other modules don't change.

### Change Analysis Logic

Modify `analyzer/core.py` prompt or scoring logic. The module is isolated, so changes won't affect extraction or formatting.

### Add a New Module

Want to add sentiment trends over time? Create a new module:

```
trends/
├── __init__.py
└── core.py
```

Import it in `main.py` and coordinate with other modules.

### Change Output Format (e.g., JSON instead of Markdown)

Replace the `formatter/` module or add a new one:

```python
# formatter/core.py
class JSONFormatter:
    def format_report(self, analysis: dict) -> str:
        return json.dumps(analysis, indent=2)
```

## Common Pitfalls

### ❌ Don't: Put business logic in main.py
```python
# ❌ WRONG
async def run(self):
    # Don't extract PDF in main.py
    reader = pypdf.PdfReader(self.pdf_path)
    text = reader.pages[0].extract_text()
```

### ✅ Do: Put logic in modules
```python
# ✅ CORRECT
async def run(self):
    text = await self.extractor.extract_text(self.pdf_path)
```

### ❌ Don't: Skip type guards on LLM responses
```python
# ❌ WRONG
result = parse_llm_json(response.content)
if "field" not in result:  # Type error if result is None or list!
    return None
```

### ✅ Do: Always check isinstance()
```python
# ✅ CORRECT
result = parse_llm_json(response.content)
if not isinstance(result, dict):
    return None
if "field" not in result:
    return None
```

### ❌ Don't: Use @click.argument
```python
# ❌ WRONG - breaks Web UI
@click.argument("pdf")
```

### ✅ Do: Use @click.option with required=True
```python
# ✅ CORRECT
@click.option("--pdf", required=True)
```

### ❌ Don't: Assume output path parent exists
```python
# ❌ WRONG
Path(output_path).write_text(content)  # Fails if parent dir doesn't exist
```

### ✅ Do: Create parent directory first
```python
# ✅ CORRECT
output_path = Path(output_path)
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(content)
```

## Testing Your Adapted Tool

1. **Install dependencies**: `cd your_tool && uv sync`
2. **Test imports**: `python -c "import your_tool"`
3. **Test CLI**: `python -m your_tool --help`
4. **Check formatting**: `uv run ruff format --check .`
5. **Check linting**: `uv run ruff check .`
6. **Check types**: `uv run pyright .`

## Module Design Guidelines

### How Many Modules?

- **1-2 modules**: Simple tools (single input/output, minimal processing)
- **3-5 modules**: Medium tools (like this one - distinct stages)
- **6-9 modules**: Complex tools (multiple workflows, state management)

### Module Naming

Use **verb-based** functional names:
- ✅ extractor/, analyzer/, formatter/, validator/
- ❌ pdf/, sentiment/, markdown/ (noun-based, unclear responsibility)

### When to Split a Module

Split when:
1. A module has multiple distinct responsibilities
2. You want to reuse part of the logic elsewhere
3. Testing/mocking becomes difficult
4. The core.py file exceeds ~200-300 lines

### When to Combine Modules

Combine when:
1. Two modules are always used together
2. One module is trivial (< 50 lines)
3. The boundary between them is unclear

## Additional Resources

- **blog_writer**: Reference example with 6 modules and state management
- **transcribe**: Complex example with 9 modules and multiple file types
- **Amplifier CCSDK Toolkit**: Core utilities for Claude sessions, logging, defensive parsing

## Philosophy: "Bricks and Studs"

Each module is a **brick** - complete, self-contained, regeneratable independently.
Each `__init__.py` is a **stud** - the connection point for assembling bricks.

This makes your tool:
- **Maintainable**: Changes isolated to specific modules
- **Testable**: Mock one module, test another
- **Adaptable**: Swap modules without rewriting everything
- **Understandable**: Each module's purpose is clear

Build tools like LEGO - not monolithic sculptures.
