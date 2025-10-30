"""
FAQ formatting functionality.

Generates comprehensive FAQ markdown from analysis results.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class FAQFormatter:
    """Formats analysis results into comprehensive FAQ."""

    async def format_faq(
        self,
        analysis: dict[str, Any],
        extracted_data: dict[str, Any],
    ) -> str | None:
        """Generate FAQ markdown from analysis.

        Args:
            analysis: Repository analysis results
            extracted_data: Original extracted data

        Returns:
            FAQ markdown content or None if failed
        """
        logger.info("Generating FAQ content...")

        # Build comprehensive context
        context = self._build_faq_context(analysis, extracted_data)

        prompt = f"""Generate a comprehensive FAQ markdown document for this project:

{context}

Create a well-structured FAQ that answers common questions about the project.
The FAQ should be organized into clear sections and use an engaging, informative tone.

Include questions and answers covering:
- What is this project and what does it do?
- What are the key features?
- Who is this project for?
- How do I install/set up the project?
- How do I use the project?
- What technology does it use?
- How is the code organized?
- How can I contribute?
- Where can I get help?
- Any other relevant questions based on the project

Format the FAQ as markdown with:
- A clear title
- Brief introduction
- Questions as H2 headers (##)
- Clear, informative answers
- Code examples where helpful
- Links to relevant sections/files if mentioned

Make the FAQ comprehensive but readable. Write in a friendly, approachable tone.
Return ONLY the markdown content, starting with # FAQ title."""

        options = SessionOptions(
            system_prompt="You are an expert technical writer who creates clear, comprehensive documentation.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                faq_content = response.content.strip()

                if not faq_content:
                    logger.error("Empty FAQ content received")
                    return None

                logger.info(f"✓ Generated FAQ ({len(faq_content.split())} words)")
                return faq_content

        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            return None

    def _build_faq_context(
        self,
        analysis: dict[str, Any],
        extracted_data: dict[str, Any],
    ) -> str:
        """Build context for FAQ generation.

        Args:
            analysis: Analysis results
            extracted_data: Extracted data

        Returns:
            Formatted context string
        """
        lines = [
            "=== PROJECT ANALYSIS ===",
            "",
            f"**Purpose**: {analysis.get('purpose', 'Not available')}",
            "",
            "**Features**:",
        ]

        features = analysis.get("features", [])
        if features:
            for feature in features:
                lines.append(f"- {feature}")
        else:
            lines.append("- Features not identified")

        lines.extend(["", "**Technology Stack**:"])

        tech_stack = analysis.get("technology_stack", {})
        if isinstance(tech_stack, dict):
            if tech_stack.get("languages"):
                lines.append(f"  Languages: {', '.join(tech_stack['languages'])}")
            if tech_stack.get("frameworks"):
                lines.append(f"  Frameworks: {', '.join(tech_stack['frameworks'])}")
            if tech_stack.get("tools"):
                lines.append(f"  Tools: {', '.join(tech_stack['tools'])}")

        lines.extend(
            [
                "",
                f"**Architecture**: {analysis.get('architecture', 'Not available')}",
                "",
                "**Setup & Installation**:",
            ]
        )

        setup_steps = analysis.get("setup_installation", [])
        if setup_steps:
            for step in setup_steps:
                lines.append(f"- {step}")
        else:
            lines.append("- Setup instructions not available")

        lines.extend(
            [
                "",
                f"**Usage**: {analysis.get('usage', 'Not available')}",
                "",
                f"**Target Audience**: {analysis.get('target_audience', 'Not specified')}",
                "",
                "**Notable Patterns**:",
            ]
        )

        patterns = analysis.get("notable_patterns", [])
        if patterns:
            for pattern in patterns:
                lines.append(f"- {pattern}")
        else:
            lines.append("- No notable patterns identified")

        lines.extend(
            [
                "",
                "=== PROJECT METADATA ===",
                "",
                f"Total Files Analyzed: {extracted_data.get('total_files', 0)}",
                f"Source Files: {len(extracted_data.get('source_files', []))}",
                f"Documentation Files: {len(extracted_data.get('doc_files', []))}",
            ]
        )

        return "\n".join(lines)
