# arXiv Summary Extractor

Extract key points and summaries from arXiv papers, focusing on insights relevant to software engineers working in AI.

## Purpose

When reading academic papers from arXiv, it's often time-consuming to extract the most relevant information for practical software engineering work. This tool:

- Fetches arXiv papers by URL
- Extracts title, authors, and abstract
- Generates a concise summary
- Identifies key points relevant to AI engineers
- Highlights practical implications and technical details
- Outputs structured JSON for easy integration

## Quick Start

### Basic Usage

```bash
# Extract summary from an arXiv paper
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --output summary.json
```

### Custom Focus Area

```bash
# Focus on specific area relevant to your work
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --output summary.json \
    --focus "distributed machine learning systems"
```

### With Verbose Logging

```bash
# Enable detailed logging
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --output summary.json \
    --verbose
```

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "summary": "Concise 2-3 paragraph summary...",
  "key_points_for_ai_engineers": [
    "Point 1: Specific finding relevant to AI engineering",
    "Point 2: Practical application or implication",
    "Point 3: Technical detail or methodology"
  ],
  "technical_details": [
    "Important algorithms or methods",
    "Key metrics or results"
  ],
  "practical_implications": [
    "Real-world applications",
    "Implementation considerations"
  ],
  "relevance_score": "8",
  "tags": ["machine-learning", "optimization", "systems"],
  "metadata": {
    "arxiv_url": "https://arxiv.org/abs/2401.12345",
    "focus_area": "software engineering and AI applications",
    "extracted_at": "2024-01-15T10:30:00",
    "session_dir": ".data/extract_arxiv_summary/sessions/20240115_103000_abc123"
  }
}
```

## Options

- `--url`: (Required) arXiv paper URL (e.g., https://arxiv.org/abs/2401.12345)
- `--output`: Output file path (default: `arxiv_summary.json`)
- `--focus`: Focus area for key points extraction (default: `software engineering and AI applications`)
- `--verbose`: Enable verbose logging

## Session Data

Runtime data is stored in `.data/extract_arxiv_summary/sessions/{timestamp}_{guid}/`:
- `raw_paper.txt`: Fetched paper content
- `summary.json`: Extracted summary (copy)
- Session logs and state

The `latest` symlink always points to the most recent session for easy access.

## Use Cases

### Research Paper Review
```bash
# Review latest transformer architecture paper
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --focus "transformer architectures and attention mechanisms"
```

### ML Systems Engineering
```bash
# Focus on systems and infrastructure aspects
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --focus "ML infrastructure and distributed training"
```

### Model Optimization
```bash
# Extract optimization techniques
python -m extract_arxiv_summary \
    --url https://arxiv.org/abs/2401.12345 \
    --focus "model compression and quantization"
```

## Troubleshooting

### "URL must be from arxiv.org"
- Ensure the URL contains `arxiv.org`
- Supported formats: `https://arxiv.org/abs/XXXX.XXXXX` or `https://arxiv.org/pdf/XXXX.XXXXX.pdf`

### "Failed to fetch paper content"
- Check internet connection
- Verify the arXiv ID is valid
- Try accessing the URL in a browser first

### "Failed to extract summary"
- The paper content may be too long or malformed
- Check `.data/extract_arxiv_summary/sessions/latest/` for raw paper content
- Try with `--verbose` to see detailed error messages

### Empty or incomplete output
- Some papers may have limited abstract information
- The focus area may be too narrow
- Try broadening the `--focus` parameter

## Tips

1. **Be specific with focus area**: Instead of "AI", use "reinforcement learning for robotics"
2. **Check session directory**: Raw paper content and logs are saved for debugging
3. **Use verbose mode**: Helps understand what's happening at each stage
4. **Batch processing**: Write a shell script to process multiple papers

## Related Tools

- `web_to_md`: Convert web pages to markdown (general purpose)
- `blog_writer`: Transform ideas into blog posts with style matching

## Requirements

- Python 3.11+
- amplifier toolkit
- Internet connection (for fetching arXiv papers)
