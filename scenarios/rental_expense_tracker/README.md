# Rental Expense Tracker

Track time and expenses for short-term rentals from PDF receipts and invoices.

## Purpose

This tool processes PDF receipts and invoices to extract, categorize, and report on expenses and time entries for short-term rental properties. It uses AI to intelligently parse unstructured receipt data and categorize expenses into predefined categories.

## Quick Start

```bash
# Process all PDFs in a directory
python -m rental_expense_tracker \
    --pdfs receipts/ \
    --format markdown

# Process specific PDF files
python -m rental_expense_tracker \
    --pdfs "receipt1.pdf,receipt2.pdf,receipt3.pdf" \
    --output expense_report.md

# Generate PDF report (requires additional dependencies)
python -m rental_expense_tracker \
    --pdfs receipts/ \
    --format pdf \
    --output report.pdf
```

## Features

- **PDF Text Extraction**: Automatically extracts text from PDF receipts and invoices
- **Expense Parsing**: Uses AI to identify expense amounts, dates, vendors, and descriptions
- **Time Tracking**: Extracts time/hours information from contractor invoices
- **Smart Categorization**: Categorizes expenses into predefined categories:
  - Cleaning
  - Maintenance
  - Utilities
  - Platform fees
  - Contractor payments
  - Supplies
  - Other
- **Summary Reports**: Generates detailed reports with totals by category
- **Multiple Formats**: Outputs in Markdown or PDF format

## Input Requirements

- **Format**: PDF files only
- **Content**: Receipts, invoices, or expense documents
- **Quantity**: One or more PDF files (supports batch processing)

## Output

The tool generates:

1. **Summary Section**: Total expenses by category, total hours tracked
2. **Detailed Expenses**: Line-by-line breakdown with dates, vendors, amounts
3. **Time Entries**: Hours worked, activities, and rates (if applicable)

Output formats:
- **Markdown** (`.md`): Human-readable text format
- **PDF** (`.pdf`): Print-ready document format

## Options

- `--pdfs`: Path to directory or comma-separated list of PDF files (required)
- `--output`: Output path for final report (optional, auto-generated if not provided)
- `--format`: Output format - `markdown` or `pdf` (default: `markdown`)
- `--verbose`: Enable detailed logging

## Examples

### Process a directory of receipts

```bash
python -m rental_expense_tracker \
    --pdfs ~/Documents/rental_receipts/ \
    --output monthly_report.md
```

### Process specific files with verbose output

```bash
python -m rental_expense_tracker \
    --pdfs "cleaning_receipt.pdf,hvac_invoice.pdf,supplies.pdf" \
    --format markdown \
    --verbose
```

## Session Data

The tool stores intermediate data in `.data/rental_expense_tracker/sessions/`:

- `extracted_text/`: Text extracted from each PDF
- `results.json`: Structured expense and time data
- `expense_report.md`: Final report (if not specified elsewhere)

Each run creates a new session directory with a timestamp and unique ID.

## Troubleshooting

### No expenses found

- Ensure PDFs contain text (not just images)
- Check that amounts and dates are clearly visible
- Try processing PDFs individually to identify problematic files

### Incorrect categorization

- The AI makes best-effort categorization based on vendor and description
- Review the confidence levels in the detailed output
- Common categories are learned from the description and vendor name

### PDF extraction fails

- Ensure PDFs are not password-protected
- Verify PDFs are not corrupted
- Some scanned PDFs may require OCR preprocessing

## Dependencies

- Python 3.11+
- amplifier (Claude Code SDK)
- click (CLI framework)
- pypdf (PDF text extraction)

## Development

To modify or extend this tool:

1. Review `HOW_TO_CREATE_YOUR_OWN.md` for architecture details
2. Modules are in subdirectories: `pdf_extractor/`, `expense_parser/`, etc.
3. Each module has `__init__.py` and `core.py`
4. Main orchestration is in `main.py`
