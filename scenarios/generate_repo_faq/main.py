#!/usr/bin/env python3
"""
Generate Repository FAQ - Main Orchestrator and CLI

Analyzes a project repository and generates comprehensive FAQ documentation.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .analyzer import RepositoryAnalyzer
from .extractor import RepositoryExtractor
from .formatter import FAQFormatter

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="generate_repo_faq", format=log_format)


class FAQGenerationPipeline:
    """Orchestrates the FAQ generation pipeline."""

    def __init__(self, session_dir: Path):
        """Initialize pipeline with session directory.

        Args:
            session_dir: Directory for storing session data
        """
        self.session_dir = session_dir
        self.extractor = RepositoryExtractor()
        self.analyzer = RepositoryAnalyzer()
        self.formatter = FAQFormatter()

    async def run(
        self,
        repo_path: Path,
        output_path: Path,
    ) -> bool:
        """Run the complete FAQ generation pipeline.

        Args:
            repo_path: Path to repository directory
            output_path: Output path for FAQ markdown file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Stage 1: Extract repository files
            logger.stage_transition(None, "extract_files", estimated_duration=10)
            logger.info("📂 Extracting repository files...")

            extracted_data = await self.extractor.extract_repository(repo_path, self.session_dir)

            if not extracted_data["source_files"] and not extracted_data["doc_files"]:
                logger.error("❌ No relevant files found in repository")
                return False

            logger.info(
                f"✓ Extracted {len(extracted_data['source_files'])} source files, "
                f"{len(extracted_data['doc_files'])} documentation files"
            )

            # Stage 2: Analyze repository content
            logger.stage_transition("extract_files", "analyze_content", estimated_duration=60)
            logger.info("🔍 Analyzing repository content...")

            analysis = await self.analyzer.analyze_repository(extracted_data)

            if not analysis:
                logger.error("❌ Analysis failed")
                return False

            logger.info("✓ Repository analysis complete")

            # Stage 3: Generate FAQ
            logger.stage_transition("analyze_content", "generate_faq", estimated_duration=90)
            logger.info("📝 Generating FAQ content...")

            faq_content = await self.formatter.format_faq(analysis, extracted_data)

            if not faq_content:
                logger.error("❌ FAQ generation failed")
                return False

            logger.info("✓ FAQ content generated")

            # Stage 4: Save output
            logger.stage_transition("generate_faq", "save_output", estimated_duration=1)
            logger.info("💾 Saving FAQ to file...")

            # Create parent directory if needed (critical for Web UI)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(faq_content)

            logger.info(f"✅ FAQ saved to: {output_path}")
            logger.file_created(
                str(output_path),
                metadata={
                    "type": "faq",
                    "word_count": len(faq_content.split()),
                    "source_file_count": len(extracted_data["source_files"]),
                    "doc_file_count": len(extracted_data["doc_files"]),
                },
            )

            return True

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return False


# CLI Interface
@add_describe_flag(version="1.0", display_name="Generate Repository FAQ")
@click.command()
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Path to the repository directory to analyze",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for FAQ markdown file (default: session_dir/FAQ.md)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    repo_path: Path,
    output: Path | None,
    verbose: bool,
):
    """Generate Repository FAQ - Analyze a repository and create comprehensive FAQ documentation.

    This tool analyzes source code, documentation, and project structure to automatically
    generate a comprehensive FAQ markdown file explaining what the project does, its features,
    setup instructions, architecture, and how it works.

    Example:
        python -m generate_repo_faq \\
            --repo-path /path/to/project \\
            --output FAQ.md
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Create session directory
    base_dir = Path.cwd() / ".data" / "generate_repo_faq" / "sessions"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guid = uuid4().hex[:8]
    session_dir = base_dir / f"{timestamp}_{guid}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create 'latest' symlink for easy access
    latest_link = base_dir / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir.name)

    # Determine output path
    if output is None:
        output_path = session_dir / "FAQ.md"
    else:
        output_path = output

    # Create pipeline and run
    pipeline = FAQGenerationPipeline(session_dir)

    logger.info("🚀 Starting FAQ Generation Pipeline")
    logger.info(f"  Session: {session_dir}")
    logger.info(f"  Repository: {repo_path}")
    logger.info(f"  Output: {output_path}")

    success = asyncio.run(
        pipeline.run(
            repo_path=repo_path,
            output_path=output_path,
        )
    )

    if success:
        logger.info("\n✨ FAQ generation complete!")
        logger.info(f"📄 FAQ saved to: {output_path}")
        return 0

    logger.error("\n❌ FAQ generation failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
