"""
State Management Template

Standardized template for state persistence in amplifier CLI tools.
Enables resume capability by saving state after every operation.

Usage:
    1. Copy this template to your tool's directory as `state.py`
    2. Customize the PipelineState dataclass fields for your tool
    3. Add custom methods to StateManager as needed
    4. Use in your main workflow to save/load state automatically

Example:
    from .state import StateManager, PipelineState

    state_mgr = StateManager()
    state_mgr.update_stage("processing")
    state_mgr.save()
"""

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineState:
    """Pipeline state for persistence.

    Customize this dataclass with fields specific to your tool's workflow.
    Common patterns:
    - stage: Current pipeline stage (str)
    - iteration: Current iteration number (int)
    - processed_items: Set of processed item IDs
    - failed_items: Dict mapping item ID to error message
    - outputs: Dict storing module outputs
    """

    # Pipeline progress tracking
    stage: str = "initialized"
    iteration: int = 0
    max_iterations: int = 10

    # Processing tracking
    processed_items: list[str] = field(default_factory=list)
    failed_items: dict[str, str] = field(default_factory=dict)

    # Outputs (customize for your tool)
    outputs: dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Input parameters (store CLI args for resume)
    input_params: dict[str, Any] = field(default_factory=dict)


class StateManager:
    """Manages pipeline state with automatic persistence.

    Provides:
    - Automatic state loading on init (resume capability)
    - Safe state saving with retry logic (handles cloud sync)
    - Convenience methods for common state operations
    - Session directory management

    Usage:
        state_mgr = StateManager()  # Auto-loads if exists
        state_mgr.update_stage("processing")
        state_mgr.mark_item_processed("item_1")
        # State auto-saved after each operation
    """

    def __init__(
        self,
        session_dir: Path | None = None,
        tool_name: str = "tool",
        state_filename: str = "state.json",
    ):
        """Initialize state manager.

        Args:
            session_dir: Path to session directory (default: .data/<tool_name>/<timestamp>/)
            tool_name: Name of the tool (used for default session path)
            state_filename: Name of state file (default: state.json)
        """
        if session_dir is None:
            # Create new session directory with timestamp
            base_dir = Path(f".data/{tool_name}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = base_dir / timestamp

        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / state_filename
        self.state = self._load_state()

    def _load_state(self) -> PipelineState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json_with_retry(self.state_file)
                logger.info(f"Resumed state from: {self.state_file}")
                logger.info(f"  Stage: {data.get('stage', 'unknown')}")
                logger.info(f"  Iteration: {data.get('iteration', 0)}")
                logger.info(f"  Processed items: {len(data.get('processed_items', []))}")
                return PipelineState(**data)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
                logger.info("Starting fresh pipeline")

        return PipelineState()

    def save(self) -> None:
        """Save current state to file.

        Uses retry logic to handle cloud sync issues (OneDrive, Dropbox, etc.).
        Logs errors but doesn't fail the pipeline if save fails.
        """
        self.state.updated_at = datetime.now().isoformat()

        try:
            state_dict = asdict(self.state)
            write_json_with_retry(state_dict, self.state_file)
            logger.debug(f"State saved to: {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            # Don't fail the pipeline on state save errors

    def update_stage(self, stage: str) -> None:
        """Update pipeline stage and save."""
        old_stage = self.state.stage
        self.state.stage = stage
        logger.info(f"Pipeline stage: {old_stage} → {stage}")
        self.save()

    def increment_iteration(self) -> bool:
        """Increment iteration counter. Returns True if within max iterations."""
        self.state.iteration += 1
        logger.info(f"Iteration {self.state.iteration}/{self.state.max_iterations}")

        if self.state.iteration > self.state.max_iterations:
            logger.warning(f"Exceeded max iterations ({self.state.max_iterations})")
            return False

        self.save()
        return True

    def mark_item_processed(self, item_id: str) -> None:
        """Mark an item as successfully processed."""
        if item_id not in self.state.processed_items:
            self.state.processed_items.append(item_id)

        # Remove from failed if it was there
        self.state.failed_items.pop(item_id, None)
        self.save()

    def mark_item_failed(self, item_id: str, error: str) -> None:
        """Mark an item as failed with error message."""
        self.state.failed_items[item_id] = error
        self.save()

    def is_item_processed(self, item_id: str) -> bool:
        """Check if an item has already been processed."""
        return item_id in self.state.processed_items

    def set_output(self, key: str, value: Any) -> None:
        """Store an output value."""
        self.state.outputs[key] = value
        self.save()

    def get_output(self, key: str, default: Any = None) -> Any:
        """Retrieve an output value."""
        return self.state.outputs.get(key, default)

    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.state.stage == "complete"

    def mark_complete(self) -> None:
        """Mark pipeline as complete."""
        self.update_stage("complete")
        logger.info("✅ Pipeline complete!")

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = PipelineState()
        self.save()
        logger.info("State reset for fresh pipeline run")

    def get_stats(self) -> dict[str, Any]:
        """Get processing statistics."""
        return {
            "stage": self.state.stage,
            "iteration": self.state.iteration,
            "processed": len(self.state.processed_items),
            "failed": len(self.state.failed_items),
            "total": len(self.state.processed_items) + len(self.state.failed_items),
            "session_dir": str(self.session_dir),
        }

    def save_artifact(self, artifact_name: str, content: str, extension: str = ".md") -> Path:
        """Save an artifact to the session directory."""
        artifact_file = self.session_dir / f"{artifact_name}{extension}"
        try:
            artifact_file.write_text(content)
            logger.info(f"Artifact saved to: {artifact_file}")
            return artifact_file
        except Exception as e:
            logger.warning(f"Could not save artifact: {e}")
            raise
