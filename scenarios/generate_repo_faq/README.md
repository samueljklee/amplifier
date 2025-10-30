# Generate Repository FAQ

**Transform any codebase into comprehensive FAQ documentation automatically.**

This tool analyzes a project repository and generates a well-structured FAQ markdown file that explains what the project does, its features, setup instructions, architecture, and how it works.

## 🎯 Purpose

Automatically create comprehensive FAQ documentation by analyzing:
- Source code files
- Existing documentation (README, docs, etc.)
- Project structure and organization
- Technology stack and patterns

Perfect for:
- Onboarding new team members
- Creating documentation for existing projects
- Understanding unfamiliar codebases
- Generating user-facing FAQs

## 🚀 Quick Start

### Installation

```bash
cd scenarios/generate_repo_faq
uv sync
```

### Basic Usage

```bash
# Analyze a repository and generate FAQ
python -m generate_repo_faq \
    --repo-path /path/to/project \
    --output FAQ.md
```

### CLI Options

- `--repo-path`: **(required)** Path to the repository directory to analyze
- `--output`: Output path for FAQ markdown file (default: session_dir/FAQ.md)
- `--verbose`: Enable verbose logging

## 📋 How It Works

1. **Extract Files** - Recursively discovers source code and documentation files
2. **Analyze Content** - Uses AI to understand the project's purpose, features, and architecture
3. **Generate FAQ** - Creates comprehensive FAQ covering common questions
4. **Save Output** - Writes formatted markdown to specified location

### Auto-Excluded Directories

The tool automatically excludes common build artifacts and dependencies:
- `.venv`, `node_modules`, `__pycache__`
- `build/`, `dist/`, `.git/`
- Binary files and generated code

## 📖 Examples

### Example 1: Generate FAQ for Current Project

```bash
python -m generate_repo_faq \
    --repo-path . \
    --output PROJECT_FAQ.md
```

### Example 2: Analyze External Repository

```bash
python -m generate_repo_faq \
    --repo-path ~/projects/awesome-tool \
    --output ~/Desktop/awesome-tool-faq.md \
    --verbose
```

## 🎨 Output Format

The generated FAQ includes sections covering:

- **What is this project?** - Purpose and problem it solves
- **Key Features** - Main capabilities and functionality
- **Installation & Setup** - How to get started
- **Usage** - How to use the project
- **Architecture** - Code organization and structure
- **Technology Stack** - Languages, frameworks, tools
- **Contributing** - How to contribute (if applicable)
- **Common Issues** - Troubleshooting tips

## 🔧 Troubleshooting

### "No files found in repository"

**Cause**: Repository is empty or all files are excluded by auto-ignore patterns.

**Solution**: Verify the repository path contains source code or documentation files.

### "Analysis failed"

**Cause**: LLM service unavailable or insufficient content to analyze.

**Solution**:
- Check your internet connection
- Ensure repository has readable source/doc files
- Try again with `--verbose` to see detailed logs

### FAQ is too generic

**Cause**: Repository has minimal documentation or comments.

**Solution**:
- Add comments to your code
- Include a basic README
- Run the tool again after adding more context

## 📂 Session Data

Runtime data is stored in `.data/generate_repo_faq/sessions/`:

```
.data/generate_repo_faq/sessions/{timestamp}_{guid}/
├── extracted_data.txt    # Summary of extracted files
└── FAQ.md               # Generated FAQ (if no output path specified)
```

Use the `latest` symlink to access the most recent session:

```bash
cat .data/generate_repo_faq/sessions/latest/FAQ.md
```

## 🤝 Contributing

This tool follows the amplifier modular architecture pattern. See `HOW_TO_CREATE_YOUR_OWN.md` for implementation details.

## 📝 License

Part of the amplifier toolkit.
