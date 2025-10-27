"""Structured logger for CCSDK toolkit."""

import json
import sys
from pathlib import Path
from typing import Any

from .models import LogEntry
from .models import LogLevel


class ToolkitLogger:
    """Structured logger with JSON and text output.

    Provides structured logging with:
    - JSON or plaintext output formats
    - Real-time streaming to stdout/stderr
    - File logging support
    - Debug mode with verbose output
    - Parent process log aggregation
    - Optional desktop notifications for stage/task completion
    """

    def __init__(
        self,
        output_format: str = "text",
        output_file: Path | None = None,
        debug: bool = False,
        source: str | None = None,
        enable_notifications: bool = False,
    ):
        """Initialize logger.

        Args:
            output_format: "json" or "text" output format
            output_file: Optional file to write logs to
            debug: Enable debug logging
            source: Default source identifier
            enable_notifications: Enable desktop notifications for stage/task completion
        """
        self.output_format = output_format
        self.output_file = output_file
        self.debug_mode = debug  # Renamed to avoid conflict with debug method
        self.source = source
        self.min_level = LogLevel.DEBUG if debug else LogLevel.INFO
        self.enable_notifications = enable_notifications

    def log(self, level: LogLevel, message: str, metadata: dict[str, Any] | None = None, source: str | None = None):
        """Log a message.

        Args:
            level: Log level
            message: Log message
            metadata: Additional structured data
            source: Source identifier (overrides default)
        """
        # Skip debug logs if not in debug mode
        if level == LogLevel.DEBUG and not self.debug_mode:
            return

        entry = LogEntry(level=level, message=message, metadata=metadata or {}, source=source or self.source)

        # Format output
        if self.output_format == "json":
            output = json.dumps(entry.to_json()) + "\n"
        else:
            output = entry.to_text() + "\n"

        # Write to appropriate stream
        stream = sys.stderr if level in [LogLevel.ERROR, LogLevel.CRITICAL] else sys.stdout
        stream.write(output)
        stream.flush()

        # Write to file if configured
        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(output)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, metadata=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log(LogLevel.INFO, message, metadata=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log(LogLevel.WARNING, message, metadata=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.log(LogLevel.ERROR, message, metadata=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, metadata=kwargs)

    def stream_action(self, action: str, details: dict | None = None):
        """Log a real-time action for streaming output.

        Args:
            action: Action being performed
            details: Additional action details
        """
        metadata = {"action": action}
        if details:
            metadata.update(details)
        self.info(f"Action: {action}", **metadata)

    def set_level(self, level: LogLevel):
        """Set minimum log level.

        Args:
            level: Minimum level to log
        """
        self.min_level = level

    def child(self, source: str) -> "ToolkitLogger":
        """Create a child logger with a new source.

        Args:
            source: Source identifier for child logger

        Returns:
            New ToolkitLogger instance
        """
        return ToolkitLogger(
            output_format=self.output_format,
            output_file=self.output_file,
            debug=self.debug_mode,
            source=f"{self.source}.{source}" if self.source else source,
            enable_notifications=self.enable_notifications,
        )

    def stage_start(self, stage_name: str, message: str | None = None):
        """Mark the start of a processing stage.

        Args:
            stage_name: Name of the stage
            message: Optional message to log
        """
        if message:
            self.info(f"Starting stage: {stage_name} - {message}", stage=stage_name)
        else:
            self.info(f"Starting stage: {stage_name}", stage=stage_name)

    def stage_complete(self, stage_name: str, message: str, **kwargs):
        """Mark stage completion (no longer sends notifications).

        Args:
            stage_name: Name of the completed stage
            message: Completion message
            **kwargs: Additional metadata to include
        """
        # Log the completion
        metadata = {"stage": stage_name, **kwargs}
        self.info(f"Stage complete: {stage_name} - {message}", **metadata)

        # No longer send progress notifications - only final completion

    def task_complete(self, message: str, duration: float | None = None, success: bool = True):
        """Mark task completion and send final notification.

        Args:
            message: Completion message
            duration: Total task duration in seconds (ignored for notifications)
            success: Whether the task completed successfully
        """
        # Log the completion
        metadata: dict[str, Any] = {"success": success}
        if duration:
            metadata["duration_seconds"] = round(duration, 2)

        if success:
            self.info(f"Task complete: {message}", **metadata)
        else:
            self.error(f"Task failed: {message}", **metadata)

        # Send notification if enabled
        if self.enable_notifications:
            try:
                # Lazy import to avoid dependency when not needed
                import os

                from amplifier.utils.notifications import send_notification

                send_notification(
                    title="Amplifier",
                    message=message,
                    cwd=os.getcwd(),
                )
            except ImportError:
                self.debug("Notifications not available - amplifier.utils.notifications not found")
            except Exception as e:
                self.debug(f"Failed to send notification: {e}")

    # Structured event methods for rich UI

    def progress(self, current: int, total: int, message: str, **kwargs):
        """Emit progress event for long-running operations.

        Args:
            current: Current progress value
            total: Total progress value
            message: Progress message
            **kwargs: Additional metadata
        """
        percent = int((current / total) * 100) if total > 0 else 0
        self.info(
            message,
            event_type="progress",
            progress_current=current,
            progress_total=total,
            progress_percent=percent,
            **kwargs,
        )

    def file_created(self, path: str, metadata: dict[str, Any] | None = None):
        """Emit file creation event.

        Args:
            path: Path to created file
            metadata: Optional file metadata (size, type, etc.)
        """
        self.info(f"File created: {path}", event_type="file.created", file_path=path, file_metadata=metadata or {})

    def file_updated(self, path: str, metadata: dict[str, Any] | None = None):
        """Emit file update event.

        Args:
            path: Path to updated file
            metadata: Optional file metadata
        """
        self.info(f"File updated: {path}", event_type="file.updated", file_path=path, file_metadata=metadata or {})

    def interactive_prompt(self, prompt: str, options: list[str] | None = None, prompt_type: str = "text"):
        """Emit interactive prompt for user input.

        Args:
            prompt: Prompt text to display
            options: Optional list of choices
            prompt_type: Type of input ("text", "choice", "confirmation")
        """
        self.info(
            prompt,
            event_type="interactive.prompt",
            prompt_text=prompt,
            prompt_options=options or [],
            prompt_type=prompt_type,
        )

    def stage_transition(self, from_stage: str | None, to_stage: str, estimated_duration: int | None = None):
        """Emit stage transition event.

        Args:
            from_stage: Previous stage name (None if starting)
            to_stage: Next stage name
            estimated_duration: Estimated duration in seconds
        """
        msg = f"Transitioning to: {to_stage}"
        if from_stage:
            msg = f"Transitioning from {from_stage} to {to_stage}"

        self.info(
            msg,
            event_type="stage.transition",
            from_stage=from_stage,
            to_stage=to_stage,
            estimated_duration=estimated_duration,
        )

    def preview_available(self, preview_type: str, preview_data: Any, **kwargs):
        """Emit preview available event for UI to display.

        Args:
            preview_type: Type of preview ("text", "image", "json", "markdown")
            preview_data: Preview data (could be URL, text, or structured data)
            **kwargs: Additional metadata
        """
        self.info(
            f"Preview available: {preview_type}",
            event_type="preview.available",
            preview_type=preview_type,
            preview_data=preview_data,
            **kwargs,
        )
