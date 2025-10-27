"""Data models for workflow creation via AI conversation."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of workflow nodes."""

    INPUT = "input"
    PROCESS = "process"
    OUTPUT = "output"
    CONTROL = "control"


class UIStyle(str, Enum):
    """UI styles for nodes."""

    # Input styles
    FILE_PICKER = "file-picker"
    DRAG_DROP = "drag-drop"
    TEXT_INPUT = "text-input"
    FORM = "form"
    AUTO_WATCH = "auto-watch"

    # Output styles
    DASHBOARD = "dashboard"
    TABLE = "table"
    DOWNLOAD = "download"
    NOTIFICATION = "notification"
    TEXT_DISPLAY = "text-display"

    # Process styles
    PROGRESS_BAR = "progress-bar"
    LOG_VIEWER = "log-viewer"
    CUSTOM = "custom"


class NodeUIConfig(BaseModel):
    """UI configuration for a workflow node."""

    style: UIStyle = Field(..., description="UI style for this node")
    show_preview: bool = Field(default=False, description="Show preview of data")
    allow_parameter_tuning: bool = Field(default=False, description="Allow runtime parameter adjustment")
    custom_component: str | None = Field(default=None, description="Custom React component name if style is CUSTOM")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional UI configuration")


class WorkflowNode(BaseModel):
    """A node in the workflow being designed."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique node ID")
    type: NodeType = Field(..., description="Type of node")
    name: str = Field(..., description="Node name (e.g., 'csv_input', 'sentiment_analysis')")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this node does")

    # Connections
    inputs: list[str] = Field(default_factory=list, description="IDs of nodes that feed into this")
    outputs: list[str] = Field(default_factory=list, description="IDs of nodes this feeds into")

    # UI configuration
    ui_config: NodeUIConfig | None = Field(default=None, description="UI configuration for this node")

    # Position for canvas
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0}, description="Canvas position (x, y)")

    # Implementation details (filled in during conversation)
    module_name: str | None = Field(default=None, description="Python module name")
    class_name: str | None = Field(default=None, description="Python class name")
    method_name: str | None = Field(default=None, description="Python method name")


class WorkflowSpec(BaseModel):
    """Complete specification of a workflow being designed."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Workflow ID")
    name: str = Field(..., description="Workflow name (for file naming)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this workflow does")

    nodes: list[WorkflowNode] = Field(default_factory=list, description="Workflow nodes")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    # Requirements gathered from conversation
    input_format: str | None = Field(default=None, description="Input data format (CSV, JSON, text, etc.)")
    output_requirements: list[str] = Field(default_factory=list, description="Output requirements from user")
    processing_steps: list[str] = Field(default_factory=list, description="Processing steps described by user")

    # Generated artifacts
    test_cases: list[str] = Field(default_factory=list, description="Test cases generated from requirements")
    ready_to_generate: bool = Field(default=False, description="Whether spec is complete enough to generate code")


class Message(BaseModel):
    """A message in the conversation."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class ConversationState(BaseModel):
    """State of an ongoing workflow creation conversation."""

    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Conversation session ID")
    workflow: WorkflowSpec = Field(..., description="Workflow being designed")
    history: list[Message] = Field(default_factory=list, description="Conversation history")

    # Conversation progress
    requirements_gathered: bool = Field(default=False, description="Basic requirements collected")
    nodes_designed: bool = Field(default=False, description="Node structure designed")
    ui_configured: bool = Field(default=False, description="UI preferences collected")

    created_at: datetime = Field(default_factory=datetime.now, description="Session start")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last activity")


class ConversationRequest(BaseModel):
    """Request to continue a conversation."""

    session_id: str | None = Field(default=None, description="Session ID (null to start new)")
    message: str = Field(..., description="User's message")


class ConversationResponse(BaseModel):
    """Response from the AI conversation."""

    session_id: str = Field(..., description="Session ID")
    ai_message: str = Field(..., description="AI's response")
    workflow_preview: WorkflowSpec = Field(..., description="Current workflow state")
    ready_to_generate: bool = Field(..., description="Whether workflow is ready to generate")
    suggested_actions: list[str] = Field(default_factory=list, description="Suggested next actions")
