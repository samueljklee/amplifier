# How to Create Your Own arXiv Extractor Tool

This guide explains the design patterns and principles used in `extract_arxiv_summary`, so you can adapt it for your own needs or create similar tools.

## Why This Tool Exists

As software engineers working in AI, we frequently need to:
1. Stay current with academic research
2. Extract practical insights from papers
3. Identify relevant techniques for our work
4. Quickly understand whether a paper is worth deep reading

This tool automates the extraction and summarization process, focusing on what matters most to engineers rather than researchers.

## Architecture Overview

### Simple Single-Module Design

This tool uses a **simple structure** with one `core.py` file because:
- Single responsibility: fetch and summarize arXiv papers
- Linear workflow: fetch → extract → save
- No reusable sub-components needed
- All logic fits comfortably in <200 lines

```
extract_arxiv_summary/
├── main.py              # CLI orchestrator
├── core.py              # All business logic
├── __init__.py          # Package metadata
├── __main__.py          # Entry point
├── pyproject.toml       # Dependencies
├── README.md            # User documentation
└── HOW_TO_CREATE_YOUR_OWN.md  # This file
```

### Key Patterns Used

#### 1. CLI Design (main.py)

**Critical patterns from blog_writer:**
```python
@add_describe_flag(version="0.1.0", display_name="arXiv Summary Extractor")
@click.command()
@click.option("--url", type=str, required=True)  # Always use @click.option
@click.option("--output", type=str, default="arxiv_summary.json")  # String defaults
```

**Why:**
- `@add_describe_flag`: Enables Web UI introspection
- `@click.option` only: Arguments break Web UI
- String defaults: Path() objects break introspection

#### 2. Progress Visibility (core.py)

**Show users what's happening:**
```python
logger.stage_transition(None, "fetch_paper", estimated_duration=10)
logger.info("📥 Fetching arXiv paper...")
# ... do work ...
logger.info(f"✓ Fetched paper (approx {len(paper_content)} characters)")
```

**Why:**
- Users need to see progress for long-running operations
- Stage transitions help Web UI visualize workflow
- Clear checkmarks (✓) show successful completion

#### 3. Runtime Data Storage

**Store data in .data/ directory:**
```python
def _create_session_dir() -> Path:
    base_dir = Path.cwd() / ".data" / "extract_arxiv_summary" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid.uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)
    # ... create 'latest' symlink ...
    return session_dir
```

**Why:**
- Keeps runtime data separate from code
- Makes tool discoverable by Web UI
- Enables debugging and recovery
- Latest symlink provides easy access

#### 4. Defensive LLM Integration

**Parse LLM output safely:**
```python
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

# ... in async function ...
async with ClaudeSession(options) as session:
    response = await session.query(prompt)
    content = response.content.strip()

    # Use defensive parsing
    summary_data = parse_llm_json(content)

    # Validate required fields
    required_fields = ["summary", "key_points_for_ai_engineers"]
    for field in required_fields:
        if field not in summary_data:
            logger.error(f"Missing required field: {field}")
            return None
```

**Why:**
- LLMs sometimes return malformed JSON
- Defensive parsing handles edge cases
- Validation ensures data quality
- Clear error messages aid debugging

#### 5. Input Validation

**Fail early with clear messages:**
```python
# In main()
if "arxiv.org" not in url.lower():
    logger.error("URL must be from arxiv.org")
    sys.exit(1)

# In core
arxiv_id = _extract_arxiv_id(url)
if not arxiv_id:
    logger.error("Could not extract arXiv ID from URL")
    return None
```

**Why:**
- Catch problems before expensive operations
- Save user time and API costs
- Provide actionable error messages

## Adapting This Tool

### For Different Paper Sources

To adapt for other academic paper sources (e.g., ACM, IEEE):

1. **Modify URL validation** in `main.py`:
```python
if "acm.org" not in url.lower():
    logger.error("URL must be from acm.org")
    sys.exit(1)
```

2. **Update fetch logic** in `core.py`:
```python
async def _fetch_acm_paper(url: str, logger: ToolkitLogger) -> str | None:
    # Extract ACM paper ID
    paper_id = _extract_acm_id(url)
    # Fetch using appropriate method
    ...
```

