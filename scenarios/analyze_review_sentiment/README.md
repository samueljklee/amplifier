# Analyze Review Sentiment

Transform customer reviews into actionable insights by analyzing sentiment and identifying the most valuable feedback.

## Purpose

This tool helps businesses extract maximum value from customer reviews by:
- Analyzing overall sentiment across all reviews
- Scoring each review for actionability (specificity, impact, feasibility, clarity)
- Identifying the top 3 most actionable reviews that could drive improvements
- Generating a markdown report with concrete suggested actions

## Quick Start

### Installation

```bash
cd /path/to/amplifier/scenarios/analyze_review_sentiment
uv sync
```

### Basic Usage

```bash
# Analyze reviews from a PDF
python -m analyze_review_sentiment --pdf customer_reviews.pdf

# Specify custom output location
python -m analyze_review_sentiment \
    --pdf reviews.pdf \
    --output /path/to/report.md

# Enable verbose logging
python -m analyze_review_sentiment --pdf reviews.pdf --verbose
```

## Input Requirements

**PDF Format:**
- Single PDF file containing customer reviews
- Can be free-form text or structured format
- Multiple reviews per file supported
- Text must be extractable (not image-only PDFs)

**Review Content:**
- Any customer feedback: reviews, surveys, support tickets, etc.
- Works with positive, negative, or mixed feedback
- Best results with specific, detailed reviews

## Output

### Markdown Report

The tool generates a comprehensive markdown report including:

1. **Overall Sentiment Analysis**
   - Sentiment classification (positive/negative/mixed/neutral)
   - Summary explanation
   - Total number of reviews analyzed

2. **Top 3 Actionable Reviews**
   - Ranked by actionability score (0-100)
   - Full review text or relevant excerpt
   - Explanation of why it's actionable
   - Concrete suggested action for the business

3. **Next Steps**
   - Guidance on how to act on the feedback

### Example Output Structure

```markdown
# Customer Review Sentiment Analysis

## Overall Sentiment
**Sentiment:** Mixed
**Total Reviews Analyzed:** 15
**Summary:** Reviews show appreciation for core features but consistent
concerns about mobile app performance and customer support responsiveness.

## Top 3 Most Actionable Reviews

### Rank #1 - Actionability Score: 92/100
**Review:**
> The desktop app works great, but the mobile version crashes whenever I try
> to upload photos larger than 5MB. This happens on both iOS and Android.

**Why This is Actionable:** Specific technical issue with clear reproduction
steps, affecting core functionality on multiple platforms.

**Suggested Action:** Prioritize mobile app bug fix for large file uploads.
Add file size validation with helpful error messages.
```

## How It Works

The tool uses a 3-stage pipeline:

1. **Extract** - Uses pypdf to extract text from PDF files
2. **Analyze** - Uses Claude AI to:
   - Assess overall sentiment
   - Score each review for actionability
   - Identify top actionable items
3. **Format** - Generates a clean markdown report

## Session Data

All processing data is saved to `.data/analyze_review_sentiment/sessions/{timestamp}_{guid}/`:
- `extracted_text.txt` - Raw text extracted from PDF
- `analysis.json` - Full analysis results
- `sentiment_report.md` - Final markdown report (default location)

Access the latest session via the `latest` symlink:
```bash
cat .data/analyze_review_sentiment/sessions/latest/sentiment_report.md
```

## Troubleshooting

### "No text could be extracted from PDF"
- Ensure PDF contains actual text (not just images)
- Try opening the PDF and copying text to verify it's extractable
- Consider using OCR if PDF is image-based

### "Extracted text is too short or empty"
- Verify PDF file is not corrupted
- Check that PDF actually contains reviews
- Some PDFs may have encoding issues - try re-exporting

### "Analysis failed to produce results"
- Check that extracted text contains actual review content
- Ensure API access to Claude is working
- Try with a smaller or simpler PDF first

### Import Errors
```bash
# Reinstall dependencies
cd scenarios/analyze_review_sentiment
uv sync
```

## Web UI Integration

When launched from the Amplifier Web UI, this tool:
- Automatically receives PDF path from file picker
- Shows progress through each pipeline stage
- Provides live preview of generated report
- Saves output to web-accessible temporary directory

## Tips for Best Results

1. **Review Quality**: More detailed reviews lead to better actionability scoring
2. **PDF Format**: Plain text PDFs work best; avoid image-only documents
3. **Volume**: Tool works with any number of reviews (tested with 1-100+)
4. **Review Types**: Works with any feedback: app reviews, surveys, support tickets, etc.
5. **Follow Up**: Use the suggested actions as starting points for team discussions

## Examples

### E-commerce Reviews
```bash
python -m analyze_review_sentiment --pdf ecommerce_feedback.pdf
```

### SaaS Product Feedback
```bash
python -m analyze_review_sentiment --pdf user_surveys_q4.pdf --output reports/q4_analysis.md
```

### Restaurant Reviews
```bash
python -m analyze_review_sentiment --pdf restaurant_reviews_jan.pdf --verbose
```

## Technical Details

- **PDF Processing**: pypdf library for text extraction
- **AI Analysis**: Claude AI via amplifier CCSDK toolkit
- **Defensive Parsing**: Type-guarded JSON parsing from LLM responses
- **Session Management**: Persistent session directories for resume capability
- **Web UI Compatible**: Full integration with Amplifier Web UI v2

## Contributing

This tool was generated by the Amplifier Tool Generator. To create similar tools:
1. See `HOW_TO_CREATE_YOUR_OWN.md` for patterns and examples
2. Study the modular structure: extractor/, analyzer/, formatter/
3. Follow the "bricks and studs" philosophy for maintainable code
