# How to Create Your Own Repository Analyzer

This guide explains how `generate_repo_faq` works and how to adapt it for your own repository analysis needs.

## 🎯 Why This Tool Exists

Documentation often lags behind code. This tool:
1. **Automates** the tedious task of reading through code to understand what a project does
2. **Extracts** key information from both code and existing docs
3. **Generates** comprehensive FAQs that answer common questions
4. **Saves time** for maintainers and new contributors

## 🏗️ Architecture Overview

### Modular Design

The tool uses a 3-module pipeline architecture:

```
generate_repo_faq/
├── main.py              # CLI orchestrator
├── extractor/          # File discovery and reading
│   └── core.py
├── analyzer/           # AI-powered code analysis
│   └── core.py
└── formatter/          # FAQ generation
    └── core.py
```

Each module has a single responsibility:
- **Extractor**: Discovers and reads files (with filtering)
- **Analyzer**: Understands what the code does (using LLM)
- **Formatter**: Generates readable FAQ markdown

### Pipeline Flow

```
Repository Path → Extract Files → Analyze Content → Generate FAQ → Save Output
```

## 🔑 Key Patterns Used

### 1. Recursive File Discovery

```python
# Use glob('**/*.ext') for recursive search
for ext in SOURCE_EXTENSIONS:
    pattern = f"**/*{ext}"
    for file_path in repo_path.glob(pattern):
        if self._should_include(file_path, repo_path):
            source_files.append(file_path)
```

**Why**: Handles nested directory structures without manual recursion.

### 2. Defensive Filtering

```python
AUTO_IGNORE = [".venv", "node_modules", "__pycache__", ...]

def _should_include(self, file_path: Path, repo_root: Path) -> bool:
    """Check against ignore patterns."""
    # ... filtering logic
```

**Why**: Prevents analyzing irrelevant files (dependencies, build artifacts).

### 3. Input Validation

```python
total_files = len(source_files) + len(doc_files)
if total_files == 0:
    logger.warning("No files found in repository after filtering")
    return {"source_files": [], "doc_files": [], "structure": {}}

if total_files < 3:
    logger.warning(f"Only {total_files} files found - may not be sufficient")
```

**Why**: Fails fast with clear error messages instead of producing poor results.

### 4. Defensive LLM Parsing

```python
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json

result = parse_llm_json(response.content)

# CRITICAL: Type guard immediately after parsing
if not isinstance(result, dict):
    logger.error("Expected dict from LLM, got invalid format")
    return None
```

**Why**: LLMs can return unexpected formats; defensive parsing prevents crashes.

### 5. Progress Visibility

```python
logger.stage_transition(None, "extract_files", estimated_duration=10)
logger.info("📂 Extracting repository files...")
# ... work happens ...
logger.info(f"✓ Extracted {len(files)} files")
```

**Why**: Users see progress, especially important for long-running operations.

### 6. Web UI Compatibility

```python
# Create parent directory before writing (Web UI doesn't pre-create)
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(faq_content)
```

**Why**: Web UI passes paths in `/tmp/` that may not exist.

## 🔧 How to Adapt This Tool

### Example: Generate API Documentation Instead of FAQ

**Changes needed:**

1. **Analyzer module** - Look for API endpoints instead of general purpose:
```python
prompt = """Find all API endpoints in this code:
- REST endpoints (GET, POST, PUT, DELETE)
- GraphQL schemas
- RPC methods

Return structured JSON with endpoint details."""
```

2. **Formatter module** - Generate API docs instead of FAQ:
```python
prompt = """Generate OpenAPI/Swagger documentation for these endpoints:
{endpoints}

Format as YAML with full specs."""
```

3. **Update CLI** - Rename options for clarity:
```python
@click.option("--api-format", type=click.Choice(["openapi", "markdown"]), ...)
```

### Example: Generate Architecture Diagrams

**Changes needed:**

1. **Add new module** `diagrammer/`:
```python
class DiagramGenerator:
    async def generate_diagram(self, analysis):
        # Use mermaid.js syntax to create flowcharts
        return mermaid_diagram
```

2. **Update formatter** to include diagrams in output:
```python
faq_content = f"""# Architecture

{diagram}

# FAQ

{faq_sections}
"""
```

### Example: Multi-Language Support

**Changes needed:**

1. **Extractor** - Add language detection:
```python
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".ts", ".jsx", ".tsx"],
    "go": [".go"],
}

def _detect_primary_language(self, source_files):
    # Count files by extension
    # Return most common language
```

2. **Analyzer** - Tailor prompts per language:
```python
if language == "python":
    prompt += "\nFocus on Python idioms, decorators, type hints."
elif language == "go":
    prompt += "\nFocus on goroutines, interfaces, channels."
```

## 📚 Learning Resources

### Related Tools to Study

1. **blog_writer** - Multi-stage pipeline with user interaction
2. **transcribe** - Media file processing (shows binary file handling)
3. **web_to_md** - Web content extraction (shows external API usage)

### Key Files to Read

- `amplifier/ccsdk_toolkit/session.py` - ClaudeSession usage
- `amplifier/ccsdk_toolkit/defensive/llm_parsing.py` - Safe JSON parsing
- `scenarios/blog_writer/main.py` - Complex state management

## 🎓 Best Practices Demonstrated

1. ✅ **Use `@click.option` not `@click.argument`** - Web UI compatibility
2. ✅ **Add `@add_describe_flag`** - Enables tool introspection
3. ✅ **Store data in `.data/{tool_name}/`** - Not in tool directory
4. ✅ **Use recursive glob patterns** - `**/*.ext` finds all nested files
5. ✅ **Validate inputs early** - Fail fast with clear messages
6. ✅ **Log progress** - `logger.info()` for each major step
7. ✅ **Type guard LLM responses** - Check `isinstance()` after parsing
8. ✅ **Create parent dirs** - Before writing to Web UI paths

## 🚀 Next Steps

1. **Experiment**: Run the tool on different repositories
2. **Customize**: Modify prompts to change FAQ style/content
3. **Extend**: Add new modules for additional analysis types
4. **Share**: Create your own analyzer following this pattern

Happy building! 🛠️
