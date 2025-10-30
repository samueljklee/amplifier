"""
State Management Module for Research Assistant

Handles pipeline state persistence with resume capability.
Saves state after every operation to enable interruption recovery.
"""

import uuid
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineState:
    """Research assistant pipeline state."""

    # Session info
    session_dir: Path

    # Phase tracking
    current_phase: str = "initialized"
    completed_phases: list[str] = field(default_factory=list)

    # Research configuration
    research_question_input: str | None = None
    research_question: str | None = None
    research_type: str | None = None
    researcher_persona: str | None = None
    research_depth: str | None = None
    output_format: str | None = None
    max_iterations: int = 10

    # Phase completion flags
    requirements_clarified: bool = False

    # Phase outputs
    preliminary_sources: list[dict] = field(default_factory=list)
    verified_facts: list[dict] = field(default_factory=list)
    themes: list[dict] = field(default_factory=list)
    reviewed_themes: list[dict] = field(default_factory=list)
    web_research: list[dict] = field(default_factory=list)
    draft: str | None = None
    final_output: str | None = None
    output_path: str | None = None

    # Metadata
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Path to string
        data["session_dir"] = str(self.session_dir)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineState":
        """Create from dictionary."""
        # Convert string back to Path
        if "session_dir" in data:
            data["session_dir"] = Path(data["session_dir"])
        return cls(**data)


class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Existing session directory to resume, or None for new session
        """
        if session_dir is None:
            # Create new session
            base_dir = Path(".data/research_assistant/sessions")
            base_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            guid = uuid.uuid4().hex[:8]
            session_dir = base_dir / f"{timestamp}_{guid}"
            session_dir.mkdir(parents=True, exist_ok=True)

            # Create 'latest' symlink
            latest_link = base_dir / "latest"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(session_dir.name)

            logger.info(f"Created new session: {session_dir}")

            # Initialize new state
            self.state = PipelineState(session_dir=session_dir)
            self.state_file = self.state.session_dir / "state.json"
            self.save()
        else:
            # Resume existing session
            session_dir = Path(session_dir)
            if not session_dir.exists():
                raise ValueError(f"Session directory not found: {session_dir}")

            state_file = session_dir / "state.json"
            if not state_file.exists():
                raise ValueError(f"State file not found: {state_file}")

            logger.info(f"Resuming session: {session_dir}")
            data = read_json_with_retry(state_file)
            self.state = PipelineState.from_dict(data)
            self.state_file = self.state.session_dir / "state.json"

    @property
    def session_dir(self) -> Path:
        """Get session directory path."""
        return self.state.session_dir

    def save(self) -> None:
        """Save current state to disk."""
        self.state.updated_at = datetime.now().isoformat()
        write_json_with_retry(self.state.to_dict(), self.state_file)

    def update_phase(self, phase: str) -> None:
        """Update current phase and save."""
        self.state.current_phase = phase
        if phase not in self.state.completed_phases:
            self.state.completed_phases.append(phase)
        self.save()
        logger.info(f"Phase updated: {phase}")

    def set_clarified_query(self, query: str) -> None:
        """Save clarified query."""
        self.state.research_question = query
        self.save()

    def add_preliminary_sources(self, sources: list[dict]) -> None:
        """Add preliminary research sources."""
        self.state.preliminary_sources.extend(sources)
        self.save()

    def add_verified_facts(self, facts: list[dict]) -> None:
        """Add verified facts."""
        self.state.verified_facts.extend(facts)
        self.save()

    def set_themes(self, themes: list[dict]) -> None:
        """Save extracted themes."""
        self.state.themes = themes
        self.save()

    def set_reviewed_themes(self, themes: list[dict]) -> None:
        """Save reviewed themes."""
        self.state.reviewed_themes = themes
        self.save()

    def add_web_research(self, research: list[dict]) -> None:
        """Add web research results."""
        self.state.web_research.extend(research)
        self.save()

    def set_draft(self, draft: str) -> None:
        """Save draft report."""
        self.state.draft = draft
        self.save()

    def set_final_report(self, report: str) -> None:
        """Save final report."""
        self.state.final_output = report
        self.save()

    def save_artifact(self, filename: str, content: str) -> Path:
        """Save an artifact file and return its path."""
        artifact_path = self.state.session_dir / filename
        artifact_path.write_text(content, encoding="utf-8")
        logger.file_created(str(artifact_path), {"type": "artifact", "phase": self.state.current_phase})
        return artifact_path

    def get_artifact_path(self, filename: str) -> Path:
        """Get path for an artifact file."""
        return self.state.session_dir / filename
