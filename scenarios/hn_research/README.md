# HN Research

Analyze top Hacker News posts to identify trends, relationships, and provide intelligent summaries with visualizations.

## Purpose

HN Research automatically fetches the top posts from Hacker News, analyzes their content and comments to identify trending topics, explains technical terms, and generates a comprehensive markdown report with visualizations showing topic relationships.

## Quick Start

```bash
# Basic usage - analyze top 20 posts
python -m scenarios.hn_research

# Analyze more posts
python -m scenarios.hn_research --post-limit 30

# Specify custom output path
python -m scenarios.hn_research --output ~/reports/hn_research.md

# Verbose logging
python -m scenarios.hn_research --verbose
```

## What It Does

1. **Fetches HN Data**: Retrieves top posts from Hacker News API with comments
2. **Analyzes Topics**: Uses LLM to identify categories, trends, and relationships
3. **Explains Terms**: Extracts and explains technical jargon and advanced terms
4. **Generates Visualization**: Creates Mermaid diagrams showing topic relationships
5. **Compiles Report**: Produces comprehensive markdown report with all insights

## Output

The tool generates:
- `hn_research_YYYYMMDD.md` - Main report with:
  - Executive summary of key trends
  - Topic relationship diagram (Mermaid)
  - Categorized topic summaries
  - Notable developments
  - Technical terms glossary
  - Complete post index
- `raw_posts.json` - Raw HN API data (in session directory)
- `analysis.json` - Analysis results (in session directory)

## Session Data

Runtime data is stored in `.data/hn_research/sessions/{timestamp}_{guid}/`:
- Session-specific intermediate files
- State and logs
- Symlink at `.data/hn_research/sessions/latest` points to most recent session

## Options

- `--output PATH` - Custom output path for final report
- `--post-limit N` - Number of top posts to analyze (default: 20)
- `--verbose` - Enable verbose logging

## Examples

```bash
# Daily research routine
python -m scenarios.hn_research --post-limit 25 --output ~/daily_hn/$(date +%Y%m%d).md

# Quick scan of top 10
python -m scenarios.hn_research --post-limit 10

# Deep dive with all details
python -m scenarios.hn_research --post-limit 50 --verbose
```

## Troubleshooting

**No posts fetched:**
- Check internet connection
- Verify HN API is accessible: `curl https://hacker-news.firebaseio.com/v0/topstories.json`

**Analysis seems incomplete:**
- Increase `--post-limit` for more data
- Check session directory for intermediate files to debug

**Report not generated:**
- Check permissions for output directory
- Verify session directory is writable
- Use `--verbose` to see detailed errors

## Requirements

- Python 3.11+
- Internet connection (for HN API)
- Anthropic API key (for LLM analysis)

## Architecture

The tool uses a modular pipeline:
- `fetcher/` - HN API client
- `analyzer/` - Topic analysis with LLM
- `term_explainer/` - Technical term extraction
- `visualizer/` - Mermaid diagram generation
- `report_generator/` - Markdown compilation

Each module is independently testable and can be regenerated/modified.
