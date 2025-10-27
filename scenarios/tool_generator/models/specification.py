"""Tool specification data models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationRule:
    """Validation rule for generated tools."""

    name: str
    check: str
    required: bool
    description: str | None = None


@dataclass
class ToolSpec:
    """
    Complete specification for tool generation.

    This is the structured contract between user requirements
    and Claude Code implementation.
    """

    tool_name: str
    requirements: str  # Original user requirements
    reference_tools: list[Path]  # Example tools to model after
    validation_rules: list[ValidationRule]  # What makes this tool valid
    constraints: dict[str, Any]  # Hard requirements
    uses_llm: bool = False  # Whether tool uses LLMs (affects validation patterns)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict for task.json."""
        return {
            "tool_name": self.tool_name,
            "requirements": self.requirements,
            "reference_tools": [str(p) for p in self.reference_tools],
            "validation_rules": [
                {
                    "name": rule.name,
                    "check": rule.check,
                    "required": rule.required,
                    "description": rule.description,
                }
                for rule in self.validation_rules
            ],
            "constraints": self.constraints,
            "uses_llm": self.uses_llm,
        }
