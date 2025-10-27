"""Validates generated tools against amplifier CLI patterns.

This validator checks for critical amplifier patterns:
- ClaudeSession usage
- @add_describe_flag decorator
- No @click.argument usage
- No Path objects as defaults
- Proper documentation structure
"""

from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models.generation import ValidationResult

logger = get_logger(__name__)


class AmplifierPatternValidator:
    """Validates amplifier CLI tool patterns."""

    # Patterns that ALWAYS apply (regardless of tool type)
    UNIVERSAL_PATTERNS = {
        "describe_flag": {
            "files": ["main.py"],
            "check_fn": lambda content: "@add_describe_flag" in content,
            "error": "CLI must have @add_describe_flag decorator (required for Web UI)",
            "fix": "Add @add_describe_flag above @click.command()",
            "reference": "See references/blog_writer/main.py line 15",
        },
        "no_click_argument": {
            "files": ["main.py"],
            "check_fn": lambda content: "@click.argument" not in content,
            "error": "NEVER use @click.argument - breaks Web UI introspection",
            "fix": "Replace @click.argument with @click.option('--param', required=True)",
            "reference": "Web UI can only pass named parameters. See references/blog_writer/main.py",
        },
        "no_path_defaults": {
            "files": ["main.py"],
            "check_fn": lambda content: "default=Path(" not in content,
            "error": "Default values must be JSON-serializable strings, not Path objects",
            "fix": 'Use default="output.json" not default=Path("output.json")',
            "reference": "Path objects break Web UI --describe-parameters introspection",
        },
    }

    # Patterns that ONLY apply when tool uses LLMs
    LLM_PATTERNS = {
        "claude_session_usage": {
            "check_type": "any_module",
            "pattern": "ClaudeSession",
            "error": "Must use ClaudeSession from ccsdk_toolkit",
            "fix": "Add: from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions",
            "reference": "See references/blog_writer for correct pattern",
        },
        "defensive_parsing": {
            "check_type": "any_module",
            "pattern": "parse_llm_json",
            "error": "Should use defensive LLM response parsing",
            "fix": "from amplifier.ccsdk_toolkit.defensive import parse_llm_json",
            "reference": "See references/blog_writer for defensive patterns",
        },
    }

    DOCUMENTATION_REQUIREMENTS = {
        "scenarios": {
            "required": ["README.md", "HOW_TO_CREATE_YOUR_OWN.md"],
            "recommended": ["Makefile"],
            "rationale": "Production tools need full documentation for learning",
        },
        "ai_working": {
            "required": [],
            "recommended": ["README.md"],
            "rationale": "Experimental tools prioritize speed over docs",
        },
    }

    def __init__(self: "AmplifierPatternValidator") -> None:
        """Initialize validator."""
        # No initialization needed - patterns defined as class variable
        super().__init__()

    async def validate(
        self: "AmplifierPatternValidator", tool_path: Path, uses_llm: bool = True
    ) -> ValidationResult:
        """
        Validate tool against amplifier patterns.

        Args:
            tool_path: Path to generated tool directory
            uses_llm: Whether tool uses LLMs (determines which patterns apply)

        Returns:
            ValidationResult with pass/fail and detailed errors
        """
        logger.info(f"Running amplifier pattern validation on {tool_path.name}")
        logger.debug(f"Tool uses LLMs: {uses_llm}")

        errors = []

        # Build patterns to check based on tool requirements
        patterns_to_check = dict(self.UNIVERSAL_PATTERNS)
        if uses_llm:
            patterns_to_check.update(self.LLM_PATTERNS)
            logger.debug("Including LLM-specific patterns")
        else:
            logger.debug("Skipping LLM-specific patterns (tool doesn't use LLMs)")

        # Check each applicable pattern
        for pattern_name, pattern in patterns_to_check.items():
            # Handle different check types
            if "check_type" in pattern and pattern["check_type"] == "any_module":
                # Check for pattern in ANY module's core.py files
                if not self._check_pattern_in_modules(tool_path, pattern["pattern"]):
                    error_msg = (
                        f"{pattern['error']}\n"
                        f"  Pattern: {pattern['pattern']}\n"
                        f"  Fix: {pattern['fix']}\n"
                        f"  Reference: {pattern['reference']}"
                    )
                    errors.append(error_msg)
                    logger.warning(f"Pattern violation: {pattern_name}")
            else:
                # Legacy file-based checks (for UNIVERSAL_PATTERNS)
                for file_name in pattern.get("files", []):
                    file_path = tool_path / file_name

                    if not file_path.exists():
                        errors.append(f"Missing required file: {file_name}")
                        continue

                    content = file_path.read_text()

                    if not pattern["check_fn"](content):
                        error_msg = (
                            f"{pattern['error']}\n"
                            f"  File: {file_name}\n"
                            f"  Fix: {pattern['fix']}\n"
                            f"  Reference: {pattern['reference']}"
                        )
                        errors.append(error_msg)
                        logger.warning(
                            f"Pattern violation: {pattern_name} in {file_name}"
                        )

        # Check documentation requirements based on location
        location = self._determine_location(tool_path)
        doc_requirements = self.DOCUMENTATION_REQUIREMENTS.get(
            location, self.DOCUMENTATION_REQUIREMENTS["scenarios"]
        )

        for required_doc in doc_requirements["required"]:
            if not (tool_path / required_doc).exists():
                errors.append(
                    f"Missing required documentation: {required_doc}\n"
                    f"  Rationale: {doc_requirements['rationale']}\n"
                    f"  Reference: See references/blog_writer/{required_doc} for quality standard"
                )

        # Report results
        if errors:
            logger.error(
                f"Amplifier pattern validation failed with {len(errors)} errors"
            )
            for error in errors:
                logger.error(
                    f"  - {error.split(chr(10))[0]}"
                )  # Log first line of each error
            return ValidationResult(
                passed=False, stage="amplifier_patterns", errors=errors
            )

        logger.info("✓ Amplifier pattern validation passed")
        return ValidationResult(passed=True, stage="amplifier_patterns", errors=[])

    def _check_pattern_in_modules(
        self: "AmplifierPatternValidator", tool_path: Path, pattern: str
    ) -> bool:
        """
        Check if pattern exists in any module's core.py file.

        Args:
            tool_path: Path to tool directory
            pattern: Pattern string to search for

        Returns:
            True if pattern found in at least one module's core.py
        """
        # Check all core.py files in subdirectories (functional modules)
        for core_file in tool_path.rglob("*/core.py"):
            # Skip __pycache__ and hidden directories
            if any(part.startswith((".", "__")) for part in core_file.parts):
                continue

            try:
                content = core_file.read_text()
                if pattern in content:
                    logger.debug(
                        f"Found pattern '{pattern}' in {core_file.relative_to(tool_path)}"
                    )
                    return True
            except Exception as e:
                logger.warning(f"Could not read {core_file}: {e}")
                continue

        logger.debug(f"Pattern '{pattern}' not found in any module core.py files")
        return False

    def _determine_location(self: "AmplifierPatternValidator", tool_path: Path) -> str:
        """
        Determine tool location (scenarios vs ai_working).

        Args:
            tool_path: Path to tool directory

        Returns:
            Location category: "scenarios" or "ai_working"
        """
        path_str = str(tool_path)

        if "scenarios/" in path_str:
            return "scenarios"
        if "ai_working/" in path_str:
            return "ai_working"
        # Default to stricter requirements
        return "scenarios"
