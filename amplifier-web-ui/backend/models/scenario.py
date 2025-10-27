from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """CLI parameter definition"""

    name: str
    type: Literal["string", "path", "directory", "boolean", "number"]
    required: bool
    default: Optional[Any] = None
    description: str
    validation: Optional[dict[str, Any]] = None


class Example(BaseModel):
    """Usage example for a scenario"""

    title: str
    description: str
    command: str
    input_files: Optional[dict[str, str]] = None


class ScenarioMetadata(BaseModel):
    """Scenario metadata"""

    version: Optional[str] = None
    author: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    """Amplifier CLI scenario"""

    id: str
    name: str
    description: str
    path: str
    cli_command: str
    parameters: list[Parameter]
    examples: list[Example] = Field(default_factory=list)
    metadata: ScenarioMetadata = Field(default_factory=ScenarioMetadata)
