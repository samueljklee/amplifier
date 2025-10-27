"""Result reader for Claude Code generation output."""

import json
import logging
from pathlib import Path
from typing import Any

from ..models.generation import GenerationResult
from ..models.generation import ValidationResult

logger = logging.getLogger(__name__)


class ResultReader:
    """
    Reads result.json from Claude Code generation.

    Result format:
    {
        "success": true,
        "tool_name": "content_analyzer",
        "files_created": ["main.py", "models.py"],
        "validation_passed": true,
        "validation_details": {...},
        "errors": []
    }
    """

    def read(self, result_file: Path) -> GenerationResult:
        """
        Parse result.json into GenerationResult.

        Args:
            result_file: Path to result.json

        Returns:
            GenerationResult with parsed data
        """
        if not result_file.exists():
            logger.error(f"Result file not found: {result_file}")
            return GenerationResult(
                success=False,
                tool_path=None,
                validation=ValidationResult(
                    passed=False, stage="file_missing", errors=["result.json not found"]
                ),
                iterations=0,
                errors=["result.json not found"],
            )

        try:
            with open(result_file) as f:
                data = json.load(f)

            logger.info(f"Read result from {result_file}")
            return self._parse_result(data, result_file.parent)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse result.json: {e}")
            return GenerationResult(
                success=False,
                tool_path=None,
                validation=ValidationResult(
                    passed=False, stage="parse_error", errors=[f"Invalid JSON: {e}"]
                ),
                iterations=0,
                errors=[f"Invalid JSON: {e}"],
            )

    def _parse_result(self, data: dict[str, Any], workspace: Path) -> GenerationResult:
        """Parse result data into GenerationResult."""
        success = data.get("success", False)
        tool_name = data.get("tool_name")
        files_created = data.get("files_created", [])
        validation_passed = data.get("validation_passed", False)
        errors = data.get("errors", [])

        # Parse validation details
        validation_details = data.get("validation_details", {})
        validation = ValidationResult(
            passed=validation_passed,
            stage="complete" if validation_passed else "failed",
            errors=errors,
            warnings=validation_details.get("warnings"),
        )

        # Determine tool path
        tool_path = None
        if success and tool_name:
            tool_path = workspace / tool_name

        return GenerationResult(
            success=success,
            tool_path=tool_path,
            validation=validation,
            iterations=data.get("iterations", 1),
            errors=errors if errors else None,
            files_created=files_created if files_created else None,
        )
