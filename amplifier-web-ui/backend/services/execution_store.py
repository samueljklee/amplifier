"""Execution persistence store for web UI."""

import json
from pathlib import Path
from typing import Any, Optional

from models.execution import Execution, ExecutionStatus


class ExecutionStore:
    """Manages persistence of execution metadata and history."""

    def __init__(self, storage_dir: Path | None = None):
        """Initialize execution store.

        Args:
            storage_dir: Directory for execution storage (defaults to .data/web_ui/executions)
        """
        if storage_dir is None:
            # Default to .data/web_ui/executions
            repo_root = Path(__file__).parent.parent.parent.parent
            storage_dir = repo_root / ".data" / "web_ui" / "executions"

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"

        # Load or create index
        self.index = self._load_index()

    def _load_index(self) -> dict[str, Any]:
        """Load execution index from disk."""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except Exception as e:
                print(f"⚠️ Failed to load execution index: {e}")
                return {"recent": [], "total": 0}
        return {"recent": [], "total": 0}

    def _save_index(self):
        """Save execution index to disk."""
        try:
            self.index_file.write_text(json.dumps(self.index, indent=2))
        except Exception as e:
            print(f"⚠️ Failed to save execution index: {e}")

    def save_execution(self, execution: Execution, events: list[Any], session_dir: str | None = None):
        """Save execution metadata to disk.

        Only persists completed executions.

        Args:
            execution: Execution object
            events: List of events from execution
            session_dir: Path to scenario session directory (if exists)
        """
        # Only persist completed executions
        if execution.status != ExecutionStatus.COMPLETED:
            return

        # Find final output from events
        final_output = None
        for event in reversed(events):
            if hasattr(event, "type") and event.type == "file.created":
                metadata = getattr(event, "metadata", None)
                if metadata and not metadata.get("type"):  # Not a draft
                    final_output = {"type": "file", "path": getattr(event, "path", None), "metadata": metadata}
                    break

        # Build metadata
        metadata = {
            "execution_id": execution.id,
            "scenario_id": execution.scenario_id,
            "parameters": execution.parameters,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "session_dir": session_dir,
            "has_rich_state": session_dir is not None,
            "final_output": final_output,
            "event_count": len(events),
        }

        # Save to individual file
        execution_file = self.storage_dir / f"{execution.id}.json"
        try:
            execution_file.write_text(json.dumps(metadata, indent=2))

            # Update index
            self.index["recent"].insert(
                0,
                {
                    "execution_id": execution.id,
                    "scenario_id": execution.scenario_id,
                    "completed_at": metadata["completed_at"],
                    "preview": self._generate_preview(metadata),
                },
            )

            # Keep only last 50
            self.index["recent"] = self.index["recent"][:50]
            self.index["total"] = len(self.index["recent"])

            self._save_index()

            print(f"✅ Persisted execution: {execution.id}")

        except Exception as e:
            print(f"⚠️ Failed to save execution metadata: {e}")

    def _generate_preview(self, metadata: dict[str, Any]) -> str:
        """Generate preview text for execution."""
        scenario = metadata["scenario_id"]
        params = metadata.get("parameters", {})

        # Blog writer preview
        if scenario == "blog_writer":
            idea_content = params.get("idea_content", "")
            if idea_content:
                # Extract first line or title
                first_line = idea_content.strip().split("\n")[0]
                return first_line.replace("#", "").strip()[:100]

        return f"{scenario} execution"

    def load_execution(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Load execution metadata from disk.

        Args:
            execution_id: Execution ID

        Returns:
            Execution metadata or None if not found
        """
        execution_file = self.storage_dir / f"{execution_id}.json"
        if execution_file.exists():
            try:
                return json.loads(execution_file.read_text())
            except Exception as e:
                print(f"⚠️ Failed to load execution {execution_id}: {e}")
                return None
        return None

    def list_executions(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent executions.

        Args:
            limit: Maximum number to return

        Returns:
            List of execution summaries
        """
        return self.index["recent"][:limit]

    def delete_execution(self, execution_id: str) -> bool:
        """Delete execution metadata from disk and index.

        Args:
            execution_id: Execution ID to delete

        Returns:
            True if deleted, False if not found
        """
        execution_file = self.storage_dir / f"{execution_id}.json"

        # Check if file exists
        if not execution_file.exists():
            return False

        try:
            # Delete the file
            execution_file.unlink()

            # Remove from index
            self.index["recent"] = [entry for entry in self.index["recent"] if entry["execution_id"] != execution_id]
            self.index["total"] = len(self.index["recent"])

            # Save updated index
            self._save_index()

            print(f"✅ Deleted execution: {execution_id}")
            return True

        except Exception as e:
            print(f"⚠️ Failed to delete execution {execution_id}: {e}")
            return False

    def reconstruct_events(self, execution_id: str) -> list[dict[str, Any]]:
        """Reconstruct events for an execution.

        Args:
            execution_id: Execution ID

        Returns:
            List of reconstructed events
        """
        metadata = self.load_execution(execution_id)
        if not metadata:
            return []

        # Check if we have rich state to reconstruct from
        if metadata.get("has_rich_state") and metadata.get("session_dir"):
            scenario_id = metadata["scenario_id"]

            if scenario_id == "blog_writer":
                return self._reconstruct_blog_writer_events(metadata)

        # Fallback: minimal reconstruction
        return self._reconstruct_minimal_events(metadata)

    def _reconstruct_blog_writer_events(self, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Reconstruct events from blog_writer state.json."""
        session_dir = metadata.get("session_dir")
        if not session_dir:
            print(f"⚠️ No session_dir in metadata for {metadata.get('execution_id')}")
            return []

        repo_root = Path(__file__).parent.parent.parent.parent
        session_path = repo_root / session_dir
        state_file = session_path / "state.json"

        if not state_file.exists():
            print(f"⚠️ State file not found: {state_file}")
            return []

        try:
            state = json.loads(state_file.read_text())
            events = []

            # Find all draft files by scanning directory
            draft_files = sorted(session_path.glob("draft_iter_*.md"))
            print(f"🔍 Reconstructing {len(draft_files)} drafts from {session_dir}")

            # Create file.created events for each draft
            for draft_file in draft_files:
                # Extract iteration number from filename (draft_iter_0.md -> 0)
                iteration = int(draft_file.stem.split("_")[-1])

                # Read draft to get word count
                draft_content = draft_file.read_text()
                word_count = len(draft_content.split())

                # Get timestamp from iteration_history if available
                timestamp = metadata["started_at"]
                iteration_history = state.get("iteration_history", [])
                if iteration < len(iteration_history):
                    timestamp = iteration_history[iteration].get("timestamp", timestamp)

                events.append(
                    {
                        "type": "file.created",
                        "execution_id": metadata["execution_id"],
                        "path": str(draft_file.relative_to(repo_root)),
                        "metadata": {"type": "draft", "iteration": iteration, "word_count": word_count},
                        "timestamp": timestamp,
                    }
                )

            # Add final output if exists
            if state.get("output_path"):
                word_count = len(state.get("current_draft", "").split())

                events.append(
                    {
                        "type": "file.created",
                        "execution_id": metadata["execution_id"],
                        "path": state["output_path"],
                        "metadata": {"word_count": word_count},  # No type field for final output
                        "timestamp": metadata["completed_at"],
                    }
                )

            # Add completion event
            events.append(
                {
                    "type": "execution.complete",
                    "execution_id": metadata["execution_id"],
                    "status": "completed",
                    "exit_code": 0,
                    "timestamp": metadata["completed_at"],
                }
            )

            return events

        except Exception as e:
            print(f"⚠️ Failed to reconstruct blog_writer events: {e}")
            return []

    def _reconstruct_minimal_events(self, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """Reconstruct minimal events for scenarios without rich state."""
        events = []

        # Add summary log
        events.append(
            {
                "type": "log",
                "execution_id": metadata["execution_id"],
                "level": "info",
                "message": f"Execution completed: {metadata['scenario_id']}",
                "timestamp": metadata["started_at"],
            }
        )

        # Add final output if exists
        if metadata.get("final_output"):
            events.append(
                {
                    "type": "file.created",
                    "execution_id": metadata["execution_id"],
                    "path": metadata["final_output"]["path"],
                    "metadata": metadata["final_output"].get("metadata"),
                    "timestamp": metadata["completed_at"],
                }
            )

        # Add completion
        events.append(
            {
                "type": "execution.complete",
                "execution_id": metadata["execution_id"],
                "status": metadata["status"],
                "exit_code": 0,
                "timestamp": metadata["completed_at"],
            }
        )

        return events
