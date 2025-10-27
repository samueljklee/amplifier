"""Generation task and result data models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GenerationTask:
    """Task specification for Claude Code delegation."""

    spec: Any  # ToolSpec reference
    workspace: Path
    task_file: Path  # Path to task.json
    result_file: Path  # Path to result.json
    progress_file: Path  # Path to progress.jsonl


@dataclass
class ValidationResult:
    """Result from tool validation."""

    passed: bool
    stage: str  # "runtime", "static", "pattern", "complete"
    errors: list[str]
    warnings: list[str] | None = None


@dataclass
class GenerationResult:
    """Final result from tool generation."""

    success: bool
    tool_path: Path | None
    validation: ValidationResult
    iterations: int
    errors: list[str] | None = None
    files_created: list[str] | None = None
