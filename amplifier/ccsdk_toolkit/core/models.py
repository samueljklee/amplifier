"""Data models for CCSDK Core module."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class SessionOptions(BaseModel):
    """Configuration options for Claude sessions.

    Attributes:
        system_prompt: System prompt for the session
        model: Claude model to use (default: claude-sonnet-4-5-20250929)
        max_turns: Maximum conversation turns (default: unlimited)
        retry_attempts: Number of retry attempts on failure (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1.0)
        stream_output: Enable real-time streaming output (default: False)
        progress_callback: Optional callback for progress updates
        allowed_tools: List of tools agent can use (default: all tools enabled)
        permission_mode: Tool permission mode - 'acceptAll', 'acceptEdits', 'manual' (default: acceptAll)
        cwd: Working directory for the agent (default: current directory)
    """

    system_prompt: str = Field(default="You are a helpful assistant")
    model: str = Field(default="claude-sonnet-4-5-20250929", description="Claude model identifier")
    max_turns: int = Field(default=5, gt=0)
    retry_attempts: int = Field(default=5, gt=0, le=10)
    retry_delay: float = Field(default=1.0, gt=0, le=10.0)
    stream_output: bool = Field(default=False, description="Enable real-time streaming output")
    progress_callback: Callable[[str], None] | None = Field(
        default=None,
        description="Optional callback for progress updates",
        exclude=True,  # Exclude from serialization since callables can't be serialized
    )
    allowed_tools: list[str] | None = Field(
        default=None,
        description="List of tools agent can use (e.g. ['Read', 'Write', 'Bash', 'Grep', 'Task']). None = all tools.",
    )
    permission_mode: str = Field(
        default="bypassPermissions",
        description="Tool permission mode: 'acceptEdits', 'bypassPermissions', 'default', or 'plan'",
    )
    cwd: str | None = Field(
        default=None,
        description="Working directory for the agent. None = current directory.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "You are a code review assistant",
                "model": "claude-sonnet-4-5-20250929",
                "max_turns": 1,
                "retry_attempts": 3,
                "retry_delay": 1.0,
                "stream_output": False,  # Streaming disabled by default
            }
        }


class SessionResponse(BaseModel):
    """Response from a Claude session query.

    Attributes:
        content: The response text content
        metadata: Additional metadata about the response
        error: Error message if the query failed
    """

    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = Field(default=None)

    @property
    def success(self) -> bool:
        """Check if the response was successful."""
        return self.error is None and bool(self.content)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Here's the code review...",
                "metadata": {"tokens": 150, "model": "claude-3"},
                "error": None,
            }
        }
