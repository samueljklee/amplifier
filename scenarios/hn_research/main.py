#!/usr/bin/env python3
"""
HN Research - Main Orchestrator and CLI

Analyzes top Hacker News posts to identify trends and relationships.
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

from .analyzer import Analyzer
from .fetcher import Fetcher
from .report_generator import ReportGenerator
from .term_explainer import TermExplainer
from .visualizer import Visualizer

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="hn_research", format=log_format)


class HNResearchPipeline:
    """Orchestrates the HN research pipeline."""

    def __init__(self, session_dir: Path):
        """Initialize pipeline.

        Args:
            session_dir: Directory for session data
        """
        self.session_dir = session_dir
        self.fetcher = Fetcher()
        self.analyzer = Analyzer()
        self.term_explainer = TermExplainer()
        self.visualizer = Visualizer()
        self.report_generator = ReportGenerator()

    async def run(self, output_path: Path | None = None, post_limit: int = 20) -> bool:
        """Run the complete pipeline.

        Args:
            output_path: Output path for final report
            post_limit: Number of top posts to fetch

        Returns:
            True if successful, False otherwise
        """
        try:
            # Stage 1: Fetch HN data
            logger.stage_transition(None, "fetch_data", estimated_duration=30)
            logger.info(f"📡 Fetching top {post_limit} Hacker News posts...")
            posts = await self.fetcher.fetch_top_posts(post_limit)

            if not posts:
                logger.error("No posts fetched")
                return False

            logger.info(f"✓ Fetched {len(posts)} posts")

            # Save raw data
            raw_data_file = self.session_dir / "raw_posts.json"
            raw_data_file.write_text(json.dumps(posts, indent=2))
            logger.file_created(str(raw_data_file), metadata={"type": "raw_data", "post_count": len(posts)})

            # Stage 2: Analyze posts
            logger.stage_transition("fetch_data", "analyze_posts", estimated_duration=60)
            logger.info("🔍 Analyzing posts for trends and relationships...")
            analysis = await self.analyzer.analyze_posts(posts)

            if not isinstance(analysis, dict):
                logger.error("Invalid analysis result")
                return False

            logger.info(f"✓ Identified {len(analysis.get('categories', {}))} topic categories")

            # Save analysis
            analysis_file = self.session_dir / "analysis.json"
            analysis_file.write_text(json.dumps(analysis, indent=2))
            logger.file_created(str(analysis_file), metadata={"type": "analysis"})

            # Stage 3: Extract and explain terms
            logger.stage_transition("analyze_posts", "explain_terms", estimated_duration=45)
            logger.info("📚 Extracting and explaining technical terms...")
            terms = await self.term_explainer.explain_terms(posts, analysis)

            if not isinstance(terms, dict):
                logger.error("Invalid terms result")
                return False

            logger.info(f"✓ Explained {len(terms.get('terms', []))} terms")

            # Stage 4: Generate visualization
            logger.stage_transition("explain_terms", "generate_visualization", estimated_duration=30)
            logger.info("📊 Generating topic relationship diagram...")
            diagram = await self.visualizer.generate_diagram(analysis)
            logger.info("✓ Diagram generated")

            # Stage 5: Compile report
            logger.stage_transition("generate_visualization", "generate_report", estimated_duration=20)
            logger.info("📝 Compiling final report...")
            report = await self.report_generator.generate_report(posts, analysis, terms, diagram)

            # Save report
            if output_path is None:
                date_str = datetime.now().strftime("%Y%m%d")
                output_path = self.session_dir / f"hn_research_{date_str}.md"
            else:
                # Web UI path - ensure parent exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(report)
            logger.info(f"✅ Report saved to: {output_path}")

            # Emit events for web UI
            logger.preview_available(preview_type="markdown", preview_data=str(output_path), post_count=len(posts))
            logger.file_created(str(output_path), metadata={"type": "final", "post_count": len(posts)})

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False


@add_describe_flag(version="1.0", display_name="HN Research")
@click.command()
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for final report (default: hn_research_YYYYMMDD.md in session dir)",
)
@click.option("--post-limit", type=int, default=20, help="Number of top posts to analyze (default: 20)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(output: Path | None, post_limit: int, verbose: bool):
    """HN Research - Analyze top Hacker News posts for trends and relationships.

    This tool automatically fetches top HN posts, analyzes their content and comments,
    identifies topic relationships, explains technical terms, and generates a comprehensive
    markdown report with visualizations.

    Example:
        python -m scenarios.hn_research --post-limit 20
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Create session directory
    base_dir = Path.cwd() / ".data" / "hn_research" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid.uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create 'latest' symlink
    latest_link = base_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(session_dir.name)

    # Create and run pipeline
    pipeline = HNResearchPipeline(session_dir)

    logger.info("🚀 Starting HN Research Pipeline")
    logger.info(f"  Session: {session_dir}")
    logger.info(f"  Post limit: {post_limit}")
    if output:
        logger.info(f"  Output: {output}")
    else:
        logger.info("  Output: Auto-generated in session directory")

    success = asyncio.run(pipeline.run(output_path=output, post_limit=post_limit))

    if success:
        logger.info("\n✨ HN research complete!")
        return 0
    logger.error("\n❌ HN research failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
