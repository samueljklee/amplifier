"""Research Assistant - AI-powered comprehensive research tool.

Conducts multi-stage research with web browsing, fact verification,
theme refinement, and output writing with user feedback loops.
"""

import asyncio
import sys
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .state import StateManager

logger = ToolkitLogger()


@add_describe_flag(version="1.0", display_name="Research Assistant")
@click.command()
@click.option("--question", type=str, required=False, help="Research question or topic to investigate")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for final research (default: auto-generated in session dir)",
)
@click.option(
    "--session-dir", type=click.Path(path_type=Path), default=None, help="Existing session directory to resume from"
)
@click.option("--max-iterations", type=int, default=10, help="Maximum writing iterations (default: 10)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(
    question: str | None, output: Path | None, session_dir: Path | None, max_iterations: int, verbose: bool
) -> None:
    """Research Assistant - Conduct comprehensive research with AI.

    This tool conducts multi-stage research:
    1. Clarifies requirements with you
    2. Performs preliminary web research
    3. Verifies facts against sources
    4. Identifies themes in findings
    5. Refines themes with your input
    6. Conducts deep research on themes
    7. Writes research output with your feedback

    Examples:
        # New research
        python -m scenarios.research_assistant \\
            --question "What are emerging trends in AI-assisted coding?"

        # Resume from session
        python -m scenarios.research_assistant \\
            --session-dir .data/research_assistant/sessions/20241027_123456_abc123def

        # Resume from latest
        python -m scenarios.research_assistant \\
            --session-dir .data/research_assistant/sessions/latest
    """
    # Note: Verbose logging not currently supported by ToolkitLogger
    # if verbose:
    #     logger.set_level("DEBUG")

    # Validate inputs
    if not session_dir and not question:
        logger.error("Either --question (for new research) or --session-dir (to resume) is required")
        sys.exit(1)

    try:
        # Run pipeline
        success = asyncio.run(run_pipeline(question, output, session_dir, max_iterations))

        if success:
            logger.info("🎉 Research complete!")
            sys.exit(0)
        else:
            logger.error("❌ Research pipeline failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user. Run with --session-dir to resume.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


async def run_pipeline(
    research_question: str | None, output_path: Path | None, session_dir: Path | None, max_iterations: int
) -> bool:
    """Run the research pipeline.

    Args:
        research_question: Initial research question (for new sessions)
        output_path: Where to save final research
        session_dir: Existing session to resume
        max_iterations: Max writing iterations

    Returns:
        True if successful, False otherwise
    """
    from .pipeline import ResearchPipeline

    # Initialize state manager
    state_manager = StateManager(session_dir)
    state_manager.state.max_iterations = max_iterations

    # For new sessions, save the question
    if research_question and state_manager.state.research_question_input is None:
        state_manager.state.research_question_input = research_question
        state_manager.save()

    # Run pipeline
    pipeline = ResearchPipeline(state_manager)
    success = await pipeline.run(output_path)

    return success


if __name__ == "__main__":
    main()