3. **Adjust extraction prompt** for different paper formats:
```python
prompt = f"""Analyze this ACM paper...
Note: ACM papers have sections labeled differently than arXiv...
"""
```

### For Different Focus Areas

To create a specialized version (e.g., for data scientists):

1. **Change default focus** in `main.py`:
```python
@click.option(
    "--focus",
    type=str,
    default="data science and statistical methods",  # Changed
    help="Focus area for key points",
)
```

2. **Update extraction fields** in `core.py`:
```python
{
  "key_points_for_data_scientists": [...],  # Renamed
  "statistical_methods": [...],              # New field
  "datasets_used": [...],                    # New field
  ...
}
```

3. **Adjust system prompt**:
```python
options = SessionOptions(
    system_prompt="You are an expert at analyzing papers for data scientists.",
    retry_attempts=2,
)
```

### Adding Multi-Step Analysis

If you need complex multi-step processing (like blog_writer), consider:

1. **Create functional modules**:
```
extract_arxiv_summary/
├── main.py
├── fetcher/
│   ├── __init__.py
│   └── core.py
├── analyzer/
│   ├── __init__.py
│   └── core.py
└── formatter/
    ├── __init__.py
    └── core.py
```

2. **Each module exports a class**:
```python
# analyzer/__init__.py
from .core import PaperAnalyzer
__all__ = ["PaperAnalyzer"]
```

3. **Orchestrate in main.py**:
```python
from .fetcher import PaperFetcher
from .analyzer import PaperAnalyzer
from .formatter import ResultFormatter

fetcher = PaperFetcher()
analyzer = PaperAnalyzer()
formatter = ResultFormatter()

paper = await fetcher.fetch(url)
analysis = await analyzer.analyze(paper)
await formatter.save(analysis, output_path)
```

## Testing Your Tool

### 1. Install Dependencies
```bash
cd scenarios/extract_arxiv_summary
uv sync
```

### 2. Test Imports
```bash
python -c "import extract_arxiv_summary"
```

### 3. Test CLI
```bash
python -m extract_arxiv_summary --help
```

### 4. Test with Real Paper
```bash
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --output test_summary.json \
    --verbose
```

### 5. Validate Code Quality
```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright .
```

## Common Pitfalls

### ❌ Using @click.argument
```python
@click.argument("url")  # DON'T: Breaks Web UI
```

### ✅ Use @click.option instead
```python
@click.option("--url", required=True)  # DO: Works with Web UI
```

---

### ❌ Path() as default
```python
@click.option("--output", default=Path("summary.json"))  # DON'T: Breaks introspection
```

### ✅ String defaults
```python
@click.option("--output", default="summary.json")  # DO: Introspectable
```

---

### ❌ No progress logging
```python
result = await long_operation()  # DON'T: User sees nothing
```

### ✅ Show progress
```python
logger.info("🔄 Running operation...")
result = await long_operation()
logger.info("✓ Operation complete")
```

---

### ❌ Storing data in tool directory
```python
output = Path(__file__).parent / "results.json"  # DON'T: Mixes code and data
```

### ✅ Store in .data/
```python
session_dir = Path.cwd() / ".data" / "tool_name" / "sessions" / session_id
output = session_dir / "results.json"  # DO: Separates code and data
```

## Key Takeaways

1. **Keep it simple**: Use single core.py unless you need multiple modules
2. **Show progress**: Users need to see what's happening
3. **Validate early**: Check inputs before expensive operations
4. **Parse defensively**: LLMs return messy data sometimes
5. **Separate data**: Runtime data goes in .data/, not with code
6. **Follow patterns**: Study blog_writer for CLI and session patterns
7. **Test thoroughly**: Run all validation checks before finishing

## Next Steps

1. **Study the code**: Read through `core.py` and `main.py` completely
2. **Try modifications**: Change the focus area or output format
3. **Create your own**: Use this as a template for similar tools
4. **Share patterns**: Document what works for others to learn from

## Questions?

- Check the main README.md for usage examples
- Look at blog_writer for multi-module patterns
- Review amplifier docs for ccsdk_toolkit details
