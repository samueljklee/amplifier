"""Specification builder - converts requirements to ToolSpec."""

from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

from ..models.specification import ToolSpec
from ..models.specification import ValidationRule

logger = get_logger(__name__)


class ParsedRequirements:
    """Structured requirements extracted from user input."""

    def __init__(self, data: dict[str, Any]):
        self.tool_name = data.get("tool_name", "")
        self.purpose = data.get("purpose", "")
        self.input_types = data.get("input_types", [])
        self.output_format = data.get("output_format", "")
        self.processes_files = (
            "files" in self.input_types or "directory" in self.input_types
        )
        self.has_minimum_inputs = data.get("minimum_inputs", 0) > 0
        self.uses_llm = data.get("uses_llm", False)
        self.constraints = data.get("constraints", {})


class SpecificationBuilder:
    """
    Converts user requirements into structured ToolSpec.

    Process:
    1. Parse requirements with LLM (extract structured data)
    2. Select appropriate reference tools
    3. Generate validation rules from patterns
    4. Build complete ToolSpec
    """

    def __init__(self, scenarios_dir: Path):
        """
        Initialize specification builder.

        Args:
            scenarios_dir: Path to scenarios/ directory with reference tools
        """
        self.scenarios_dir = scenarios_dir
        logger.debug(
            f"SpecificationBuilder initialized with scenarios_dir: {scenarios_dir}"
        )

    async def build(self, requirements: str) -> ToolSpec:
        """
        Build ToolSpec from free-form requirements.

        Args:
            requirements: User's tool description

        Returns:
            Complete ToolSpec ready for generation
        """
        logger.info("Building tool specification from requirements")

        # 1. Parse requirements into structured data
        parsed = await self._parse_requirements(requirements)

        # 2. Select reference tools
        references = self._select_references(parsed)

        # 3. Generate validation rules
        rules = self._generate_validation_rules(parsed)

        # 4. Build ToolSpec
        spec = ToolSpec(
            tool_name=parsed.tool_name,
            requirements=requirements,
            reference_tools=references,
            validation_rules=rules,
            constraints=parsed.constraints,
            uses_llm=parsed.uses_llm,
        )

        logger.info(f"Built specification for tool: {parsed.tool_name}")
        return spec

    async def _parse_requirements(self, requirements: str) -> ParsedRequirements:
        """
        Extract structured data from free-form requirements.

        Uses LLM to identify:
        - Tool name and purpose
        - Input types (files, directories, URLs, etc.)
        - Output format (files, JSON, reports, etc.)
        - Processing steps
        - Dependencies and constraints

        Args:
            requirements: User's tool description

        Returns:
            ParsedRequirements with structured data
        """
        prompt = f"""Extract structured information from this tool requirement:

{requirements}

Return JSON with this structure:
{{
    "tool_name": "snake_case_name",
    "purpose": "One sentence description",
    "input_types": ["files", "directory", "url", "text"],
    "output_format": "markdown|json|files|report",
    "minimum_inputs": 0,
    "uses_llm": true|false,
    "constraints": {{}}
}}

Return ONLY the JSON object, no other text."""

        # Determine repo root for agent access
        repo_root = self.scenarios_dir.parent

        options = SessionOptions(
            system_prompt="You are an expert at analyzing tool requirements and extracting structured data.",
            retry_attempts=3,
            cwd=str(repo_root),  # Enable access to .claude/agents/
            allowed_tools=[
                "Task",
                "Read",
                "Grep",
                "Glob",
            ],  # Allow delegation to specialized agents if needed
        )

        try:
            async with ClaudeSession(options) as session:
                response = await session.query(prompt)
                data = parse_llm_json(response.content, default={})

                if not isinstance(data, dict):
                    logger.error("LLM returned non-dictionary response")
                    # Fallback: extract tool name from requirements
                    data = self._create_fallback_data(requirements)
                elif not data.get("tool_name"):
                    logger.warning("LLM response missing tool_name, using fallback")
                    # Merge fallback tool_name with LLM data
                    fallback_name = self._extract_name_fallback(requirements)
                    data["tool_name"] = fallback_name

                logger.debug(f"Parsed tool name: {data.get('tool_name')}")
                return ParsedRequirements(data)

        except Exception as e:
            logger.error(f"Failed to parse requirements with LLM: {e}")
            # Fallback to basic parsing
            data = self._create_fallback_data(requirements)
            return ParsedRequirements(data)

    def _create_fallback_data(self, requirements: str) -> dict[str, Any]:
        """
        Create fallback data when LLM parsing fails.

        Args:
            requirements: Original requirements text

        Returns:
            Basic structured data dictionary
        """
        return {
            "tool_name": self._extract_name_fallback(requirements),
            "purpose": requirements[:100],
            "input_types": ["files"],
            "output_format": "files",
            "uses_llm": "claude" in requirements.lower()
            or "llm" in requirements.lower(),
            "constraints": {},
        }

    def _extract_name_fallback(self, requirements: str) -> str:
        """
        Extract tool name from requirements as fallback.

        Simple heuristic: first few words, snake_case

        Args:
            requirements: Original requirements text

        Returns:
            Tool name in snake_case
        """
        words = requirements.lower().split()[:3]
        name = "_".join(w for w in words if w.isalnum())
        return name or "generated_tool"

    def _select_references(self, parsed: ParsedRequirements) -> list[Path]:
        """
        Choose reference tools based on similarity.

        Matches on:
        - Input/output patterns
        - Processing complexity
        - LLM usage

        Args:
            parsed: Parsed requirements

        Returns:
            List of reference tool paths
        """
        references = []

        # Always include blog_writer (canonical exemplar)
        blog_writer = self.scenarios_dir / "blog_writer"
        if blog_writer.exists():
            references.append(blog_writer)
            logger.debug("Added blog_writer as reference (canonical exemplar)")

        # If uses LLM, include transcribe
        if parsed.uses_llm:
            transcribe = self.scenarios_dir / "transcribe"
            if transcribe.exists():
                references.append(transcribe)
                logger.debug("Added transcribe as reference (LLM usage)")

        # If processes files, include web_to_md
        if parsed.processes_files:
            web_to_md = self.scenarios_dir / "web_to_md"
            if web_to_md.exists():
                references.append(web_to_md)
                logger.debug("Added web_to_md as reference (file processing)")

        logger.debug(f"Selected {len(references)} reference tools")
        return references

    def _generate_validation_rules(
        self, parsed: ParsedRequirements
    ) -> list[ValidationRule]:
        """
        Create validation rules from patterns and learnings.

        Enforces:
        - Recursive file discovery (if tool processes files)
        - Input validation (if tool has minimum requirements)
        - Progress visibility (always)
        - Defensive utilities (if tool uses LLMs)

        Args:
            parsed: Parsed requirements

        Returns:
            List of ValidationRule
        """
        rules = [
            ValidationRule(
                name="progress_visibility",
                check="has_progress_logging",
                required=True,
                description="Must use logger.info() to show progress",
            )
        ]

        if parsed.processes_files:
            rules.append(
                ValidationRule(
                    name="recursive_glob",
                    check="uses_recursive_glob_patterns",
                    required=True,
                    description="Must use glob('**/*.ext') for file discovery",
                )
            )

        if parsed.has_minimum_inputs:
            rules.append(
                ValidationRule(
                    name="input_validation",
                    check="validates_minimum_inputs",
                    required=True,
                    description="Must validate sufficient inputs before processing",
                )
            )

        if parsed.uses_llm:
            rules.append(
                ValidationRule(
                    name="defensive_utilities",
                    check="uses_defensive_utilities",
                    required=True,
                    description="Must use parse_llm_json and other defensive utilities",
                )
            )

        logger.debug(f"Generated {len(rules)} validation rules")
        return rules
