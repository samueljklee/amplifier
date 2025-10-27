"""Models for scenario generation API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    """Status of generation session."""

    ASKING_QUESTIONS = "asking_questions"
    SPEC_READY = "spec_ready"
    GENERATING_CODE = "generating_code"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"


class CreateSessionRequest(BaseModel):
    """Request to create a new generation session."""

    description: str = Field(..., description="User's description of what they want to build")
    name: str | None = Field(None, description="Optional scenario name")


class CreateSessionResponse(BaseModel):
    """Response from creating a session."""

    session_id: str
    status: GenerationStatus


class MessageRole(str, Enum):
    """Message role in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """Message in the conversation history."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionMessage(BaseModel):
    """Message sent to a session."""

    content: str = Field(..., description="User's message or refinement")
    action: str = Field("refine", description="Action: 'refine' (answer question) or 'generate' (approve spec)")


class SessionState(BaseModel):
    """State of a generation session."""

    id: str
    status: GenerationStatus
    description: str
    scenario_name: str | None
    created_at: datetime
    updated_at: datetime
    conversation: list[ConversationMessage] = Field(default_factory=list)
    current_question_index: int = 0
    spec_json: dict[str, Any] | None = None
    generated_files: dict[str, str] | None = None
    validation_results: list[dict[str, Any]] | None = None
    error: str | None = None


class GenerationEvent(BaseModel):
    """Event emitted during generation."""

    type: str
    timestamp: datetime
    message: str
    data: dict[str, Any] | None = None
