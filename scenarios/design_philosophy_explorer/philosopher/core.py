"""
Design philosopher core functionality.

Helps users explore and understand design philosophies.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class DesignPhilosopher:
    """Explores design philosophies through interactive guidance."""

    async def explore(self, question: str) -> dict[str, Any]:
        """Explore a design question deeply.

        Args:
            question: User's design question

        Returns:
            Comprehensive exploration of design concepts
        """
        logger.info(f"Exploring question: {question}")

        prompt = f"""Explore this design question deeply:

QUESTION: {question}

Provide a comprehensive exploration covering:

1. CORE CONCEPTS: What fundamental design principles apply?
   - Color theory (if relevant)
   - Motion and animation principles
   - Accessibility considerations
   - Responsive design patterns
   - Theming and consistency
   - User experience fundamentals

2. PRACTICAL GUIDANCE: How to implement these concepts
   - Specific techniques and patterns
   - Tools and frameworks
   - Best practices
   - Common pitfalls to avoid

3. DESIGN PHILOSOPHY: Why these approaches matter
   - User psychology and perception
   - Cultural considerations
   - Accessibility and inclusion
   - Performance implications

4. EXAMPLES: Real-world applications
   - Industry examples
   - Case studies
   - When to apply each approach

Return as JSON with keys:
- concepts: list of design concepts (each with: name, description, relevance)
- guidance: practical implementation advice
- philosophy: underlying principles and reasoning
- examples: real-world applications
- summary: concise synthesis
"""

        options = SessionOptions(
            system_prompt="You are an expert design educator who helps people understand design principles deeply.",
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
                    return self._fallback_exploration(question)

                logger.info(f"Explored {len(result.get('concepts', []))} concepts")
                return result

        except Exception as e:
            logger.error(f"Exploration failed: {e}")
            return self._fallback_exploration(question)

    def _fallback_exploration(self, question: str) -> dict[str, Any]:
        """Provide basic exploration when AI fails.

        Args:
            question: Original question

        Returns:
            Basic exploration structure
        """
        logger.warning("Using fallback exploration")
        return {
            "concepts": [
                {
                    "name": "User-Centered Design",
                    "description": "Design with user needs and capabilities at the center",
                    "relevance": "Fundamental to all good design",
                },
                {
                    "name": "Accessibility",
                    "description": "Ensure your design works for everyone",
                    "relevance": "Critical for inclusive products",
                },
                {
                    "name": "Visual Hierarchy",
                    "description": "Guide attention through layout and emphasis",
                    "relevance": "Essential for usability",
                },
            ],
            "guidance": "Focus on user needs, test with real users, iterate based on feedback.",
            "philosophy": "Good design serves people, not aesthetics alone.",
            "examples": "Apple's iOS: Simple, accessible, consistent. Material Design: Clear hierarchy and motion.",
            "summary": f"Regarding '{question}': Start with user needs, prioritize accessibility, create clear hierarchy.",
        }
