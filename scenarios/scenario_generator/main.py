#!/usr/bin/env python3
"""Scenario Generator - Generate amplifier scenarios from requirements."""

import asyncio
import os
import sys
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .orchestrator.core import ScenarioGenerationOrchestrator

# Environment-aware logging: JSON for Web UI, plain text for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger("scenario_generator", format=log_format)


@add_describe_flag(version="0.1.0", display_name="Scenario Generator")
@click.command()
@click.option(
    "--requirements",
    "-r",
    required=True,
    help="Requirements description for the scenario",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for the generated scenario (defaults to scenarios/)",
)
def main(
    requirements: str,
    output: str | None,
) -> None:
    """
    Generate an amplifier scenario from requirements.

    Usage:

    \b
    # Generate a new scenario
    python -m scenarios.scenario_generator -r "Create a scenario that analyzes code complexity"

    \b
    # Specify output directory
    python -m scenarios.scenario_generator -r "..." -o /path/to/output
    """
    # Determine output directory
    if output:
        output_dir = Path(output)
    else:
        # Default: repo_root/scenarios/
        current_dir = Path(__file__).parent
        repo_root = current_dir.parent.parent
        output_dir = repo_root / "scenarios"

    # logger.info(f"Scenario will be generated in: {output_dir}")

    # Run generation
    try:
        result = asyncio.run(
            generate_scenario(
                requirements=requirements,
                output_dir=output_dir,
            )
        )

        if result.get("success"):
            # logger.info("")
            # logger.info("🎉 Scenario generated successfully!")
            # logger.info(f"   Location: {result.get('scenario_path')}")
            # logger.info("")
            # logger.info("Next steps:")
            # logger.info(f"  1. cd {result.get('scenario_path')}")
            # logger.info("  2. Review generated code")
            # logger.info("  3. Test: python -m <scenario_name> --help")
            sys.exit(0)

        logger.error("")
        logger.error("❌ Scenario generation failed")
        if result.get("errors"):
            logger.error("Errors:")
            for error in result["errors"]:
                logger.error(f"  - {error}")
        sys.exit(1)

    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", error=e)
        sys.exit(1)


async def generate_scenario(
    requirements: str,
    output_dir: Path,
) -> dict:
    """
    Generate scenario using orchestrator.

    Args:
        requirements: User's scenario description
        output_dir: Path to directory where scenario will be created

    Returns:
        dict with success, scenario_path, and errors keys
    """
    # Create orchestrator
    orchestrator = ScenarioGenerationOrchestrator(output_dir=output_dir)

    # Generate scenario
    result = await orchestrator.generate(requirements=requirements)

    return result


if __name__ == "__main__":
    main()
