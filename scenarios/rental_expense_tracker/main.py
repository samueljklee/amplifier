#!/usr/bin/env python3
"""
Rental Expense Tracker - Main Orchestrator and CLI

Extracts and categorizes expenses and time from PDF receipts.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .categorizer import Categorizer
from .expense_parser import ExpenseParser
from .pdf_extractor import PDFExtractor
from .report_generator import ReportGenerator
from .time_parser import TimeParser

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="rental_expense_tracker", format=log_format)


class ExpenseTrackerPipeline:
    """Orchestrates the expense tracking pipeline."""

    def __init__(self, session_dir: Path):
        """Initialize pipeline with session directory.

        Args:
            session_dir: Session directory for storing state
        """
        self.session_dir = session_dir
        self.pdf_extractor = PDFExtractor()
        self.expense_parser = ExpenseParser()
        self.time_parser = TimeParser()
        self.categorizer = Categorizer()
        self.report_generator = ReportGenerator()

        # Create session directories
        self.session_dir.mkdir(parents=True, exist_ok=True)
        (self.session_dir / "extracted_text").mkdir(exist_ok=True)

    async def run(
        self,
        pdf_paths: list[Path],
        output_path: Path | None = None,
        output_format: str = "markdown",
    ) -> bool:
        """Run the complete pipeline.

        Args:
            pdf_paths: List of PDF file paths to process
            output_path: Output path for final report
            output_format: Output format (markdown or pdf)

        Returns:
            True if successful, False otherwise
        """
        logger.stage_transition(None, "extract_pdfs", estimated_duration=30)
        logger.info(f"📄 Extracting text from {len(pdf_paths)} PDF files...")

        # Extract text from all PDFs
        extracted_texts = []
        for pdf_path in pdf_paths:
            try:
                text = await self.pdf_extractor.extract_text(pdf_path)
                if text:
                    extracted_texts.append({"path": pdf_path, "text": text})
                    # Save extracted text to session
                    text_file = self.session_dir / "extracted_text" / f"{pdf_path.stem}.txt"
                    text_file.write_text(text)
                    logger.info(f"  ✓ Extracted: {pdf_path.name}")
                else:
                    logger.warning(f"  ⚠ No text found: {pdf_path.name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to extract {pdf_path.name}: {e}")

        if not extracted_texts:
            logger.error("No text could be extracted from PDFs")
            return False

        logger.info(f"✓ Extracted text from {len(extracted_texts)} PDFs")

        # Parse expenses
        logger.stage_transition("extract_pdfs", "parse_expenses", estimated_duration=60)
        logger.info("💰 Parsing expense information...")

        all_expenses = []
        for item in extracted_texts:
            try:
                expenses = await self.expense_parser.parse_expenses(item["text"], item["path"].name)
                all_expenses.extend(expenses)
                logger.info(f"  ✓ Found {len(expenses)} expenses in {item['path'].name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to parse expenses from {item['path'].name}: {e}")

        logger.info(f"✓ Parsed {len(all_expenses)} total expenses")

        # Parse time entries
        logger.stage_transition("parse_expenses", "parse_time", estimated_duration=30)
        logger.info("⏱️  Parsing time information...")

        all_time_entries = []
        for item in extracted_texts:
            try:
                time_entries = await self.time_parser.parse_time_entries(item["text"], item["path"].name)
                all_time_entries.extend(time_entries)
                if time_entries:
                    logger.info(f"  ✓ Found {len(time_entries)} time entries in {item['path'].name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to parse time from {item['path'].name}: {e}")

        logger.info(f"✓ Parsed {len(all_time_entries)} total time entries")

        # Categorize expenses
        logger.stage_transition("parse_time", "categorize", estimated_duration=30)
        logger.info("🏷️  Categorizing expenses...")

        categorized_expenses = await self.categorizer.categorize_expenses(all_expenses)
        logger.info(f"✓ Categorized {len(categorized_expenses)} expenses")

        # Save intermediate results
        results = {
            "expenses": categorized_expenses,
            "time_entries": all_time_entries,
            "pdf_count": len(pdf_paths),
            "processed_date": datetime.now().isoformat(),
        }

        results_file = self.session_dir / "results.json"
        results_file.write_text(json.dumps(results, indent=2))
        logger.info(f"💾 Saved results to {results_file}")

        # Generate report
        logger.stage_transition("categorize", "generate_report", estimated_duration=20)
        logger.info("📊 Generating report...")

        # Determine output path
        if output_path is None:
            output_path = self.session_dir / f"expense_report.{output_format}"
        else:
            output_path = Path(output_path)
            # CRITICAL: Create parent directory for Web UI
            output_path.parent.mkdir(parents=True, exist_ok=True)

        report_path = await self.report_generator.generate_report(
            expenses=categorized_expenses,
            time_entries=all_time_entries,
            output_path=output_path,
            output_format=output_format,
        )

        if report_path:
            logger.info(f"✅ Report generated: {report_path}")
            logger.file_created(
                str(report_path),
                metadata={
                    "type": "report",
                    "format": output_format,
                    "expense_count": len(categorized_expenses),
                    "time_entry_count": len(all_time_entries),
                },
            )

            # Emit preview for web UI
            if output_format == "markdown":
                logger.preview_available(
                    preview_type="markdown",
                    preview_data=str(report_path),
                    expense_count=len(categorized_expenses),
                    time_entry_count=len(all_time_entries),
                )

            return True
        logger.error("Failed to generate report")
        return False


# CLI Interface
@add_describe_flag(version="1.0", display_name="Rental Expense Tracker")
@click.command()
@click.option(
    "--pdfs",
    type=str,
    required=True,
    help="Path to directory containing PDF receipts or comma-separated PDF file paths",
)
@click.option(
    "--output",
    type=str,
    default=None,
    help="Output path for final report (default: auto-generated in session dir)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "pdf"]),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    pdfs: str,
    output: str | None,
    output_format: str,
    verbose: bool,
):
    """Rental Expense Tracker - Extract and categorize expenses from PDF receipts.

    This tool processes PDF receipts and invoices to extract expense and time
    information, categorizes them, and generates summary reports.

    Example:
        python -m rental_expense_tracker \\
            --pdfs receipts/ \\
            --format markdown
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Create session directory in .data/
    base_dir = Path.cwd() / ".data" / "rental_expense_tracker" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid.uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create 'latest' symlink
    latest_link = base_dir / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir.name)

    logger.info("🚀 Starting Rental Expense Tracker")
    logger.info(f"  Session: {session_dir}")

    # Parse PDF paths
    pdf_paths: list[Path] = []
    pdfs_path = Path(pdfs)

    if pdfs_path.is_dir():
        # Find all PDFs in directory (recursive)
        pdf_paths = list(pdfs_path.glob("**/*.pdf"))
        logger.info(f"  Found {len(pdf_paths)} PDF files in directory")
    elif pdfs_path.is_file() and pdfs_path.suffix.lower() == ".pdf":
        pdf_paths = [pdfs_path]
        logger.info(f"  Processing single PDF: {pdfs_path.name}")
    else:
        # Try parsing as comma-separated list
        for path_str in pdfs.split(","):
            path = Path(path_str.strip())
            if path.is_file() and path.suffix.lower() == ".pdf":
                pdf_paths.append(path)

        if pdf_paths:
            logger.info(f"  Processing {len(pdf_paths)} PDF files from list")

    # Validate minimum inputs
    if not pdf_paths:
        logger.error("❌ No valid PDF files found")
        logger.error(f"   Searched in: {pdfs}")
        return 1

    if len(pdf_paths) < 1:
        logger.error("❌ At least 1 PDF file is required")
        return 1

    logger.info(f"  Output format: {output_format}")
    if output:
        logger.info(f"  Output path: {output}")
    else:
        logger.info("  Output: Auto-generated in session directory")

    # Create and run pipeline
    pipeline = ExpenseTrackerPipeline(session_dir)

    output_path = Path(output) if output else None

    success = asyncio.run(
        pipeline.run(
            pdf_paths=pdf_paths,
            output_path=output_path,
            output_format=output_format,
        )
    )

    if success:
        logger.info("\n✨ Expense tracking complete!")
        logger.info(f"📊 Session directory: {session_dir}")
        return 0
    logger.error("\n❌ Expense tracking failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
