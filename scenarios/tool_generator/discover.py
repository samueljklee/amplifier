"""Discovery stage for tool_generator - Conversational requirements gathering.

This module implements conversational Q&A for gathering tool requirements from users.
It uses the same pattern as scenario_generator but with an outcome-focused approach:
- Asks about WHAT user wants (inputs, outputs, behavior)
- Avoids technical details (CLI, Python, implementation)
- Works identically in CLI and Web UI via interactive_prompt events
"""

import asyncio
import json
import os
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions, ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat

# Use JSON format for web UI, plain for CLI
log_format = LogFormat.JSON if os.getenv("AMPLIFIER_WEB_UI") else LogFormat.PLAIN
logger = ToolkitLogger("tool_generator.discover", format=log_format)

# System prompt for requirements gathering - outcome-focused, not implementation-focused
DISCOVERY_SYSTEM_PROMPT = """You are a helpful assistant gathering requirements for an automation tool.

Your goal is to understand what the user wants to BUILD (the outcome), not how it works internally.

## Guiding Principles

1. **Outcomes over Implementation**
   - Ask: "What problem does this solve?" not "What Python libraries will you use?"
   - Ask: "What inputs does it need?" not "What Click arguments will it have?"
   - Ask: "What should it produce?" not "What file formats will you write?"

2. **Abstract Types over Technical Details**
   - User says "directory of files" → You understand: recursive file processing
   - User says "report with charts" → You understand: structured output with visualization
   - User says "review and refine" → You understand: interactive workflow

3. **Natural Language**
   - No mention of: CLI, Python, SDK, decorators, frameworks
   - No mention of: Click, @option, Path objects, JSON serialization
   - Use: files, data, inputs, outputs, reports, results, processing

## Discovery Flow

Ask clarifying questions about:

1. **Problem/Purpose** - What problem are they trying to solve?
2. **Inputs** - What data/content will they provide? Format and characteristics?
3. **Processing** - What should happen to that data? Does it need AI intelligence?
4. **Outputs** - What should they get back? Format and characteristics?
5. **Interaction Pattern** - Run once, review and refine, or interactive?
6. **Special Requirements** - Performance, formats, integrations?

## Important Rules

- **ONE question at a time** - Keep the conversation natural
- **Follow-up based on answers** - Adapt questions to what they say
- **Clarify ambiguity** - If they're vague, ask specific questions
- **Avoid jargon** - Use plain language, not technical terms

When you have enough information, respond with ONLY this JSON structure (no other text):

```json
{
  "ready": true,
  "tool_name": "suggested_snake_case_name",
  "purpose": "Clear one-sentence description",
  "inputs": {
    "description": "What the user provides",
    "type": "file|files|directory|text|url|data",
    "characteristics": ["specific traits"]
  },
  "processing": {
    "description": "What happens to the data",
    "steps": ["step 1", "step 2"],
    "uses_llm": true|false,
    "special_requirements": []
  },
  "outputs": {
    "description": "What the user gets back",
    "type": "file|report|data|visualization",
    "format": "html|json|csv|pdf|markdown",
    "characteristics": ["viewable", "downloadable"]
  },
  "interaction": "once|iterative|interactive",
  "constraints": {}
}
```

If you need more information, continue asking questions naturally.
"""


