"""Pattern validation - architecture compliance checks."""

from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models.generation import ValidationResult
from ..models.specification import ValidationRule

logger = get_logger(__name__)


class PatternValidator:
    """
    Validates tool follows required patterns.

    Checks validation rules from specification:
    - recursive_glob: Uses **/*.ext patterns
    - input_validation: Validates minimum inputs
    - progress_visibility: Uses logger.info()
    - defensive_utilities: Uses parse_llm_json
    """

    def __init__(self: "PatternValidator", rules: list[ValidationRule]) -> None:
        """
        Initialize pattern validator.

        Args:
            rules: Validation rules to check
        """
        self.rules = rules

    async def validate(self: "PatternValidator", tool_path: Path) -> ValidationResult:
        """
        Run pattern validation on generated tool.

        Args:
            tool_path: Path to generated tool directory

        Returns:
            ValidationResult with pattern check results
        """
        logger.info(f"Running pattern validation on {tool_path.name}")

        errors = []
        warnings = []

        # Check each validation rule
        for rule in self.rules:
            passed, message = await self._check_rule(tool_path, rule)

            if not passed:
                if rule.required:
                    errors.append(f"{rule.name}: {message}")
                else:
                    warnings.append(f"{rule.name}: {message}")

        if errors:
            logger.error(f"Pattern validation failed: {len(errors)} errors")
            return ValidationResult(
                passed=False,
                stage="pattern",
                errors=errors,
                warnings=warnings if warnings else None,
            )

        if warnings:
            logger.warning(f"Pattern validation passed with {len(warnings)} warnings")
        else:
            logger.info("✓ Pattern validation passed")

        return ValidationResult(
            passed=True,
            stage="pattern",
            errors=[],
            warnings=warnings if warnings else None,
        )

    async def _check_rule(
        self: "PatternValidator", tool_path: Path, rule: ValidationRule
    ) -> tuple[bool, str]:
        """
        Check specific validation rule.

        Args:
            tool_path: Path to generated tool
            rule: Validation rule to check

        Returns:
            (passed, message) tuple
        """
        # Read all Python files
        code_files = list(tool_path.glob("**/*.py"))
        code_content = "\n".join(f.read_text() for f in code_files if f.is_file())

        # Check specific patterns
        if rule.check == "uses_recursive_glob_patterns":
            if "glob(" in code_content:
                has_recursive = "**/" in code_content
                return (
                    has_recursive,
                    "Found glob() calls"
                    if has_recursive
                    else "Uses glob() but not recursive **/",
                )
            return False, "No glob() calls found"

        if rule.check == "validates_minimum_inputs":
            has_validation = "len(" in code_content and (
                "< " in code_content or "> " in code_content
            )
            return (
                has_validation,
                "Found length validation"
                if has_validation
                else "No length validation found",
            )

        if rule.check == "has_progress_logging":
            has_logging = (
                "logger.info(" in code_content or "logging.info(" in code_content
            )
            return (
                has_logging,
                "Found progress logging"
                if has_logging
                else "No progress logging found",
            )

        if rule.check == "uses_defensive_utilities":
            has_defensive = "parse_llm_json" in code_content
            return (
                has_defensive,
                "Found defensive utilities"
                if has_defensive
                else "No defensive utilities found",
            )

        # Unknown rule - skip
        logger.debug(f"Unknown validation rule: {rule.check}")
        return True, "Skipped (unknown rule)"
