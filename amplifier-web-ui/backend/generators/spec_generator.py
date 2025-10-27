"""
Specification Generator

Converts user descriptions into ScenarioSpec objects using LLM.
"""

import os
from typing import Any

from models.scenario_spec import ScenarioSpec
from pydantic_ai import Agent


class SpecGenerator:
    """Generates ScenarioSpec from user descriptions using LLM."""

    def __init__(self: "SpecGenerator") -> None:
        """Initialize the spec generator."""
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        self.agent: Agent[None, ScenarioSpec] = Agent(
            model=model,  # type: ignore[call-arg]
            result_retries=2,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self: "SpecGenerator") -> str:
        """Build the system prompt for spec generation."""
        return """You are a scenario specification generator for the Amplifier AI agent toolkit.

Your task is to convert user descriptions into complete ScenarioSpec objects that can be used
to generate working code.

Key principles:
1. **Analyze the workflow pattern**: Determine if it's MULTI_STAGE, SINGLE_PASS, or ITERATIVE
2. **Break down into stages**: For multi-stage workflows, identify clear processing stages
3. **Define inputs/outputs**: Specify all parameters and what the tool produces
4. **State management**: For iterative/multi-stage, plan how state is tracked
5. **UI integration**: Determine what events to emit for web UI visibility

Examples of workflow patterns:

SINGLE_PASS (one-shot processing):
- Convert format A to format B
- Extract information from document
- Generate report from data

MULTI_STAGE (sequential stages with state):
- Research → Draft → Edit → Publish
- Extract → Analyze → Synthesize → Report
- Parse → Validate → Transform → Output

ITERATIVE (repeating until condition met):
- Generate → Review → Revise (until approved)
- Detect issues → Fix → Validate (until clean)
- Simplify → Check readability → Adjust (until target met)

Stage design guidelines:
- Each stage should have ONE clear responsibility
- Stages should be named as verbs (extract, analyze, generate, review)
- Module names should match stage names (snake_case)
- Class names should be PascalCase versions (ExtractStyle)
- Method names should describe the action (extract_style, analyze_data)

State management:
- State fields should track workflow progress (stage, iteration, etc.)
- Use auto_save for reliability
- Enable resume_capability for long-running workflows
- Session-based directories keep runs separate

UI features:
- Always enable json_logging and structured_events for web UI
- Use STAGE_TRANSITION events for major steps
- Use FILE_CREATED events when outputs are generated
- Use INTERACTIVE_PROMPT for user input
- Use PROGRESS_UPDATE for long operations

Return a complete, valid ScenarioSpec object."""

    async def generate_spec(
        self: "SpecGenerator", description: str, additional_context: dict[str, Any] | None = None
    ) -> ScenarioSpec:
        """Generate a ScenarioSpec from a description.

        Args:
            description: User's description of what the scenario should do
            additional_context: Optional additional context (examples, constraints, etc.)

        Returns:
            Complete ScenarioSpec object

        Raises:
            ValueError: If spec generation fails
        """
        prompt = f"""Generate a complete scenario specification for:

{description}

{self._format_additional_context(additional_context)}

Ensure the specification is complete, valid, and follows Amplifier patterns."""

        try:
            result = await self.agent.run(prompt)
            return result.data if hasattr(result, "data") else result  # type: ignore[return-value]
        except Exception as e:
            raise ValueError(f"Failed to generate spec: {e}")

    def _format_additional_context(self: "SpecGenerator", context: dict[str, Any] | None) -> str:
        """Format additional context for the prompt."""
        if not context:
            return ""

        lines = ["Additional context:"]

        if "examples" in context:
            lines.append(f"\nExample scenarios to model after: {context['examples']}")

        if "constraints" in context:
            lines.append(f"\nConstraints: {context['constraints']}")

        if "required_features" in context:
            lines.append(f"\nRequired features: {context['required_features']}")

        return "\n".join(lines)

    async def refine_spec(self: "SpecGenerator", spec: ScenarioSpec, feedback: str) -> ScenarioSpec:
        """Refine an existing spec based on feedback.

        Args:
            spec: Existing ScenarioSpec
            feedback: User feedback on what to change

        Returns:
            Refined ScenarioSpec
        """
        prompt = f"""Refine this scenario specification based on feedback:

Current spec:
{spec.model_dump_json()}

Feedback:
{feedback}

Return the updated specification."""

        try:
            result = await self.agent.run(prompt)
            return result.data if hasattr(result, "data") else result  # type: ignore[return-value]
        except Exception as e:
            raise ValueError(f"Failed to refine spec: {e}")
