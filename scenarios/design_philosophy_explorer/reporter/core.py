"""
Design reporter core functionality.

Generates comprehensive markdown reports.
"""

from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class DesignReporter:
    """Generates comprehensive design exploration reports."""

    async def generate_report(
        self,
        question: str,
        exploration: dict[str, Any],
        analysis: dict[str, Any] | None,
        critique: dict[str, Any],
    ) -> str:
        """Generate comprehensive markdown report.

        Args:
            question: Original design question
            exploration: Philosophy exploration results
            analysis: Optional directory analysis
            critique: Critique and suggestions

        Returns:
            Markdown formatted report
        """
        logger.info("Generating comprehensive report")

        sections = []

        # Header
        sections.append("# Design Philosophy Exploration Report\n")
        sections.append(f"**Question:** {question}\n")
        sections.append(f"**Generated:** {self._timestamp()}\n")

        # Exploration section
        sections.append("\n---\n")
        sections.append("## Design Concepts Explored\n")
        sections.append(self._format_exploration(exploration))

        # Analysis section (if available)
        if analysis:
            sections.append("\n---\n")
            sections.append("## Implementation Analysis\n")
            sections.append(self._format_analysis(analysis))

        # Critique section
        sections.append("\n---\n")
        sections.append("## Recommendations & Next Steps\n")
        sections.append(self._format_critique(critique, has_analysis=analysis is not None))

        # Summary
        sections.append("\n---\n")
        sections.append("## Summary\n")
        sections.append(self._format_summary(exploration, analysis, critique))

        report = "\n".join(sections)
        logger.info(f"Generated report ({len(report.split())} words)")

        return report

    def _format_exploration(self, exploration: dict[str, Any]) -> str:
        """Format exploration section."""
        sections = []

        # Concepts
        concepts = exploration.get("concepts", [])
        if concepts:
            sections.append("### Core Concepts\n")
            for concept in concepts:
                if isinstance(concept, dict):
                    name = concept.get("name", "Unknown")
                    desc = concept.get("description", "")
                    relevance = concept.get("relevance", "")

                    sections.append(f"#### {name}\n")
                    sections.append(f"{desc}\n")
                    if relevance:
                        sections.append(f"**Relevance:** {relevance}\n")

        # Guidance
        guidance = exploration.get("guidance", "")
        if guidance:
            sections.append("\n### Practical Guidance\n")
            sections.append(f"{guidance}\n")

        # Philosophy
        philosophy = exploration.get("philosophy", "")
        if philosophy:
            sections.append("\n### Design Philosophy\n")
            sections.append(f"{philosophy}\n")

        # Examples
        examples = exploration.get("examples", "")
        if examples:
            sections.append("\n### Real-World Examples\n")
            sections.append(f"{examples}\n")

        return "\n".join(sections)

    def _format_analysis(self, analysis: dict[str, Any]) -> str:
        """Format analysis section."""
        sections = []

        file_count = analysis.get("file_count", 0)
        analyzed_count = analysis.get("analyzed_count", 0)
        maturity = analysis.get("overall_maturity", "unknown")

        sections.append(f"**Files Analyzed:** {analyzed_count} of {file_count} total\n")
        sections.append(f"**Design Maturity:** {maturity}\n")

        # Patterns found
        patterns = analysis.get("patterns_found", [])
        if patterns:
            sections.append("\n### Design Patterns Found\n")
            for pattern in patterns:
                if isinstance(pattern, dict):
                    name = pattern.get("name", "Unknown")
                    desc = pattern.get("description", "")
                    sections.append(f"- **{name}:** {desc}\n")

        # Strengths
        strengths = analysis.get("strengths", [])
        if strengths:
            sections.append("\n### Strengths\n")
            for strength in strengths:
                sections.append(f"- {strength}\n")

        # Gaps
        gaps = analysis.get("gaps", [])
        if gaps:
            sections.append("\n### Areas for Improvement\n")
            for gap in gaps:
                sections.append(f"- {gap}\n")

        return "\n".join(sections)

    def _format_critique(self, critique: dict[str, Any], has_analysis: bool) -> str:
        """Format critique section."""
        sections = []

        if has_analysis:
            # With analysis: show critical/enhancements/future
            critical = critique.get("critical", [])
            if critical:
                sections.append("### Critical Improvements (High Priority)\n")
                for item in critical:
                    if isinstance(item, dict):
                        title = item.get("title", "Unknown")
                        desc = item.get("description", "")
                        impact = item.get("impact", "")
                        effort = item.get("effort", "")

                        sections.append(f"#### {title}\n")
                        sections.append(f"{desc}\n")
                        if impact:
                            sections.append(f"**Impact:** {impact}\n")
                        if effort:
                            sections.append(f"**Effort:** {effort}\n")

            enhancements = critique.get("enhancements", [])
            if enhancements:
                sections.append("\n### Enhancement Opportunities (Medium Priority)\n")
                for item in enhancements:
                    if isinstance(item, dict):
                        title = item.get("title", "Unknown")
                        desc = item.get("description", "")
                        sections.append(f"- **{title}:** {desc}\n")

            future = critique.get("future", [])
            if future:
                sections.append("\n### Future Considerations (Long-term)\n")
                for item in future:
                    if isinstance(item, dict):
                        title = item.get("title", "Unknown")
                        desc = item.get("description", "")
                        sections.append(f"- **{title}:** {desc}\n")

            priority = critique.get("priority_order", [])
            if priority:
                sections.append("\n### Recommended Priority Order\n")
                for i, item in enumerate(priority, 1):
                    sections.append(f"{i}. {item}\n")

        else:
            # Without analysis: show conceptual suggestions
            suggestions = critique.get("suggestions", [])
            if suggestions:
                sections.append("### Actionable Suggestions\n")
                for sugg in suggestions:
                    if isinstance(sugg, dict):
                        title = sugg.get("title", "Unknown")
                        desc = sugg.get("description", "")
                        category = sugg.get("category", "general")
                        sections.append(f"- **{title}** ({category}): {desc}\n")

            resources = critique.get("resources", [])
            if resources:
                sections.append("\n### Recommended Resources\n")
                for resource in resources:
                    sections.append(f"- {resource}\n")

            next_steps = critique.get("next_steps", [])
            if next_steps:
                sections.append("\n### Next Steps\n")
                for i, step in enumerate(next_steps, 1):
                    sections.append(f"{i}. {step}\n")

        return "\n".join(sections)

    def _format_summary(
        self,
        exploration: dict[str, Any],
        analysis: dict[str, Any] | None,
        critique: dict[str, Any],
    ) -> str:
        """Format summary section."""
        sections = []

        # Key takeaways
        summary_text = exploration.get("summary", "")
        if summary_text:
            sections.append(f"{summary_text}\n")

        # Overall assessment if available
        if analysis:
            assessment = critique.get("overall_assessment", "")
            if assessment:
                sections.append(f"\n**Overall Assessment:** {assessment}\n")

        # Action items
        sections.append("\n### Key Action Items\n")

        # Get top priorities
        if analysis:
            critical = critique.get("critical", [])[:3]
            for item in critical:
                if isinstance(item, dict):
                    sections.append(f"- {item.get('title', 'Unknown')}\n")
        else:
            next_steps = critique.get("next_steps", [])[:3]
            for step in next_steps:
                sections.append(f"- {step}\n")

        return "\n".join(sections)

    def _timestamp(self) -> str:
        """Generate timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
