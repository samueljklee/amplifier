from typing import Any, Optional

from pydantic import BaseModel


class WebSocketEvent(BaseModel):
    """Base WebSocket event"""

    type: str
    execution_id: str
    timestamp: Optional[str] = None


class LogEvent(WebSocketEvent):
    """Log message event"""

    type: str = "log"
    level: str = "info"
    message: str


class AgentStartEvent(WebSocketEvent):
    """Agent started event"""

    type: str = "agent.start"
    agent: str
    message: str


class AgentProgressEvent(WebSocketEvent):
    """Agent progress event"""

    type: str = "agent.progress"
    agent: str
    message: str
    progress: Optional[float] = None


class AgentCompleteEvent(WebSocketEvent):
    """Agent completed event"""

    type: str = "agent.complete"
    agent: str
    message: str
    result: Optional[Any] = None


class ExecutionCompleteEvent(WebSocketEvent):
    """Execution completed event"""

    type: str = "execution.complete"
    status: str
    exit_code: int


class ExecutionErrorEvent(WebSocketEvent):
    """Execution error event"""

    type: str = "execution.error"
    error: str


class ProgressEvent(WebSocketEvent):
    """Progress event for long-running operations"""

    type: str = "progress"
    message: str
    current: int
    total: int
    percent: int
    metadata: Optional[dict[str, Any]] = None


class FileCreatedEvent(WebSocketEvent):
    """File created event"""

    type: str = "file.created"
    path: str
    metadata: Optional[dict[str, Any]] = None


class FileUpdatedEvent(WebSocketEvent):
    """File updated event"""

    type: str = "file.updated"
    path: str
    metadata: Optional[dict[str, Any]] = None


class InteractivePromptEvent(WebSocketEvent):
    """Interactive prompt for user input"""

    type: str = "interactive.prompt"
    prompt_text: str
    prompt_type: str = "text"
    prompt_options: list[str] = []


class StageTransitionEvent(WebSocketEvent):
    """Stage transition event"""

    type: str = "stage.transition"
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None  # None when completing the final stage
    estimated_duration: Optional[int] = None


class PreviewAvailableEvent(WebSocketEvent):
    """Preview available event"""

    type: str = "preview.available"
    preview_type: str
    preview_data: Any
    metadata: Optional[dict[str, Any]] = None
