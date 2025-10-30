"""
Design analyzer core functionality.

Analyzes code and design implementations in directories.
"""

from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class DesignAnalyzer:
    """Analyzes directories for design patterns."""

    async def analyze(self, directory: Path, exploration: dict[str, Any]) -> dict[str, Any]:
        """Analyze directory for design patterns.

        Args:
            directory: Directory to analyze
            exploration: Design philosophy exploration context

        Returns:
            Analysis of design patterns found
        """
        logger.info(f"Analyzing directory: {directory}")

        # Find relevant files (CRITICAL: recursive glob)
        file_patterns = ["**/*.css", "**/*.scss", "**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.html", "**/*.js"]
        files = []
        for pattern in file_patterns:
            files.extend(list(directory.glob(pattern)))

        if not files:
            logger.warning(f"No design-related files found in {directory}")
            return self._empty_analysis()

        logger.info(f"Found {len(files)} design-related files:")
        for f in files[:5]:
            logger.info(f"  • {f.relative_to(directory)}")
        if len(files) > 5:
            logger.info(f"  ... and {len(files) - 5} more")

        # Sample files for analysis (prevent context overflow)
        max_files = 10
        max_chars_per_file = 2000
        samples = []

        for file in files[:max_files]:
            try:
                content = file.read_text()[:max_chars_per_file]
                rel_path = file.relative_to(directory)
                samples.append(f"=== {rel_path} ===\n{content}")
            except Exception as e:
                logger.warning(f"Could not read {file}: {e}")

        if not samples:
            logger.warning("Could not read any files")
            return self._empty_analysis()

        # Analyze with AI
        combined = "\n\n".join(samples)
        concepts = exploration.get("concepts", [])
        concept_names = [c.get("name", "") for c in concepts if isinstance(c, dict)]

        analysis = await self._analyze_with_ai(combined, concept_names)
        analysis["file_count"] = len(files)
        analysis["analyzed_count"] = len(samples)

        return analysis

    async def _analyze_with_ai(self, samples: str, concepts: list[str]) -> dict[str, Any]:
        """Analyze samples with AI.

        Args:
            samples: Code samples to analyze
            concepts: Design concepts to look for

        Returns:
            Analysis results
        """
        concepts_text = ", ".join(concepts) if concepts else "design principles"

        prompt = f"""Analyze these design implementation files:

{samples}

Looking for these design concepts: {concepts_text}

Identify:
1. DESIGN PATTERNS USED:
   - Color systems (palettes, tokens, variables)
   - Motion/animation implementations
   - Accessibility features (ARIA, semantic HTML, keyboard nav)
   - Responsive patterns (breakpoints, fluid layouts)
   - Theming systems (CSS variables, theme switching)
   - Component design patterns

2. STRENGTHS:
   - What's done well
   - Good practices observed
   - Consistent patterns

3. GAPS:
   - Missing design considerations
   - Accessibility issues
   - Inconsistencies
   - Performance concerns

Return as JSON with keys:
- patterns_found: list of design patterns (each with: name, description, files)
- strengths: list of positive observations
- gaps: list of missing or problematic areas
- overall_maturity: assessment of design maturity (basic/intermediate/advanced)
"""

        options = SessionOptions(
            system_prompt="You are an expert design auditor who analyzes code for design patterns and quality.",
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
                    return self._empty_analysis()

                logger.info(f"Found {len(result.get('patterns_found', []))} patterns")
                logger.info(f"Identified {len(result.get('gaps', []))} gaps")

                return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._empty_analysis()

    def _empty_analysis(self) -> dict[str, Any]:
        """Return empty analysis structure."""
        return {
            "patterns_found": [],
            "strengths": [],
            "gaps": ["Could not analyze directory - no readable files found"],
            "overall_maturity": "unknown",
            "file_count": 0,
            "analyzed_count": 0,
        }
