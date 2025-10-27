#!/usr/bin/env python3
"""
arXiv Summary Extractor - Main CLI

Extracts key points and summaries from arXiv papers for AI engineers.
"""

import asyncio
import os
import sys
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .core import extract_arxiv_summary

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="extract_arxiv_summary", format=log_format)


@add_describe_flag(version="0.1.0", display_name="arXiv Summary Extractor")
@click.command()
@click.option(
    "--url",
    type=str,
    required=True,
    help="arXiv paper URL (e.g., https://arxiv.org/abs/2401.12345)",
)
@click.option(
    "--output",
    type=str,
    default="arxiv_summary.json",
    help="Output file path for the summary (default: arxiv_summary.json)",
)
@click.option(
    "--focus",
    type=str,
    default="software engineering and AI applications",
    help="Focus area for key points (default: 'software engineering and AI applications')",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(url: str, output: str, focus: str, verbose: bool):
    """Extract key points and summaries from arXiv papers for AI engineers.

    This tool fetches arXiv papers, extracts the key findings, and highlights
    points relevant to software engineers working in the AI space.

    Example:
        python -m extract_arxiv_summary \\
            --url https://arxiv.org/abs/2401.12345 \\
            --output summary.json \\
            --focus "machine learning infrastructure"
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Validate arXiv URL
    if "arxiv.org" not in url.lower():
        logger.error("URL must be from arxiv.org")
        sys.exit(1)

    logger.info("🚀 Starting arXiv Summary Extractor")
    logger.info(f"  URL: {url}")
    logger.info(f"  Output: {output}")
    logger.info(f"  Focus: {focus}")

    # Create output directory if needed
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run extraction
    try:
        result = asyncio.run(extract_arxiv_summary(url, focus, output_path, logger))

        if result:
            logger.info("\n✨ Summary extraction complete!")
            logger.info(f"📄 Summary saved to: {output_path}")

            # Emit file created event for web UI
            logger.file_created(
                str(output_path),
                metadata={"type": "summary", "url": url, "focus": focus},
            )
            return 0
        logger.error("\n❌ Summary extraction failed")
        return 1

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
