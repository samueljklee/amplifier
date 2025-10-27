"""
Scenario Specification Schema

Defines the contract for scenario specifications that guide code generation.
This schema captures all necessary information to generate a complete scenario tool.

Based on analysis of blog_writer structure and web UI integration requirements.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkflowType(str, Enum):
    """Type of workflow execution pattern."""

    MULTI_STAGE = "multi_stage"
    SINGLE_PASS = "single_pass"
    ITERATIVE = "iterative"


class InputType(str, Enum):
    """Type of input parameter."""

    FILE = "file"
    DIRECTORY = "directory"
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    CHOICE = "choice"


class OutputType(str, Enum):
    """Type of output generated."""

    FILE = "file"
    DIRECTORY = "directory"
    JSON = "json"
    TEXT = "text"


class LogEventType(str, Enum):
    """Types of events that should be logged for web UI."""

    STAGE_TRANSITION = "stage_transition"
    FILE_CREATED = "file_created"
    PREVIEW_AVAILABLE = "preview_available"
    INTERACTIVE_PROMPT = "interactive_prompt"
    PROGRESS_UPDATE = "progress_update"


class InputSpec(BaseModel):
    """Specification for an input parameter."""

    name: str = Field(..., description="Parameter name (used in CLI and code)")
    type: InputType = Field(..., description="Type of input")
    description: str = Field(..., description="Human-readable description")
    required: bool = Field(True, description="Whether input is required")
    default: Any | None = Field(None, description="Default value if optional")
    cli_flag: str | None = Field(None, description="CLI flag (e.g., '--input')")
    help_text: str | None = Field(None, description="Extended help text for CLI")

    choices: list[str] | None = Field(None, description="Valid choices for CHOICE type")

    validate_exists: bool = Field(False, description="Validate file/dir exists (for FILE/DIRECTORY)")
    validate_not_empty: bool = Field(False, description="Validate not empty (for TEXT)")
    min_value: int | None = Field(None, description="Minimum value (for INTEGER)")
    max_value: int | None = Field(None, description="Maximum value (for INTEGER)")

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, v: list[str] | None, info) -> list[str] | None:  # type: ignore
        """Ensure choices provided for CHOICE type."""
        if info.data.get("type") == InputType.CHOICE and not v:
            raise ValueError("choices required for CHOICE type")
        return v


class OutputSpec(BaseModel):
    """Specification for an output."""

    name: str = Field(..., description="Output name")
    type: OutputType = Field(..., description="Type of output")
    description: str = Field(..., description="Human-readable description")
    default_path: str | None = Field(None, description="Default path/filename")
    auto_generated: bool = Field(False, description="Whether path is auto-generated (e.g., from title)")
    format: str | None = Field(None, description="Format specification (e.g., 'markdown', 'json')")


class StageSpec(BaseModel):
    """Specification for a processing stage."""

    name: str = Field(..., description="Stage identifier (e.g., 'extract_style')")
    display_name: str = Field(..., description="Human-readable name (e.g., 'Extract Style')")
    description: str = Field(..., description="What this stage does")
    estimated_duration: int | None = Field(None, description="Estimated duration in seconds")

    module_name: str = Field(..., description="Python module name (e.g., 'style_extractor')")
    class_name: str = Field(..., description="Class name (e.g., 'StyleExtractor')")
    method_name: str = Field(..., description="Method to call (e.g., 'extract_style')")

    depends_on: list[str] = Field(default_factory=list, description="Stage names this depends on")
    required_state: list[str] = Field(default_factory=list, description="State keys that must exist")

    state_output_key: str | None = Field(None, description="Key to store output in state")
    updates_stage_name: str | None = Field(None, description="Stage name to update state to")

    emits_events: list[LogEventType] = Field(default_factory=list, description="Event types emitted during this stage")


class IterationConfig(BaseModel):
    """Configuration for iterative workflows."""

    max_iterations: int = Field(10, description="Maximum iterations allowed")
    iteration_stages: list[str] = Field(..., description="Stages that repeat each iteration")
    exit_conditions: list[str] = Field(
        default_factory=list, description="Conditions that exit iteration (e.g., 'user_approved', 'no_issues_found')"
    )
    increment_before_save: bool = Field(False, description="Increment iteration before saving (prevents overwriting)")


class StateManagementSpec(BaseModel):
    """Specification for state management."""

    enabled: bool = Field(default=True, description="Whether to use state management")
    state_dir: str = Field(default=".data/{scenario_name}", description="Directory for state files")
    session_based: bool = Field(default=True, description="Create session subdirectories with timestamps")
    state_fields: list[str] = Field(
        default_factory=list, description="Additional state fields beyond defaults (stage, iteration)"
    )
    resume_capability: bool = Field(default=True, description="Support resuming from saved state")
    auto_save: bool = Field(default=True, description="Save state after each operation")


class UIFeaturesSpec(BaseModel):
    """UI feature requirements."""

    supports_web_ui: bool = Field(default=True, description="Support web UI mode")
    supports_cli: bool = Field(default=True, description="Support CLI mode")

    preview_support: bool = Field(default=False, description="Emit preview events for web UI")
    preview_format: str | None = Field(default=None, description="Preview format (e.g., 'markdown', 'json')")

    interactive_prompts: bool = Field(default=False, description="Support interactive user prompts")
    progress_updates: bool = Field(default=True, description="Emit progress updates")
    file_tracking: bool = Field(default=True, description="Track and emit file creation events")

    json_logging: bool = Field(default=True, description="Use JSON logging for web UI")
    structured_events: bool = Field(default=True, description="Emit structured log events")


class DependencySpec(BaseModel):
    """External dependency specification."""

    name: str = Field(..., description="Package name")
    version: str | None = Field(None, description="Version constraint (e.g., '>=1.0.0')")
    purpose: str = Field(..., description="Why this dependency is needed")


class ScenarioSpec(BaseModel):
    """Complete specification for a scenario tool.

    This is the contract between user intent and code generation.
    Contains all information needed to generate a complete, working scenario tool.
    """

    name: str = Field(..., description="Scenario name (used for module/file names)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this scenario does")
    version: str = Field("0.1.0", description="Semantic version")

    workflow_type: WorkflowType = Field(..., description="Type of workflow execution")

    inputs: list[InputSpec] = Field(..., description="Input parameters")
    outputs: list[OutputSpec] = Field(..., description="Generated outputs")

    stages: list[StageSpec] = Field(..., description="Processing stages in order")

    iteration: IterationConfig | None = Field(None, description="Iteration config (for ITERATIVE workflows)")

    state_management: StateManagementSpec = Field(
        default_factory=lambda: StateManagementSpec(), description="State management configuration"
    )

    ui_features: UIFeaturesSpec = Field(default_factory=lambda: UIFeaturesSpec(), description="UI feature requirements")

    dependencies: list[DependencySpec] = Field(
        default_factory=list, description="External dependencies beyond amplifier toolkit"
    )

    generation_notes: str | None = Field(
        None, description="Additional notes for code generation (e.g., special patterns to follow)"
    )

    @field_validator("stages")
    @classmethod
    def validate_stage_dependencies(cls, v: list[StageSpec]) -> list[StageSpec]:
        """Validate stage dependencies reference existing stages."""
        stage_names = {stage.name for stage in v}
        for stage in v:
            for dep in stage.depends_on:
                if dep not in stage_names:
                    raise ValueError(f"Stage '{stage.name}' depends on unknown stage '{dep}'")
        return v

    @field_validator("iteration")
    @classmethod
    def validate_iteration_config(cls, v: IterationConfig | None, info) -> IterationConfig | None:  # type: ignore
        """Ensure iteration config provided for ITERATIVE workflows."""
        if info.data.get("workflow_type") == WorkflowType.ITERATIVE and not v:
            raise ValueError("iteration config required for ITERATIVE workflow")
        return v

    def model_dump_json(self, **kwargs) -> str:  # type: ignore
        """Export as JSON with nice formatting."""
        return super().model_dump_json(indent=2, **kwargs)
