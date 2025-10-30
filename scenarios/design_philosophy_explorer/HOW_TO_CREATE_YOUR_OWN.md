# How to Create Your Own Design Philosophy Explorer

This guide explains how to create similar design exploration tools or adapt this one.

## Why This Tool Exists

Design is often treated as mysterious "taste" rather than learnable principles. This tool:
- **Demystifies design**: Breaks down concepts into understandable components
- **Bridges theory and practice**: Connects design philosophy to actual implementations
- **Provides guidance**: Offers actionable next steps, not just critique
- **Educates**: Explains the reasoning behind recommendations

## Key Patterns

### 1. Modular Architecture (Bricks & Studs)

The tool uses 4 functional modules, each with a clear responsibility:

```
design_philosophy_explorer/
├── philosopher/       # Explores design concepts
├── analyzer/         # Analyzes code implementations
├── critic/           # Generates critique and suggestions
└── reporter/         # Creates comprehensive reports
```

**Why This Works:**
- Each module is independently testable
- Clear separation of concerns
- Easy to regenerate or replace modules
- Scales from simple to complex

### 2. State Management with Resume

The `StateManager` enables interruption recovery:

```python
class StateManager:
    def __init__(self, session_dir: Path | None = None):
        # Creates: .data/tool_name/sessions/{timestamp}_{guid}/
        # Saves state after EVERY operation
        # Creates 'latest' symlink for easy resume
```

**Benefits:**
- Long-running operations can be interrupted
- Debugging is easier with saved state
- Users can resume after crashes or interruptions

### 3. Defensive LLM Integration

Uses defensive utilities from `amplifier.ccsdk_toolkit.defensive`:

```python
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

result = parse_llm_json(response.content)

# ALWAYS add type guard
if not isinstance(result, dict):
    logger.error("Expected dict from LLM")
    return fallback_response()
```

**Why This Matters:**
- LLMs don't always return valid JSON
- Type guards prevent runtime crashes
- Fallback responses ensure tool always completes

### 4. Recursive File Discovery

**CRITICAL PATTERN** - Uses recursive glob:

```python
# ✅ CORRECT - Finds files in subdirectories
files = list(directory.glob("**/*.css"))

# ❌ WRONG - Only finds files in top level
files = list(directory.glob("*.css"))
```

### 5. Progressive Disclosure in Reports

Reports structure information from high-level to detailed:

1. **Concepts Explored**: What design principles apply
2. **Implementation Analysis**: What's actually in the code
3. **Recommendations**: Prioritized improvements
4. **Summary**: Key takeaways and action items

**Benefits:**
- Users can skim or deep-dive
- Actionable immediately (summary)
- Educational (concepts)

## How to Adapt This Tool

### For Different Design Aspects

To create a **color-theory-explorer**:

```python
# 1. Modify philosopher/core.py
prompt = """Explore color theory for this question:
{question}

Cover:
- Color psychology
- Color harmonies (complementary, analogous, triadic)
- Accessibility (WCAG contrast ratios)
- Cultural considerations
- Color in UI systems
"""

# 2. Modify analyzer/core.py to find color-related patterns
file_patterns = ["**/*.css", "**/*.scss", "**/*.theme.ts"]

prompt = """Analyze color usage:
- Color palettes and tokens
- Contrast ratios
- Theme implementations
- Consistency across files
"""
```

### For Different Domains

To create a **performance-philosophy-explorer**:

```python
# Modules would be:
# - philosopher/: Performance concepts
# - analyzer/: Code profiling and bottlenecks
# - critic/: Optimization suggestions
# - reporter/: Performance report

# Analyzer would look for:
file_patterns = ["**/*.js", "**/*.tsx", "**/*.py"]

# Focus on:
# - Bundle sizes
# - Lazy loading patterns
# - Async operations
# - Caching strategies
```

## Key Learnings

### 1. Structure Enables Regeneration

By keeping each module self-contained:
- You can regenerate any module independently
- Updates don't break other modules
- Testing is straightforward

### 2. Fallbacks Ensure Reliability

Every AI query has a fallback:

```python
try:
    result = await session.query(prompt)
    parsed = parse_llm_json(result.content)
    return parsed
except Exception as e:
    logger.error(f"Query failed: {e}")
    return fallback_response()
```

**Never let AI failures break the tool.**

### 3. Type Guards Prevent Crashes

LLMs can return unexpected formats:

```python
# LLM might return: dict, list, or malformed JSON
result = parse_llm_json(response)

# Always check type before using
if not isinstance(result, dict):
    return fallback()

# Now safe to use dict operations
value = result.get("key", "default")
```

### 4. Progressive File Sampling

Don't overwhelm context windows:

```python
max_files = 10
max_chars_per_file = 2000

for file in files[:max_files]:
    content = file.read_text()[:max_chars_per_file]
    samples.append(content)
```

**Analyze representative samples, not entire codebases.**

### 5. Logging Shows Progress

Users need visibility:

```python
logger.info(f"Found {len(files)} files")
for f in files[:5]:
    logger.info(f"  • {f.name}")
if len(files) > 5:
    logger.info(f"  ... and {len(files) - 5} more")
```

## Testing Your Tool

Create `tests/test_modules.py`:

```python
def test_philosopher_basic():
    philosopher = DesignPhilosopher()
    result = asyncio.run(philosopher.explore("What is color theory?"))
    assert result is not None
    assert "concepts" in result

def test_analyzer_empty_directory(tmp_path):
    analyzer = DesignAnalyzer()
    result = asyncio.run(analyzer.analyze(tmp_path, {}))
    assert result["file_count"] == 0

def test_critic_fallback():
    critic = DesignCritic()
    result = critic._fallback_critique()
    assert "suggestions" in result
```

## Common Pitfalls

### 1. Not Handling Missing Directory

```python
# ✅ Handle gracefully
if not directory.exists():
    logger.error(f"Directory not found: {directory}")
    return empty_analysis()
```

### 2. Forgetting Parent Directory Creation

```python
# ✅ Create parent dirs for output
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(content)
```

### 3. Not Validating LLM Responses

```python
# ✅ Always validate type
result = parse_llm_json(response)
if not isinstance(result, dict):
    return fallback()
```

### 4. Using Non-Recursive Globs

```python
# ❌ Only finds top-level files
files = list(dir.glob("*.css"))

# ✅ Finds files in subdirectories
files = list(dir.glob("**/*.css"))
```

## Next Steps

To create your own tool:

1. **Define your domain**: What aspect are you exploring?
2. **Identify modules**: What are the 3-5 key functions?
3. **Design the pipeline**: What's the flow from input to output?
4. **Create specifications**: Write clear contracts for each module
5. **Implement and test**: Build one module at a time
6. **Add state management**: Enable resume capability
7. **Write comprehensive README**: Help others use your tool

## Philosophy Alignment

This tool follows Amplifier's core principles:

- **Ruthless Simplicity**: 4 focused modules, clear flow
- **Bricks and Studs**: Each module is regeneratable
- **Defensive by Default**: Fallbacks and type guards everywhere
- **User-Centered**: Clear progress, actionable output
- **Educational**: Explains the "why" behind recommendations

## Resources

- [Amplifier Design Philosophy](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md)
- [Modular Design Philosophy](../../ai_context/MODULAR_DESIGN_PHILOSOPHY.md)
- [Blog Writer Example](../blog_writer/) - Reference implementation
- [Defensive Utilities](../../amplifier/ccsdk_toolkit/defensive/) - LLM parsing
