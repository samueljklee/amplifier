#!/usr/bin/env python3
"""
Code Complexity Analyzer - Main Orchestrator and CLI

Analyzes code complexity across multiple programming languages.
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

from .metrics_analyzer import MetricsAnalyzer
from .quality_analyzer import QualityAnalyzer
from .report_generator import ReportGenerator
from .scanner import CodeScanner

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="analyze_code_complexity", format=log_format)


class CodeComplexityPipeline:
    """Orchestrates the code complexity analysis pipeline."""

    def __init__(self, session_dir: Path):
        """Initialize pipeline with session directory.

        Args:
            session_dir: Session directory for state and outputs
        """
        self.session_dir = session_dir
        self.scanner = CodeScanner()
        self.metrics_analyzer = MetricsAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.report_generator = ReportGenerator()

        # Create session subdirectories
        self.results_dir = session_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        code_dir: Path,
        output_path: Path | None = None,
    ) -> bool:
        """Run the complete analysis pipeline.

        Args:
            code_dir: Directory containing code files to analyze
            output_path: Output path for final report

        Returns:
            True if successful, False otherwise
        """
        try:
            # Stage 1: Discover code files
            logger.stage_transition(None, "scan_files", estimated_duration=10)
            logger.info(f"📂 Scanning directory: {code_dir}")

            files = await self.scanner.discover_files(code_dir)
            if not files:
                logger.error("No code files found in directory")
                return False

            logger.info(f"✓ Found {len(files)} code files")

            # Save discovered files
            files_json = self.results_dir / "discovered_files.json"
            files_json.write_text(json.dumps([str(f) for f in files], indent=2))

            # Stage 2: Calculate metrics
            logger.stage_transition("scan_files", "calculate_metrics", estimated_duration=30)
            logger.info("📊 Calculating complexity metrics...")

            metrics_results = await self.metrics_analyzer.analyze_metrics(files)
            logger.info(f"✓ Analyzed metrics for {len(metrics_results)} files")

            # Save metrics
            metrics_json = self.results_dir / "metrics.json"
            metrics_json.write_text(json.dumps(metrics_results, indent=2))

            # Stage 3: Analyze code quality
            logger.stage_transition("calculate_metrics", "analyze_quality", estimated_duration=60)
            logger.info("🔍 Analyzing code quality and security...")

            quality_results = await self.quality_analyzer.analyze_quality(files)
            logger.info("✓ Completed quality analysis")

            # Save quality results
            quality_json = self.results_dir / "quality.json"
            quality_json.write_text(json.dumps(quality_results, indent=2))

            # Stage 4: Generate report
            logger.stage_transition("analyze_quality", "generate_report", estimated_duration=20)
            logger.info("📝 Generating markdown report...")

            report = await self.report_generator.generate_report(
                files=files,
                metrics_results=metrics_results,
                quality_results=quality_results,
            )

            # Determine output path
            if output_path is None:
                output_path = self.session_dir / "complexity_report.md"
            else:
                # Create parent directory for user-provided output paths (Web UI requirement)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save report
            output_path.write_text(report)
            logger.info(f"✅ Report saved to: {output_path}")

            # Emit events for Web UI
            logger.preview_available(
                preview_type="markdown",
                preview_data=str(output_path),
                file_count=len(files),
            )
            logger.file_created(
                str(output_path),
                metadata={
                    "type": "final_report",
                    "file_count": len(files),
                    "word_count": len(report.split()),
                },
            )

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False


# CLI Interface
@add_describe_flag(version="1.0", display_name="Code Complexity Analyzer")
@click.command()
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing code files to analyze",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for complexity report (default: session_dir/complexity_report.md)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    directory: Path,
    output: Path | None,
    verbose: bool,
):
    """Code Complexity Analyzer - Analyze code complexity and quality.

    This tool scans a directory of code files, calculates complexity metrics,
    identifies code quality issues, and generates a comprehensive markdown report.

    Supported languages: Python, JavaScript, TypeScript, Java, Go, Rust, C++, and more.

    Example:
        python -m scenarios.analyze_code_complexity \\
            --directory ./my_project \\
            --output complexity_report.md
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Create session directory
    base_dir = Path.cwd() / ".data" / "analyze_code_complexity" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid.uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create 'latest' symlink for easy access
    latest_link = base_dir / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir.name)

    logger.info("🚀 Starting Code Complexity Analyzer")
    logger.info(f"  Session: {session_dir}")
    logger.info(f"  Directory: {directory}")
    if output:
        logger.info(f"  Output: {output}")
    else:
        logger.info(f"  Output: {session_dir}/complexity_report.md")

    # Create and run pipeline
    pipeline = CodeComplexityPipeline(session_dir)

    success = asyncio.run(
        pipeline.run(
            code_dir=directory,
            output_path=output,
        )
    )

    if success:
        logger.info("\n✨ Code complexity analysis complete!")
        return 0
    logger.error("\n❌ Code complexity analysis failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
