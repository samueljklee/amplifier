"""
Design critic core functionality.

Generates critique and improvement suggestions.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class DesignCritic:
    """Provides design critique and improvement suggestions."""

    async def critique(
        self,
        exploration: dict[str, Any],
        analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate critique and suggestions.

        Args:
            exploration: Design philosophy exploration
            analysis: Optional directory analysis

        Returns:
            Critique with actionable suggestions
        """
        logger.info("Generating critique and suggestions")

        if analysis:
            return await self._critique_with_analysis(exploration, analysis)
        return await self._critique_conceptual(exploration)

    async def _critique_with_analysis(
        self,
        exploration: dict[str, Any],
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Critique with actual code analysis.

        Args:
            exploration: Design concepts explored
            analysis: Code analysis results

        Returns:
            Detailed critique
        """
        concepts = exploration.get("concepts", [])
        patterns = analysis.get("patterns_found", [])
        gaps = analysis.get("gaps", [])
        strengths = analysis.get("strengths", [])

        prompt = f"""Provide design critique and improvement suggestions:

DESIGN CONCEPTS EXPLORED:
{self._format_concepts(concepts)}

PATTERNS FOUND IN CODE:
{self._format_patterns(patterns)}

STRENGTHS OBSERVED:
{self._format_list(strengths)}

GAPS IDENTIFIED:
{self._format_list(gaps)}

Generate actionable improvement suggestions:

1. CRITICAL IMPROVEMENTS: High-priority changes
   - Accessibility fixes
   - Performance issues
   - Usability problems

2. ENHANCEMENT OPPORTUNITIES: Medium-priority improvements
   - Better design patterns
   - Consistency improvements
   - User experience refinements

3. FUTURE CONSIDERATIONS: Long-term improvements
   - Advanced features
   - Scalability enhancements
   - Innovation opportunities

Return as JSON with keys:
- critical: list of critical improvements (each with: title, description, impact, effort)
- enhancements: list of enhancement opportunities (same structure)
- future: list of future considerations (same structure)
- overall_assessment: summary assessment
- priority_order: ordered list of what to tackle first
"""

        return await self._query_critique(prompt)

    async def _critique_conceptual(self, exploration: dict[str, Any]) -> dict[str, Any]:
        """Critique at conceptual level without code analysis.

        Args:
            exploration: Design concepts explored

        Returns:
            Conceptual critique
        """
        concepts = exploration.get("concepts", [])
        guidance = exploration.get("guidance", "")

        prompt = f"""Provide design improvement suggestions based on these concepts:

DESIGN CONCEPTS:
{self._format_concepts(concepts)}

GUIDANCE PROVIDED:
{guidance}

Generate actionable next steps and suggestions:

1. How to implement these concepts effectively
2. Common mistakes to avoid
3. Tools and resources to use
4. How to validate your design decisions

Return as JSON with keys:
- suggestions: list of actionable suggestions (each with: title, description, category)
- resources: recommended tools, libraries, or learning materials
- validation: how to test/validate design decisions
- next_steps: ordered list of what to do next
"""

        return await self._query_critique(prompt)

    async def _query_critique(self, prompt: str) -> dict[str, Any]:
        """Query AI for critique.

        Args:
            prompt: Critique prompt

        Returns:
            Critique results
        """
        options = SessionOptions(
            system_prompt="You are an expert design critic who provides actionable, prioritized improvement suggestions.",
            model="claude-sonnet-4-5-20250929",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                result = parse_llm_json(response.content)

                # Type guard
                if not isinstance(result, dict):
                    logger.error(f"Expected dict from LLM, got {type(result)}")
                    return self._fallback_critique()

                # Count suggestions across all categories
                total = 0
                for key in ["critical", "enhancements", "future", "suggestions"]:
                    items = result.get(key, [])
                    if isinstance(items, list):
                        total += len(items)

                logger.info(f"Generated {total} total suggestions")
                return result

        except Exception as e:
            logger.error(f"Critique generation failed: {e}")
            return self._fallback_critique()

    def _format_concepts(self, concepts: list) -> str:
        """Format concepts for prompt."""
        if not concepts:
            return "No concepts provided"

        lines = []
        for i, concept in enumerate(concepts, 1):
            if isinstance(concept, dict):
                name = concept.get("name", "Unknown")
                desc = concept.get("description", "")
                lines.append(f"{i}. {name}: {desc}")

        return "\n".join(lines)

    def _format_patterns(self, patterns: list) -> str:
        """Format patterns for prompt."""
        if not patterns:
            return "No patterns found"

        lines = []
        for i, pattern in enumerate(patterns, 1):
            if isinstance(pattern, dict):
                name = pattern.get("name", "Unknown")
                desc = pattern.get("description", "")
                lines.append(f"{i}. {name}: {desc}")

        return "\n".join(lines)

    def _format_list(self, items: list) -> str:
        """Format list items for prompt."""
        if not items:
            return "None identified"

        return "\n".join(f"- {item}" for item in items)

    def _fallback_critique(self) -> dict[str, Any]:
        """Fallback critique when AI fails."""
        logger.warning("Using fallback critique")
        return {
            "suggestions": [
                {
                    "title": "Start with Accessibility",
                    "description": "Ensure your design works for everyone, including keyboard navigation and screen readers",
                    "category": "critical",
                },
                {
                    "title": "Establish Design Tokens",
                    "description": "Create a consistent system of colors, spacing, and typography",
                    "category": "enhancement",
                },
            ],
            "next_steps": ["Audit accessibility", "Define design system", "Test with real users"],
        }
