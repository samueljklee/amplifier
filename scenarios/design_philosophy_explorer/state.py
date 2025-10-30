"""
State Management Module

Handles pipeline state persistence for resume capability.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry, write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineState:
    """Complete pipeline state for persistence."""

    # Current pipeline stage
    stage: str = "initialized"

    # Inputs
    question: str | None = None
    directory: str | None = None
    output_path: str | None = None

    # Module outputs
    exploration: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] | None = None
    critique: dict[str, Any] = field(default_factory=dict)
    report_path: str | None = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Path to session directory
        """
        if session_dir is None:
            # Create session directory with timestamp + GUID
            base_dir = Path(".data/design_philosophy_explorer/sessions")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            guid = uuid.uuid4().hex[:8]
            session_dir = base_dir / f"{timestamp}_{guid}"

        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self.state = self._load_state()

        # Create 'latest' symlink for easy resume
        latest_link = self.session_dir.parent / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(self.session_dir.name)

    def _load_state(self) -> PipelineState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json_with_retry(self.state_file)
                logger.info(f"Resumed state from: {self.state_file}")
                logger.info(f"  Stage: {data.get('stage', 'unknown')}")
                return PipelineState(**data)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
                logger.info("Starting fresh exploration")

        return PipelineState()

    def save(self) -> None:
        """Save current state to file."""
        self.state.updated_at = datetime.now().isoformat()

        try:
            state_dict = asdict(self.state)
            write_json_with_retry(state_dict, self.state_file)
            logger.debug(f"State saved to: {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def update_stage(self, stage: str) -> None:
        """Update pipeline stage and save."""
        old_stage = self.state.stage
        self.state.stage = stage
        logger.info(f"Pipeline stage: {old_stage} → {stage}")
        self.save()

    def set_exploration(self, exploration: dict[str, Any]) -> None:
        """Save philosophy exploration results."""
        self.state.exploration = exploration
        self.save()

    def set_analysis(self, analysis: dict[str, Any]) -> None:
        """Save directory analysis results."""
        self.state.analysis = analysis
        self.save()

    def set_critique(self, critique: dict[str, Any]) -> None:
        """Save critique and suggestions."""
        self.state.critique = critique
        self.save()

    def set_report_path(self, path: str) -> None:
        """Save report output path."""
        self.state.report_path = path
        self.save()

    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.state.stage == "complete"

    def mark_complete(self) -> None:
        """Mark pipeline as complete."""
        self.update_stage("complete")
        logger.info("✅ Exploration complete!")

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = PipelineState()
        self.save()
        logger.info("State reset for fresh exploration")
