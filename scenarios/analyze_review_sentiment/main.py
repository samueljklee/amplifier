#!/usr/bin/env python3
"""
Analyze Review Sentiment - Main Orchestrator and CLI

Coordinates the review analysis pipeline.
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

from .analyzer import SentimentAnalyzer
from .extractor import PDFExtractor
from .formatter import ReportFormatter

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="analyze_review_sentiment", format=log_format)


class ReviewAnalysisPipeline:
    """Orchestrates the review analysis pipeline."""

    def __init__(self, session_dir: Path):
        """Initialize pipeline with session directory.

        Args:
            session_dir: Directory for session data
        """
        self.session_dir = session_dir
        self.extractor = PDFExtractor()
        self.analyzer = SentimentAnalyzer()
        self.formatter = ReportFormatter()

    async def run(self, pdf_path: Path, output_path: Path | None = None) -> bool:
        """Run the complete analysis pipeline.

        Args:
            pdf_path: Path to PDF file with reviews
            output_path: Output path for markdown report

        Returns:
            True if successful, False otherwise
        """
        try:
            # Stage 1: Extract text from PDF
            logger.stage_transition(None, "extract_text", estimated_duration=10)
            logger.info(f"📄 Extracting text from PDF: {pdf_path.name}")

            review_text = await self.extractor.extract_text(pdf_path)

            if not review_text or len(review_text.strip()) < 50:
                logger.error("Extracted text is too short or empty")
                return False

            # Save extracted text to session
            extracted_file = self.session_dir / "extracted_text.txt"
            extracted_file.write_text(review_text)
            logger.info(f"✓ Extracted {len(review_text)} characters")
            logger.file_created(
                str(extracted_file),
                metadata={"type": "extracted_text", "length": len(review_text)},
            )

            # Stage 2: Analyze sentiment and actionability
            logger.stage_transition("extract_text", "analyze_sentiment", estimated_duration=30)
            logger.info("🔍 Analyzing sentiment and scoring actionability...")

            analysis = await self.analyzer.analyze(review_text)

            if not analysis:
                logger.error("Analysis failed to produce results")
                return False

            # Save analysis to session
            analysis_file = self.session_dir / "analysis.json"
            analysis_file.write_text(json.dumps(analysis, indent=2))
            logger.info(
                f"✓ Analysis complete: {analysis.get('overall_sentiment', 'unknown')} sentiment, "
                f"{len(analysis.get('top_actionable_reviews', []))} actionable reviews identified"
            )
            logger.file_created(
                str(analysis_file),
                metadata={
                    "type": "analysis",
                    "sentiment": analysis.get("overall_sentiment"),
                    "review_count": len(analysis.get("top_actionable_reviews", [])),
                },
            )

            # Stage 3: Format markdown report
            logger.stage_transition("analyze_sentiment", "generate_report", estimated_duration=5)
            logger.info("📝 Generating markdown report...")

            report_content = self.formatter.format_report(analysis)

            # Determine output path
            if output_path is None:
                output_path = self.session_dir / "sentiment_report.md"
            else:
                # CRITICAL: Create parent directory for Web UI paths
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save report
            output_path.write_text(report_content)
            logger.info(f"✅ Report saved to: {output_path}")

            # Emit events for web UI
            logger.preview_available(
                preview_type="markdown",
                preview_data=str(output_path),
                word_count=len(report_content.split()),
            )
            logger.file_created(
                str(output_path),
                metadata={"type": "final_report", "word_count": len(report_content.split())},
            )

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False


# CLI Interface
@add_describe_flag(version="1.0.0", display_name="Analyze Review Sentiment")
@click.command()
@click.option(
    "--pdf",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to PDF file containing customer reviews",
)
@click.option(
    "--output",
    type=str,
    default=None,
    help="Output path for markdown report (default: session_dir/sentiment_report.md)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(pdf: Path, output: str | None, verbose: bool):
    """Analyze customer reviews and identify actionable feedback.

    This tool extracts text from a PDF containing customer reviews,
    analyzes overall sentiment, scores each review for actionability,
    and generates a markdown report highlighting the top 3 most actionable reviews.

    Example:
        python -m analyze_review_sentiment --pdf reviews.pdf
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Create session directory in .data/
    base_dir = Path.cwd() / ".data" / "analyze_review_sentiment" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid.uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create 'latest' symlink for easy access
    latest_link = base_dir / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir.name)

    logger.info("🚀 Starting Review Sentiment Analysis")
    logger.info(f"  Session: {session_dir}")
    logger.info(f"  PDF: {pdf.name}")
    if output:
        logger.info(f"  Output: {output}")
    else:
        logger.info(f"  Output: {session_dir / 'sentiment_report.md'}")

    # Convert output string to Path if provided
    output_path = Path(output) if output else None

    # Create and run pipeline
    pipeline = ReviewAnalysisPipeline(session_dir)
    success = asyncio.run(pipeline.run(pdf, output_path))

    if success:
        logger.info("\n✨ Analysis complete!")
        return 0
    logger.error("\n❌ Analysis failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
