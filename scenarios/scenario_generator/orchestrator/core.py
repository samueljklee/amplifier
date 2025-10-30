"""Scenario Generation Orchestrator - Uses Claude Code SDK to generate scenarios."""

import os
from pathlib import Path

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession
from amplifier.ccsdk_toolkit.logger import LogFormat

# Environment-aware logging
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger("scenario_generator.orchestrator", format=log_format)


class ScenarioGenerationOrchestrator:
    """Orchestrates scenario generation using Claude Code SDK."""

    def __init__(self, output_dir: Path):
        """Initialize orchestrator.

        Args:
            output_dir: Directory where scenario will be created
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(self, requirements: str) -> dict:
        """
        Generate a scenario from requirements.

        Args:
            requirements: User's scenario description

        Returns:
            dict with keys:
                - success: bool
                - scenario_path: Path to generated scenario
                - errors: list of error messages
        """
        # Build the prompt for Claude
        prompt = f"""/ultrathink-task {requirements}"""

        # Configure session options (same as tool_generator)
        max_turns = int(os.getenv("SCENARIO_GEN_MAX_TURNS", "200"))

        # Progress callback to log agent activity and emit streaming events
        progress_buffer = []
        current_context = {"source": "assistant", "in_tool_call": False, "in_subagent": False}

        def log_progress(text: str) -> None:
            """Log agent progress and emit streaming events."""
            import re

            progress_buffer.append(text)
            full_text = "".join(progress_buffer)

            # Detect context changes for source attribution
            # Subagent delegation patterns
            if "🤖 Delegating to" in text or "Delegating to" in text:
                current_context["in_subagent"] = True
                current_context["source"] = "agent"
                # Extract agent name if possible
                match = re.search(r"Delegating to (\w+(?:-\w+)*)", text)
                if match:
                    logger.info(f"🤖 Delegating to subagent: {match.group(1)}")

            # Tool call detection patterns
            tool_patterns = [
                r"I'll use the (\w+) tool",
                r"Let me use (\w+)",
                r"I'm going to use (\w+)",
                r"Using (\w+) to",
                r"Let me (\w+) to",
            ]
            for pattern in tool_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    current_context["in_tool_call"] = True
                    current_context["source"] = "tool"
                    break

            # Task list detection
            if "TodoWrite" in text or "todo" in text.lower() and "list" in text.lower():
                logger.info("📋 Managing todo list")

            # Thinking/analysis patterns
            thinking_patterns = [
                "Let me analyze",
                "Let me think",
                "I need to consider",
                "Before I",
                "First, let me",
            ]
            if any(pattern in text for pattern in thinking_patterns):
                current_context["source"] = "thinking"

            # Emit streaming text as it comes (for real-time rendering)
            logger.stream_text(text, source=current_context["source"])

            # Also log complete sentences for traditional logging
            if text.endswith((".", ":", "\n")) or len(full_text) > 200:
                logger.info(f" [amplifier] {full_text.strip()}")
                progress_buffer.clear()
                # Reset context after complete thought
                if not current_context["in_subagent"]:
                    current_context["source"] = "assistant"

        options = SessionOptions(
            system_prompt="",
            max_turns=max_turns,  # Configurable via SCENARIO_GEN_MAX_TURNS env var (default: 200)
            retry_attempts=3,
            allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"],
            permission_mode="bypassPermissions",
            cwd=str(self.output_dir.parent),  # Work from parent of output directory
            stream_output=False,  # Disable stdout streaming (use progress callback instead)
            progress_callback=log_progress,
            model="claude-sonnet-4-5-20250929",  # Use latest model
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)

                logger.debug("CCSDK agent completed generation")
                logger.debug(f"Response success: {response.success}")
                logger.debug(f"Response error: {response.error}")
                logger.debug(f"Response metadata: {response.metadata}")

                # Extract session info
                session_id = response.metadata.get("session_id")
                if session_id:
                    logger.info(f"Session ID: {session_id}")
                    # Session stats available but not logged to reduce noise
                    # message_count = response.metadata.get("message_count", 0)
                    # session_info = {
                    #     "session_id": session_id,
                    #     "cost_usd": response.metadata.get("total_cost_usd", 0.0),
                    #     "duration_ms": response.metadata.get("duration_ms", 0),
                    #     "message_count": message_count,
                    #     "max_turns": max_turns,
                    #     "turn_utilization_pct": int(message_count / max_turns * 100) if max_turns > 0 else 0,
                    #     "hit_turn_limit": message_count >= max_turns,
                    # }
                    # logger.info(f"Session stats: {json.dumps(session_info, indent=2)}")

                if response.success:
                    # Try to find the generated scenario directory
                    scenario_path = self._find_generated_scenario()
                    return {
                        "success": True,
                        "scenario_path": str(scenario_path) if scenario_path else None,
                        "errors": [],
                    }
                return {
                    "success": False,
                    "scenario_path": None,
                    "errors": [response.error or "Unknown error"],
                }

        except Exception as e:
            logger.error(f"Generation failed: {e}", error=e)
            return {
                "success": False,
                "scenario_path": None,
                "errors": [str(e)],
            }

    def _find_generated_scenario(self) -> Path | None:
        """Find the generated scenario directory."""
        # Look for newly created directories in output_dir
        for item in self.output_dir.iterdir():
            if item.is_dir() and (item / "main.py").exists():
                return item
        return None