class DiscoverStage:
    """Discovers tool requirements through conversational AI."""

    def __init__(self) -> None:
        """Initialize discovery stage."""
        self.logger = logger
        self.conversation_history: list[dict[str, str]] = []

    async def run(self) -> dict[str, Any]:
        """Execute conversational discovery and return requirements.

        This method:
        1. Starts a conversation with Claude
        2. Asks questions about what the user wants to build
        3. Gathers requirements through natural Q&A
        4. Returns structured requirements dict

        Works identically in CLI and Web UI via logger.interactive_prompt().

        Returns:
            Dictionary with structured requirements ready for code generation

        Raises:
            Exception: If conversation fails or requirements parsing fails
        """
        self.logger.info("🔍 Starting conversational requirements discovery...")
        self.logger.info("💬 Tell me about the tool you want to build!")

        # Create Claude session for conversation
        options = SessionOptions(
            system_prompt=DISCOVERY_SYSTEM_PROMPT,
            max_turns=20,  # Allow up to 20 back-and-forth exchanges
        )

        try:
            async with ClaudeSession(options) as session:
                # Start with an opening prompt
                first_response = await session.query(
                    "The user wants to create a new automation tool. "
                    "Greet them warmly and ask what they want to build."
                )

                if not first_response.success:
                    raise Exception(
                        f"Failed to start conversation: {first_response.error}"
                    )

                # Show first question to user
                await self._show_message(first_response.content)

                # Conversation loop - continue until we have complete requirements
                requirements = None
                while not requirements:
                    # Get user's answer
                    user_input = await self._get_user_input()

                    if not user_input.strip():
                        self.logger.warning(
                            "Empty response received, asking for clarification"
                        )
                        await self._show_message(
                            "I didn't catch that. Could you tell me more?"
                        )
                        continue

                    # Send to Claude and get next question or final requirements
                    claude_response = await session.query(user_input)

                    if not claude_response.success:
                        raise Exception(f"Conversation error: {claude_response.error}")

                    # Try to parse requirements from response
                    requirements = self._parse_requirements(claude_response.content)

                    if requirements:
                        # Success! We have complete requirements
                        self.logger.info("✅ Requirements gathered successfully!")
                        return requirements
                    else:
                        # Still gathering info, show next question
                        await self._show_message(claude_response.content)

                # This shouldn't be reached, but just in case
                raise Exception("Conversation ended without gathering requirements")

        except Exception as e:
            self.logger.error(f"Discovery failed: {str(e)}")
            raise

    async def _show_message(self, message: str) -> None:
        """Show AI message to user.

        Uses logger.interactive_prompt() which:
        - CLI: Prints message to terminal
        - Web UI: Emits JSON event that shows in chat modal

        Args:
            message: Message from AI assistant
        """
        self.logger.interactive_prompt(
            prompt=message,
            options=[],  # No predefined choices, free-form text
            prompt_type="text",
        )

    async def _get_user_input(self) -> str:
        """Get user input from stdin.

        This blocks waiting for user input:
        - CLI: User types in terminal
        - Web UI: Backend sends response via stdin after user clicks "Send"

        Returns:
            User's response text

        Raises:
            EOFError: If stdin is closed (Ctrl+D or EOF)
        """
        # Run input() in executor to make it async-compatible
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, input, "")
            return response.strip()
        except EOFError:
            raise EOFError(
                "Input ended unexpectedly (EOF/Ctrl+D). Conversation cancelled."
            )

    def _parse_requirements(self, response: str) -> dict[str, Any] | None:
        """Try to parse requirements JSON from Claude's response.

        Claude is instructed to return JSON when requirements are complete.
        This method looks for JSON in the response and validates it.

        Args:
            response: Claude's response text

        Returns:
            Requirements dict if found and valid, None otherwise
        """
        # Look for JSON block in response
        if "```json" in response:
            try:
                # Extract JSON from markdown code block
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()

                # Parse JSON
                requirements = json.loads(json_str)

                # Validate it has the "ready" flag
                if requirements.get("ready"):
                    self.logger.info("Successfully parsed requirements JSON")
                    return requirements
                else:
                    self.logger.debug("JSON found but not marked as ready")
                    return None

            except (json.JSONDecodeError, ValueError) as e:
                self.logger.debug(f"Failed to parse JSON from response: {e}")
                return None

        # No JSON found, still gathering requirements
        return None

    def format_requirements_as_text(self, requirements: dict[str, Any]) -> str:
        """Convert structured requirements to human-readable text.

        This is used to create the requirements text that gets passed
        to the code generator.

        Args:
            requirements: Structured requirements dict

        Returns:
            Formatted requirements text
        """
        lines = [
            f"Tool Name: {requirements['tool_name']}",
            "",
            f"Purpose: {requirements['purpose']}",
            "",
            "Inputs:",
            f"  Description: {requirements['inputs']['description']}",
            f"  Type: {requirements['inputs']['type']}",
        ]

        if requirements["inputs"].get("characteristics"):
            lines.append(
                f"  Characteristics: {', '.join(requirements['inputs']['characteristics'])}"
            )

        lines.extend(
            [
                "",
                "Processing:",
                f"  Description: {requirements['processing']['description']}",
                "  Steps:",
            ]
        )

        for i, step in enumerate(requirements["processing"]["steps"], 1):
            lines.append(f"    {i}. {step}")

        lines.extend(
            [
                f"  Uses LLM: {requirements['processing']['uses_llm']}",
                "",
                "Outputs:",
                f"  Description: {requirements['outputs']['description']}",
                f"  Type: {requirements['outputs']['type']}",
                f"  Format: {requirements['outputs']['format']}",
            ]
        )

        if requirements["outputs"].get("characteristics"):
            lines.append(
                f"  Characteristics: {', '.join(requirements['outputs']['characteristics'])}"
            )

        lines.extend(
            [
                "",
                f"Interaction Pattern: {requirements['interaction']}",
                "",
                "Constraints:",
            ]
        )

        for key, value in requirements.get("constraints", {}).items():
            if value:
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)
