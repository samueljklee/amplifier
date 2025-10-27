#!/usr/bin/env python3
"""Tool Generator - Generate amplifier CLI tools from requirements."""

import asyncio
import os
import sys
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .discover import DiscoverStage
from .models.generation import GenerationResult
from .orchestrator.core import ToolGenerationOrchestrator

# Environment-aware logging: JSON for Web UI, plain text for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger("tool_generator", format=log_format)


@add_describe_flag(version="0.1.0", display_name="Tool Generator")
@click.command()
@click.option(
    "--inline",
    "-i",
    help="Inline requirements description (skip conversational Q&A)",
)
@click.option(
    "--iterations",
    "-n",
    default=3,
    type=int,
    help="Maximum refinement iterations (default: 3)",
)
def main(
    inline: str | None,
    iterations: int,
) -> None:
    """
    Generate an amplifier CLI tool through conversational Q&A.

    By default, starts an interactive conversation to gather requirements.
    Use --inline to bypass Q&A and provide requirements directly.

    Usage:

    \b
    # Conversational mode (default - asks questions)
    python -m scenarios.tool_generator

    \b
    # Quick mode (bypass Q&A)
    python -m scenarios.tool_generator --inline "Create a tool that analyzes code complexity"
    """
    logger.info("Tool Generator v0.1.0")
    logger.info("")

    # Get requirements
    if inline:
        # Power user mode: Skip Q&A, use inline description
        requirements = inline
        logger.info("Using inline requirements (Q&A skipped)")
    else:
        # Default mode: Conversational discovery
        try:
            discovery = DiscoverStage()
            requirements_dict = asyncio.run(discovery.run())

            # Convert structured requirements to text format for generator
            requirements = discovery.format_requirements_as_text(requirements_dict)

            logger.info("")
            logger.info("✅ Requirements gathered successfully!")

        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            logger.error("")
            logger.error('You can bypass discovery using: --inline "your requirements"')
            sys.exit(1)

    # Show requirements
    logger.info("")
    logger.info("Requirements:")
    logger.info("-" * 60)
    for line in requirements.split("\n"):
        logger.info(f"  {line}")
    logger.info("-" * 60)
    logger.info("")

    # Determine scenarios directory
    # Assume we're in scenarios/tool_generator
    current_dir = Path(__file__).parent
    repo_root = (
        current_dir.parent.parent
    )  # Up two levels: tool_generator/ -> scenarios/ -> repo root

    # Tools are ALWAYS generated in ./scenarios/ regardless of --output parameter
    # The --output parameter (used by Web UI) is for temporary workspace, not final tool location
    scenarios_dir = repo_root / "scenarios"

    logger.info(f"Tool will be generated in: {scenarios_dir}")

    # Run generation
    try:
        result = asyncio.run(
            generate_tool(
                requirements=requirements,
                scenarios_dir=scenarios_dir,
                max_iterations=iterations,
            )
        )

        if result.success:
            logger.info("")
            logger.info("🎉 Tool generated successfully!")
            logger.info(f"   Location: {result.tool_path}")
            logger.info(f"   Files: {len(result.files_created or [])}")
            logger.info(f"   Iterations: {result.iterations}")
            logger.info("")
            logger.info("Next steps:")
            logger.info(f"  1. cd {result.tool_path}")
            logger.info("  2. Review generated code")
            logger.info("  3. Test: python -m <tool_name> --help")
            sys.exit(0)

        logger.error("")
        logger.error("❌ Tool generation failed")
        if result.errors:
            logger.error("Errors:")
            for error in result.errors:
                logger.error(f"  - {error}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Generation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", error=e)
        sys.exit(1)


async def generate_tool(
    requirements: str, scenarios_dir: Path, max_iterations: int
) -> GenerationResult:
    """
    Generate tool using orchestrator.

    Args:
        requirements: User's tool description
        scenarios_dir: Path to scenarios/ directory where tool will be created
        max_iterations: Maximum refinement iterations

    Returns:
        GenerationResult
    """
    # Create orchestrator - workspace_base should always be None to use .data/
    # Tools are always generated in scenarios_dir
    orchestrator = ToolGenerationOrchestrator(
        scenarios_dir=scenarios_dir, workspace_base=None
    )

    # Generate tool
    result = await orchestrator.generate(
        requirements=requirements, max_iterations=max_iterations
    )

    return result


if __name__ == "__main__":
    main()
