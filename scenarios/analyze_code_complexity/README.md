# Code Complexity Analyzer

Analyze code complexity across multiple programming languages and generate comprehensive reports with metrics, quality issues, and recommendations.

## Purpose

This tool helps you understand and improve code quality by:
- Calculating complexity metrics (cyclomatic complexity, LOC, nesting depth)
- Identifying code smells and quality issues
- Detecting potential security vulnerabilities
- Analyzing maintainability and technical debt
- Generating actionable recommendations

## Supported Languages

Python, JavaScript, TypeScript, Java, Go, Rust, C++, C, C#, Ruby, PHP, Swift, Kotlin, Scala, Objective-C, R, Julia, Shell

## Quick Start

### Basic Usage

```bash
python -m scenarios.analyze_code_complexity \
    --directory ./my_project \
    --output complexity_report.md
```

### Installation

```bash
cd scenarios/analyze_code_complexity
uv sync
```

## What Gets Analyzed

### Complexity Metrics
- **Cyclomatic Complexity** - Number of independent paths through code
- **Lines of Code** - Total, code, comment, and blank lines
- **Function Length** - Maximum and average function/method length
- **Nesting Depth** - Maximum level of nested blocks
- **Maintainability Index** - 0-100 score (higher is better)

### Code Quality Issues
- **Code Smells** - Long methods, large classes, duplicated code
- **Security Issues** - SQL injection, XSS, hardcoded secrets
- **Best Practices** - Naming conventions, error handling
- **Technical Debt** - Areas needing refactoring

## Output

The tool generates a comprehensive markdown report with:
- Executive summary with key metrics
- Files ranked by complexity
- Quality issues by severity (critical, high, medium, low)
- Detailed findings per file
- Actionable recommendations

## Examples

### Analyze a Python project
```bash
python -m scenarios.analyze_code_complexity \
    --directory ./my_python_app \
    --output reports/complexity.md
```

### Analyze with verbose logging
```bash
python -m scenarios.analyze_code_complexity \
    --directory ./src \
    --verbose
```

## How It Works

1. **Discovery** - Recursively scans directory for code files
2. **Identification** - Determines programming language for each file
3. **Metrics Analysis** - Calculates complexity metrics using LLM
4. **Quality Analysis** - Identifies issues and security vulnerabilities
5. **Report Generation** - Creates comprehensive markdown report

## Session Management

Analysis results are saved in `.data/analyze_code_complexity/sessions/`:
- `discovered_files.json` - List of files found
- `metrics.json` - Complexity metrics for all files
- `quality.json` - Quality analysis results
- `complexity_report.md` - Final report

The `latest` symlink always points to the most recent session.

## Options

- `--directory` - Directory containing code files (required)
- `--output` - Output path for report (default: session_dir/complexity_report.md)
- `--verbose` - Enable detailed logging

## Troubleshooting

### No files found
- Ensure the directory contains supported file types
- Check file permissions

### Analysis taking too long
- Large files (>1MB) are automatically skipped
- Files are analyzed in batches with progress updates

### LLM parsing errors
- Very complex files may occasionally fail analysis
- Check logs for specific error messages
- Failed files are skipped, analysis continues

## Integration

### Web UI
The tool integrates with the Amplifier Web UI for:
- Visual workflow diagram
- Real-time progress updates
- Interactive report preview

### CLI
Can be used standalone or integrated into CI/CD pipelines:
```bash
python -m scenarios.analyze_code_complexity --directory ./src --output reports/complexity.md
```

## Tips

1. **Start small** - Analyze a single module first to understand the metrics
2. **Focus on critical issues** - Prioritize security and critical code smells
3. **Track over time** - Run regularly to monitor complexity trends
4. **Use in reviews** - Identify problematic areas before merging

## Related Tools

- `blog_writer` - Transform ideas into polished blog posts
- `transcribe` - Transcribe and analyze audio/video content
- `web_to_md` - Convert web pages to markdown

## Learn More

See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) to understand the implementation and create your own analysis tools.
