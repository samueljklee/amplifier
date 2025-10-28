"""Core Claude session implementation with robust error handling."""

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any

from .models import SessionOptions
from .models import SessionResponse


class SessionError(Exception):
    """Base exception for session errors."""


class SDKNotAvailableError(SessionError):
    """Raised when Claude CLI/SDK is not available."""


class ClaudeSession:
    """Async context manager for Claude Code SDK sessions.

    This provides a robust wrapper around the claude_code_sdk with:
    - Prerequisite checking for the claude CLI
    - Automatic retry with exponential backoff
    - Graceful degradation when SDK unavailable
    """

    def __init__(self, options: SessionOptions | None = None):
        """Initialize session with options.

        Args:
            options: Session configuration options
        """
        self.options = options or SessionOptions()
        self.client = None
        self._check_prerequisites()

    def _check_prerequisites(self):
        """Check if claude CLI is installed and accessible."""
        # Check if claude CLI is available
        claude_path = shutil.which("claude")
        if not claude_path:
            # Check common installation locations
            known_locations = [
                Path.home() / ".local/share/reflex/bun/bin/claude",
                Path.home() / ".npm-global/bin/claude",
                Path("/usr/local/bin/claude"),
            ]

            for loc in known_locations:
                if loc.exists() and os.access(loc, os.X_OK):
                    claude_path = str(loc)
                    break

            if not claude_path:
                raise SDKNotAvailableError(
                    "Claude CLI not found. Install with one of:\n"
                    "  - npm install -g @anthropic-ai/claude-code\n"
                    "  - bun install -g @anthropic-ai/claude-code"
                )

    async def __aenter__(self):
        """Enter async context and initialize SDK client."""
        try:
            # Import SDK only when actually using it
            from claude_agent_sdk import ClaudeAgentOptions
            from claude_agent_sdk import ClaudeSDKClient

            # Build options dict, including tools and permissions
            sdk_options = {
                "model": self.options.model,
                "system_prompt": self.options.system_prompt,
                "max_turns": self.options.max_turns,
                "permission_mode": self.options.permission_mode,
            }

            # Add optional parameters if provided
            if self.options.allowed_tools is not None:
                sdk_options["allowed_tools"] = self.options.allowed_tools

            if self.options.cwd is not None:
                sdk_options["cwd"] = self.options.cwd

                # Auto-enable project settings if cwd is set (loads .claude/ agents/commands/settings)
                if self.options.setting_sources is not None:
                    sdk_options["setting_sources"] = self.options.setting_sources
                else:
                    # Default to loading project settings when cwd is provided
                    # This makes .claude/agents/ and .claude/commands/ available
                    sdk_options["setting_sources"] = ["project"]

            # Pass max_buffer_size if specified (for long sessions with 100+ turns)
            if self.options.max_buffer_size is not None:
                sdk_options["max_buffer_size"] = self.options.max_buffer_size

            self.client = ClaudeSDKClient(options=ClaudeAgentOptions(**sdk_options))
            await self.client.__aenter__()
            return self

        except ImportError:
            raise SDKNotAvailableError(
                "claude-agent-sdk Python package not installed. Install with: pip install claude-agent-sdk or uv add claude-agent-sdk"
            )
        except Exception as e:
            # Catch and report SDK initialization errors clearly
            raise SessionError(f"Failed to initialize Claude Agent SDK: {type(e).__name__}: {e}") from e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def query(self, prompt: str, stream: bool | None = None) -> SessionResponse:
        """Send a query to Claude with automatic retry.

        Args:
            prompt: The prompt to send to Claude
            stream: Override the session's stream_output setting

        Returns:
            SessionResponse with the result or error
        """
        if not self.client:
            return SessionResponse(error="Session not initialized. Use 'async with' context.")

        retry_delay = self.options.retry_delay
        last_error = None

        for attempt in range(self.options.retry_attempts):
            try:
                # Execute query directly
                assert self.client is not None  # Type guard for pyright
                await self.client.query(prompt)

                # Collect response with streaming support
                # IMPORTANT: We need to consume ALL messages until completion
                # This includes text, tool_use, tool_result blocks, etc.
                response_text = ""
                metadata: dict[str, Any] = {"attempt": attempt + 1}
                all_messages = []  # Track all messages for debugging

                try:
                    async for message in self.client.receive_response():
                        all_messages.append(message)  # Store for debugging

                        # Detect agent delegation via Task tool usage
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    # Check for ToolUseBlock with Task tool (agent delegation)
                                    if (
                                        hasattr(block, "name")
                                        and hasattr(block, "input")
                                        and getattr(block, "name", None) == "Task"
                                    ):
                                        # Agent delegation detected!
                                        tool_input = getattr(block, "input", {})
                                        subagent_type = tool_input.get("subagent_type", "unknown")
                                        task_description = tool_input.get("description", "")
                                        tool_use_id = getattr(block, "id", "")

                                        # Track in metadata
                                        if "agents_used" not in metadata:
                                            metadata["agents_used"] = []

                                        agent_info = {
                                            "subagent_type": subagent_type,
                                            "description": task_description,
                                            "tool_use_id": tool_use_id,
                                        }
                                        metadata["agents_used"].append(agent_info)

                                        # Optional: Notify via progress callback
                                        if self.options.progress_callback:
                                            self.options.progress_callback(
                                                f"\n🤖 Delegating to {subagent_type}: {task_description}\n"
                                            )

                        # Extract text content from ContentBlock messages
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        text = getattr(block, "text", "")
                                        if text:
                                            response_text += text

                                            # Stream output if enabled
                                            should_stream = stream if stream is not None else self.options.stream_output
                                            if should_stream:
                                                print(text, end="", flush=True)

                                            # Call progress callback if provided
                                            if self.options.progress_callback:
                                                self.options.progress_callback(text)

                        # Collect metadata from ResultMessage if available
                        if hasattr(message, "__class__") and message.__class__.__name__ == "ResultMessage":
                            if hasattr(message, "session_id"):
                                metadata["session_id"] = getattr(message, "session_id", None)
                            if hasattr(message, "total_cost_usd"):
                                metadata["total_cost_usd"] = getattr(message, "total_cost_usd", 0.0)
                            if hasattr(message, "duration_ms"):
                                metadata["duration_ms"] = getattr(message, "duration_ms", 0)

                except Exception as sdk_error:
                    # Catch SDK internal errors like "No assistant message found"
                    error_msg = str(sdk_error)
                    if "No assistant message found" in error_msg:
                        # This typically means max_turns was hit or session ended unexpectedly
                        # Return what we collected so far
                        metadata["sdk_error"] = error_msg
                        metadata["hit_sdk_limit"] = True

                        if response_text:
                            # Got some text before error
                            return SessionResponse(
                                content=response_text, metadata=metadata, error=f"Session ended: {error_msg}"
                            )
                        if metadata.get("message_count", 0) >= self.options.max_turns:
                            # Hit max_turns without final message
                            return SessionResponse(
                                content="[Session completed: Hit max_turns limit without final assistant message]",
                                metadata=metadata,
                                error="Hit max_turns without final message",
                            )
                        if metadata.get("agents_used"):
                            # Work was delegated to subagents
                            return SessionResponse(
                                content="[Session completed: Work delegated to subagents]",
                                metadata=metadata,
                                error=f"SDK error after agent delegation: {error_msg}",
                            )
                        # True error - no progress made
                        raise
                    # Other SDK error - re-raise
                    raise

                # Store message count for debugging
                metadata["message_count"] = len(all_messages)

                # Add newline after streaming if enabled
                should_stream = stream if stream is not None else self.options.stream_output
                if should_stream and response_text:
                    print()  # Final newline after streaming

                if response_text:
                    return SessionResponse(content=response_text, metadata=metadata)

                # Empty response, will retry
                raise ValueError("Received empty response from SDK")
            except ValueError as e:
                last_error = f"ValueError: {e}"
            except Exception as e:
                # Preserve exception type and details for better debugging
                last_error = f"{type(e).__name__}: {e}"

            # Wait before retry (except on last attempt)
            if attempt < self.options.retry_attempts - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        # All retries exhausted
        return SessionResponse(error=f"Failed after {self.options.retry_attempts} attempts: {last_error}")
