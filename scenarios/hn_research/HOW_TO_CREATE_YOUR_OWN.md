# How to Create Your Own Research Tool

This guide explains how `hn_research` works and how to adapt it for other research tasks.

## Why This Tool Exists

HN Research demonstrates a **research and reporting pipeline** pattern:
1. **Fetch** data from external sources
2. **Analyze** content with LLM
3. **Enrich** with additional context (term explanations)
4. **Visualize** relationships
5. **Compile** comprehensive report

This pattern works for any scenario where you need to gather, analyze, and report on data from external sources.

## Key Patterns

### 1. Modular Architecture

The tool is organized into functional modules:

```
hn_research/
├── main.py                 # Orchestrator
├── fetcher/               # Data acquisition
├── analyzer/              # LLM-based analysis
├── term_explainer/        # Context enrichment
├── visualizer/            # Diagram generation
└── report_generator/      # Report compilation
```

**Why this matters:** Each module has a single responsibility and can be developed/tested independently.

### 2. Session-Based Data Storage

```python
base_dir = Path.cwd() / ".data" / "hn_research" / "sessions"
session_dir = base_dir / f"{timestamp}_{guid}"
```

**Why this matters:**
- Keeps runtime data separate from code
- Allows multiple runs without conflicts
- Makes debugging easier (inspect intermediate files)
- Web UI can discover and display results

### 3. Defensive LLM Parsing

```python
result = parse_llm_json(response.content)

# REQUIRED: Type guard
if not isinstance(result, dict):
    logger.error("Expected dict from LLM, got invalid format")
    return fallback_result()
```

**Why this matters:** LLMs can return unexpected formats. Always validate before using results.

### 4. Progress Logging

```python
logger.stage_transition("fetch_data", "analyze_posts", estimated_duration=60)
logger.info("🔍 Analyzing posts for trends...")
```

**Why this matters:** Users (and Web UI) need visibility into long-running processes.

### 5. Graceful Fallbacks

```python
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    return self._fallback_analysis(posts)
```

**Why this matters:** Tool should provide useful output even when LLM calls fail.

## Adapting for Other Sources

### Example: Reddit Research

```python
# 1. Change fetcher to use Reddit API
class Fetcher:
    async def fetch_top_posts(self, subreddit: str, limit: int):
        # Use PRAW or httpx to fetch Reddit posts
        ...

# 2. Adjust analyzer prompts for Reddit culture
prompt = f"""Analyze these Reddit posts from r/{subreddit}...
Consider Reddit-specific dynamics like upvotes, awards, subreddit culture..."""

# 3. Update term_explainer for community-specific jargon
# 4. Keep visualizer and report_generator mostly the same
```

### Example: GitHub Trending

```python
# 1. Change fetcher to use GitHub API
class Fetcher:
    async def fetch_trending_repos(self, language: str, limit: int):
        # Use GitHub API to fetch trending repositories
        ...

# 2. Adjust analyzer for repository analysis
prompt = f"""Analyze these GitHub repositories...
Identify common technologies, emerging patterns, notable projects..."""

# 3. term_explainer focuses on tech stacks and frameworks
# 4. visualizer shows technology relationships
```

## Key Design Decisions

### Why 5 modules?

Each module maps to a distinct phase of the pipeline:
1. **Fetching** - External data acquisition (API-specific)
2. **Analysis** - Understanding content (LLM-heavy)
3. **Enrichment** - Adding context (specialized LLM task)
4. **Visualization** - Creating diagrams (structured output)
5. **Reporting** - Compiling results (formatting)

This separation makes it easy to:
- Replace the fetcher for different data sources
- Modify analysis without changing reporting
- Skip enrichment if not needed
- Use different visualization formats

### Why async/await?

```python
async def fetch_top_posts(self, limit: int):
    async with httpx.AsyncClient() as client:
        # Concurrent API calls
```

**Benefits:**
- Fetch multiple posts concurrently
- Don't block on I/O
- Better performance for data-heavy operations

### Why session directories?

```
.data/hn_research/sessions/20250126_143522_a3b4c5d6/
├── raw_posts.json       # Original data
├── analysis.json        # LLM analysis
└── hn_research_20250126.md  # Final report
```

**Benefits:**
- Reproducible results (can re-run report generation)
- Debugging (inspect intermediate steps)
- Caching (skip expensive API calls if data exists)

## Checklist for Your Own Tool

- [ ] Identify data source (API, web scraping, file system)
- [ ] Design module structure (3-5 modules typically)
- [ ] Implement fetcher with proper error handling
- [ ] Write LLM prompts for analysis (be specific!)
- [ ] Add type guards after `parse_llm_json()`
- [ ] Implement fallback logic for LLM failures
- [ ] Add progress logging at each stage
- [ ] Create session directories for runtime data
- [ ] Generate final report in requested format
- [ ] Write README with examples
- [ ] Test with `--verbose` to see full execution

## Common Pitfalls

1. **Forgetting type guards:** Always check `isinstance(result, dict)` after `parse_llm_json()`
2. **No fallbacks:** What happens when LLM fails? Have a basic fallback.
3. **Missing progress logs:** Users need to see what's happening
4. **Hardcoded paths:** Use session directories, not fixed file names
5. **No error handling:** Wrap API calls in try/except
6. **Vague prompts:** Be specific about what you want from the LLM

## Learn More

- Study `blog_writer` for multi-iteration workflows with user feedback
- Study `transcribe` for file-based processing pipelines
- Read the Amplifier documentation for more utilities and patterns
