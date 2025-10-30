"""
Repository analysis functionality.

Analyzes repository content using LLM to understand the project.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryAnalyzer:
    """Analyzes repository content to understand the project."""

    async def analyze_repository(self, extracted_data: dict[str, Any]) -> dict[str, Any] | None:
        """Analyze repository to understand what it does.

        Args:
            extracted_data: Extracted repository data

        Returns:
            Analysis results dictionary or None if failed
        """
        source_files = extracted_data["source_files"]
        doc_files = extracted_data["doc_files"]
        structure = extracted_data["structure"]

        logger.info("Analyzing repository with AI...")

        # Build context from files
        context = self._build_analysis_context(source_files, doc_files, structure)

        # Analyze with LLM
        prompt = f"""Analyze this project repository and provide a comprehensive understanding:

{context}

Analyze the project and provide:
1. **Purpose**: What is this project? What problem does it solve?
2. **Key Features**: What are the main features and capabilities?
3. **Technology Stack**: What languages, frameworks, and tools are used?
4. **Architecture**: How is the code organized? What are the main components?
5. **Setup & Installation**: What steps are needed to set up and run the project?
6. **Usage**: How do users interact with or use this project?
7. **Target Audience**: Who is this project for?
8. **Notable Patterns**: Any interesting design patterns or architectural choices?

Return your analysis as a JSON object with these keys:
{{
    "purpose": "Clear description of what the project does",
    "features": ["feature1", "feature2", ...],
    "technology_stack": {{
        "languages": ["lang1", "lang2"],
        "frameworks": ["framework1", ...],
        "tools": ["tool1", ...]
    }},
    "architecture": "Description of how the code is organized",
    "setup_installation": ["step1", "step2", ...],
    "usage": "How users interact with the project",
    "target_audience": "Who this is for",
    "notable_patterns": ["pattern1", "pattern2", ...]
}}

Be thorough but concise. Focus on the most important aspects."""

        options = SessionOptions(
            system_prompt="You are an expert software architect who analyzes codebases to understand their purpose and design.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)

                # Parse response with defensive parsing
                result = parse_llm_json(response.content)

                # CRITICAL: Type guard after parsing
                if not isinstance(result, dict):
                    logger.error("Expected dict from LLM analysis, got invalid format")
                    return None

                # Validate required fields
                required_fields = [
                    "purpose",
                    "features",
                    "technology_stack",
                    "architecture",
                    "setup_installation",
                    "usage",
                ]
                for field in required_fields:
                    if field not in result:
                        logger.warning(f"Missing field in analysis: {field}")
                        result[field] = self._get_default_value(field)

                logger.info("✓ Analysis complete")
                return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None

    def _build_analysis_context(
        self,
        source_files: list[dict[str, Any]],
        doc_files: list[dict[str, Any]],
        structure: dict[str, Any],
    ) -> str:
        """Build context string for analysis.

        Args:
            source_files: List of source file data
            doc_files: List of documentation file data
            structure: Directory structure information

        Returns:
            Formatted context string
        """
        lines = []

        # Add documentation first (most informative)
        if doc_files:
            lines.append("=== DOCUMENTATION FILES ===\n")
            for doc in doc_files[:5]:  # Limit to first 5 docs
                lines.append(f"File: {doc['name']}")
                # Truncate very long docs
                content = doc["content"][:5000] if len(doc["content"]) > 5000 else doc["content"]
                lines.append(content)
                lines.append("\n" + "=" * 50 + "\n")

        # Add structure overview
        lines.append("=== PROJECT STRUCTURE ===\n")
        lines.append(f"Directories: {', '.join(structure.get('directories', [])[:10])}")
        lines.append(f"File types: {structure.get('file_types', {})}")
        lines.append("\n")

        # Add sample source files
        if source_files:
            lines.append("=== SOURCE CODE SAMPLES ===\n")
            # Prioritize main/init/setup files
            priority_names = ["main", "__init__", "__main__", "setup", "index", "app"]
            priority_files = [f for f in source_files if any(name in f["name"].lower() for name in priority_names)]
            other_files = [f for f in source_files if f not in priority_files]

            sample_files = (priority_files + other_files)[:10]  # Limit to 10 files

            for src in sample_files:
                lines.append(f"File: {src['name']}")
                # Truncate very long files
                content = src["content"][:2000] if len(src["content"]) > 2000 else src["content"]
                lines.append(content)
                lines.append("\n" + "=" * 50 + "\n")

        return "\n".join(lines)

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field.

        Args:
            field: Field name

        Returns:
            Default value for the field
        """
        defaults: dict[str, Any] = {
            "purpose": "Project purpose not determined",
            "features": [],
            "technology_stack": {"languages": [], "frameworks": [], "tools": []},
            "architecture": "Architecture not determined",
            "setup_installation": ["Setup instructions not available"],
            "usage": "Usage information not available",
            "target_audience": "Target audience not determined",
            "notable_patterns": [],
        }
        return defaults.get(field, "Not available")
