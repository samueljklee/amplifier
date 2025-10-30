"""Research pipeline orchestrator."""

from pathlib import Path

from amplifier.ccsdk_toolkit import ToolkitLogger

from .state import StateManager

logger = ToolkitLogger()


class ResearchPipeline:
    """Orchestrates the 7-phase research pipeline."""

    def __init__(self, state_manager: StateManager):
        """Initialize pipeline with state manager.

        Args:
            state_manager: State manager for persistence
        """
        self.state = state_manager

    async def run(self, output_path: Path | None = None) -> bool:
        """Run complete research pipeline.

        Args:
            output_path: Where to save final output

        Returns:
            True if successful, False otherwise
        """
        try:
            # Resume from saved phase
            phase = self.state.state.current_phase
            logger.info(f"📍 Current phase: {phase}")

            # PHASE 1: Requirements Gathering
            if phase == "initialized":
                await self._phase_requirements()
                phase = self.state.state.current_phase

            # PHASE 2: Preliminary Research
            if phase == "requirements_complete":
                await self._phase_preliminary_research()
                phase = self.state.state.current_phase

            # PHASE 3: Fact Verification
            if phase == "preliminary_research_complete":
                await self._phase_fact_verification()
                phase = self.state.state.current_phase

            # PHASE 4: Theme Extraction
            if phase == "verification_complete":
                await self._phase_theme_extraction()
                phase = self.state.state.current_phase

            # PHASE 5: Theme Refinement
            if phase == "themes_extracted":
                await self._phase_theme_refinement()
                phase = self.state.state.current_phase

            # PHASE 6: Deep Research
            if phase == "themes_refined":
                await self._phase_deep_research()
                phase = self.state.state.current_phase

            # PHASE 7: Writing
            if phase == "deep_research_complete":
                await self._phase_writing()
                phase = self.state.state.current_phase

            # Save final output
            if phase == "complete":
                await self._save_final_output(output_path)
                return True

            logger.error(f"Pipeline did not complete (stuck at {phase})")
            return False

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False

    async def _phase_requirements(self) -> None:
        """Phase 1: Gather and clarify requirements."""
        logger.info("📋 Phase 1: Gathering requirements...")

        from .clarifier import RequirementsClarifier

        clarifier = RequirementsClarifier()
        requirements = await clarifier.clarify_requirements(self.state.state.research_question_input, self.state)

        # Save to state
        self.state.state.research_question = requirements["research_question"]
        self.state.state.research_type = requirements["research_type"]
        self.state.state.researcher_persona = requirements["researcher_persona"]
        self.state.state.research_depth = requirements["research_depth"]
        self.state.state.output_format = requirements["output_format"]
        self.state.state.requirements_clarified = True

        self.state.update_phase("requirements_complete")
        logger.info("✅ Requirements clarified")

    async def _phase_preliminary_research(self) -> None:
        """Phase 2: Conduct preliminary web research."""
        logger.info("🔍 Phase 2: Preliminary research...")
        raise NotImplementedError("Phase 2 not yet implemented")

    async def _phase_fact_verification(self) -> None:
        """Phase 3: Verify facts with AI-to-AI feedback loop."""
        logger.info("🔎 Phase 3: Fact verification...")
        raise NotImplementedError("Phase 3 not yet implemented")

    async def _phase_theme_extraction(self) -> None:
        """Phase 4: Extract themes from verified notes."""
        logger.info("🎯 Phase 4: Theme extraction...")
        raise NotImplementedError("Phase 4 not yet implemented")

    async def _phase_theme_refinement(self) -> None:
        """Phase 5: Refine themes with user feedback."""
        logger.info("👤 Phase 5: Theme refinement...")
        raise NotImplementedError("Phase 5 not yet implemented")

    async def _phase_deep_research(self) -> None:
        """Phase 6: Deep research on refined themes."""
        logger.info("🔬 Phase 6: Deep research...")
        raise NotImplementedError("Phase 6 not yet implemented")

    async def _phase_writing(self) -> None:
        """Phase 7: Write research output with review."""
        logger.info("✍️ Phase 7: Writing...")
        raise NotImplementedError("Phase 7 not yet implemented")

    async def _save_final_output(self, output_path: Path | None) -> None:
        """Save final research to file."""
        logger.info("💾 Saving final output...")

        from amplifier.ccsdk_toolkit.utils import slugify

        # Check if we have final output
        if not self.state.state.final_output:
            logger.error("No final output to save")
            return

        # Extract title for filename
        lines = self.state.state.final_output.split("\n")
        title = next((line.strip("# ").strip() for line in lines if line.startswith("# ")), None)

        if title:
            slug = slugify(title)
            final_path = self.state.session_dir / f"{slug}.md"
        else:
            final_path = output_path or self.state.session_dir / "research_output.md"

        try:
            final_path.write_text(self.state.state.final_output)
            logger.info(f"✅ Research saved to: {final_path}")

            # Emit events for Web UI
            logger.file_created(
                str(final_path),
                metadata={
                    "type": "final_research",
                    "word_count": len(self.state.state.final_output.split()),
                    "phases_completed": len(self.state.state.completed_phases),
                },
            )

            # Update state
            self.state.state.output_path = str(final_path)
            self.state.save()

        except Exception as e:
            logger.error(f"Could not save output: {e}")
            raise
