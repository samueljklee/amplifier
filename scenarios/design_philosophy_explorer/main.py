#!/usr/bin/env python3
"""
Design Philosophy Explorer - Main Orchestrator and CLI

Helps users explore design philosophies and analyze existing implementations.
"""

import asyncio
import os
import sys
from pathlib import Path

import click
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat
from amplifier.ccsdk_toolkit.scenario_base import add_describe_flag

from .analyzer import DesignAnalyzer
from .critic import DesignCritic
from .philosopher import DesignPhilosopher
from .reporter import DesignReporter
from .state import StateManager

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger(name="design_philosophy_explorer", format=log_format)


class DesignExplorationPipeline:
    """Orchestrates the design philosophy exploration pipeline."""

    def __init__(self, state_manager: StateManager):
        """Initialize pipeline with state management.

        Args:
            state_manager: State manager instance
        """
        self.state = state_manager
        self.philosopher = DesignPhilosopher()
        self.analyzer = DesignAnalyzer()
        self.critic = DesignCritic()
        self.reporter = DesignReporter()

    async def run(
        self,
        question: str,
        directory: Path | None = None,
        output_path: Path | None = None,
    ) -> bool:
        """Run the complete exploration pipeline.

        Args:
            question: User's design question to explore
            directory: Optional directory to analyze
            output_path: Output path for report

        Returns:
            True if successful, False otherwise
        """
        # Store inputs
        self.state.state.question = question
        if directory:
            self.state.state.directory = str(directory)
        if output_path:
            self.state.state.output_path = str(output_path)
        self.state.save()

        try:
            # Stage 1: Explore design philosophy
            logger.stage_transition(None, "explore_philosophy", estimated_duration=60)
            logger.info("🎨 Exploring design philosophy...")
            self.state.update_stage("exploring")

            exploration = await self.philosopher.explore(question)
            self.state.set_exploration(exploration)
            self.state.update_stage("explored")

            logger.info(f"✓ Explored {len(exploration.get('concepts', []))} design concepts")

            # Stage 2: Analyze directory if provided
            analysis = None
            if directory:
                logger.stage_transition("explore_philosophy", "analyze_directory", estimated_duration=90)
                logger.info(f"🔍 Analyzing directory: {directory}")
                self.state.update_stage("analyzing")

                analysis = await self.analyzer.analyze(directory, exploration)
                self.state.set_analysis(analysis)
                self.state.update_stage("analyzed")

                logger.info(f"✓ Analyzed {analysis.get('file_count', 0)} files")

            # Stage 3: Generate critique and suggestions
            logger.stage_transition(
                "analyze_directory" if directory else "explore_philosophy", "generate_critique", estimated_duration=60
            )
            logger.info("💡 Generating improvement suggestions...")
            self.state.update_stage("critiquing")

            critique = await self.critic.critique(exploration, analysis)
            self.state.set_critique(critique)
            self.state.update_stage("critiqued")

            logger.info(f"✓ Generated {len(critique.get('suggestions', []))} suggestions")

            # Stage 4: Generate comprehensive report
            logger.stage_transition("generate_critique", "generate_report", estimated_duration=30)
            logger.info("📝 Generating comprehensive report...")
            self.state.update_stage("reporting")

            report = await self.reporter.generate_report(
                question=question,
                exploration=exploration,
                analysis=analysis,
                critique=critique,
            )

            # Save report
            if output_path is None:
                output_path = self.state.session_dir / "design_exploration_report.md"

            # CRITICAL: Create parent directory for output path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)

            self.state.set_report_path(str(output_path))
            self.state.mark_complete()

            logger.info(f"✅ Report saved to: {output_path}")
            logger.file_created(
                str(output_path),
                metadata={
                    "type": "report",
                    "word_count": len(report.split()),
                    "has_analysis": analysis is not None,
                },
            )

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False


# CLI Interface
@add_describe_flag(version="1.0", display_name="Design Philosophy Explorer")
@click.command()
@click.option(
    "--question",
    type=str,
    required=True,
    help="Your design question to explore (e.g., 'How do I create a great user experience?')",
)
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Optional: Directory to analyze for design patterns",
)
@click.option(
    "--output",
    type=str,
    default=None,
    help="Output path for exploration report (default: auto-generated in session dir)",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from saved state",
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset state and start fresh",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    question: str,
    directory: Path | None,
    output: str | None,
    resume: bool,
    reset: bool,
    verbose: bool,
):
    """Design Philosophy Explorer - Explore design concepts and analyze implementations.

    This tool helps you understand design philosophies including color theory, motion,
    accessibility, responsiveness, themes, and animations. It can also analyze existing
    directories to identify design patterns and suggest improvements.

    Example:
        python -m scenarios.design_philosophy_explorer \\
            --question "How do I create engaging animations?" \\
            --directory ./my-web-app/
    """
    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Determine session directory
    session_dir = None
    if resume:
        # Find most recent session for resume
        base_dir = Path(".data/design_philosophy_explorer/sessions")
        if base_dir.exists():
            sessions = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
            if sessions:
                session_dir = sessions[0]
                logger.info(f"Resuming session: {session_dir.name}")

    # Create state manager
    state_manager = StateManager(session_dir)

    # Handle reset
    if reset:
        state_manager.reset()
        logger.info("State reset - starting fresh")

    # Create output path if provided
    output_path = Path(output) if output else None

    # Create and run pipeline
    pipeline = DesignExplorationPipeline(state_manager)

    logger.info("🚀 Starting Design Philosophy Explorer")
    logger.info(f"  Session: {state_manager.session_dir}")
    logger.info(f"  Question: {question}")
    if directory:
        logger.info(f"  Directory: {directory}")
    if output_path:
        logger.info(f"  Output: {output_path}")

    success = asyncio.run(
        pipeline.run(
            question=question,
            directory=directory,
            output_path=output_path,
        )
    )

    if success:
        logger.info("\n✨ Design exploration complete!")
        report_path = state_manager.state.report_path
        logger.info(f"📄 Report saved to: {report_path}")
        return 0
    logger.error("\n❌ Design exploration failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
