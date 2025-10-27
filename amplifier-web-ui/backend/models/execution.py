from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status enum"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Execution(BaseModel):
    """Execution record"""

    id: str
    scenario_id: str
    parameters: dict[str, Any]
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None


class ExecutionRequest(BaseModel):
    """Request to start an execution"""

    parameters: dict[str, Any]
    options: Optional[dict[str, Any]] = None


class ProgressState(BaseModel):
    """Execution progress state"""

    current_stage: str = ""
    stage_number: int = 0
    total_stages: int = 0
    percentage: int = Field(default=0, ge=0, le=100)


class Artifact(BaseModel):
    """Generated artifact file"""

    filename: str
    path: str
    size: int
    content_type: str
    url: str
    created_at: str
    metadata: Optional[dict[str, Any]] = None


class ExecutionOutput(BaseModel):
    """Execution output data"""

    stdout: list[str] = Field(default_factory=list)
    stderr: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)


class ExecutionError(BaseModel):
    """Execution error details"""

    message: str
    traceback: Optional[str] = None


class ExecutionStatusResponse(BaseModel):
    """Complete execution status response"""

    job_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    scenario_id: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: ProgressState = Field(default_factory=ProgressState)
    output: ExecutionOutput = Field(default_factory=ExecutionOutput)
    error: Optional[ExecutionError] = None
