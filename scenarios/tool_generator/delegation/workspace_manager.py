"""Workspace management for tool generation."""

import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """
    Manages temporary workspaces for tool generation.

    Each workspace contains:
    - task.json: Task specification for Claude Code
    - progress.jsonl: Streaming progress updates
    - result.json: Final generation result
    - <tool_name>/: Generated tool directory
    """

    def __init__(self: "WorkspaceManager", base_dir: Path | None = None) -> None:
        """
        Initialize workspace manager.

        Args:
            base_dir: Base directory for workspaces (default: .data/)
        """
        # Default to .data/ in repo root for temporary workspaces
        if base_dir is None:
            # Find repo root (go up until we find .git or stop at root)
            current = Path.cwd()
            repo_root = current
            while current != current.parent:
                if (current / ".git").exists():
                    repo_root = current
                    break
                current = current.parent
            self.base_dir = repo_root / ".data"
        else:
            self.base_dir = base_dir

        # Handle case where base_dir is a file (e.g., web UI creates output.md)
        if self.base_dir.exists() and self.base_dir.is_file():
            logger.warning(
                f"base_dir is a file, using parent directory: {self.base_dir}"
            )
            self.base_dir = self.base_dir.parent

        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"WorkspaceManager initialized at {self.base_dir}")

    def create_workspace(self: "WorkspaceManager", tool_name: str) -> Path:
        """
        Create new workspace for tool generation.

        Creates workspace at .data/<tool_name>/ (no timestamp, reuses directory)

        Args:
            tool_name: Name of tool being generated

        Returns:
            Path to workspace directory
        """
        # Use .data/<tool_name>/ (no timestamp - reuse directory for iterations)
        workspace = self.base_dir / tool_name

        try:
            workspace.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created workspace: {workspace}")
            return workspace
        except OSError as e:
            logger.error(f"Failed to create workspace {workspace}: {e}")
            raise

    def create_session_workspace(self: "WorkspaceManager", tool_name: str) -> Path:
        """
        Create new session-based workspace with timestamp + GUID.

        Creates: .data/tool_generator/sessions/{timestamp}_{guid}/

        Args:
            tool_name: Name of tool being generated

        Returns:
            Path to session workspace directory
        """
        import json

        # Create session directory with timestamp + short GUID
        base_dir = self.base_dir / "tool_generator" / "sessions"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        guid = uuid.uuid4().hex[:8]  # 8-char GUID for uniqueness
        session_dir = base_dir / f"{timestamp}_{guid}"

        try:
            session_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (session_dir / "references").mkdir(exist_ok=True)
            (session_dir / "logs").mkdir(exist_ok=True)

            # Save session metadata
            metadata = {
                "tool_name": tool_name,
                "created_at": datetime.now().isoformat(),
                "session_id": f"{timestamp}_{guid}",
            }
            (session_dir / "session.json").write_text(json.dumps(metadata, indent=2))

            # Create 'latest' symlink to this session
            latest_link = base_dir / "latest"
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(session_dir.name)

            logger.info(f"Created session workspace: {session_dir}")
            logger.info(f"Updated 'latest' symlink -> {session_dir.name}")
            return session_dir
        except OSError as e:
            logger.error(f"Failed to create session workspace {session_dir}: {e}")
            raise

    def cleanup_workspace(self: "WorkspaceManager", workspace: Path) -> None:
        """
        Remove workspace directory.

        Args:
            workspace: Path to workspace directory
        """
        if not workspace.exists():
            logger.debug(f"Workspace does not exist, skipping cleanup: {workspace}")
            return

        try:
            shutil.rmtree(workspace)
            logger.info(f"Cleaned up workspace: {workspace}")
        except OSError as e:
            logger.error(f"Failed to cleanup workspace {workspace}: {e}")
            raise

    def get_task_file(self: "WorkspaceManager", workspace: Path) -> Path:
        """Get path to task.json in workspace."""
        return workspace / "task.json"

    def get_result_file(self: "WorkspaceManager", workspace: Path) -> Path:
        """Get path to result.json in workspace."""
        return workspace / "result.json"

    def get_progress_file(self: "WorkspaceManager", workspace: Path) -> Path:
        """Get path to progress.jsonl in workspace."""
        return workspace / "progress.jsonl"

    def get_tool_dir(self: "WorkspaceManager", workspace: Path, tool_name: str) -> Path:
        """Get path to generated tool directory in workspace."""
        return workspace / tool_name

    def copy_reference_tools(
        self: "WorkspaceManager", workspace: Path, reference_paths: list[Path]
    ) -> None:
        """
        Copy reference tool directories into workspace for Claude Code access.

        Only copies source code and documentation - excludes:
        - Virtual environments (.venv, venv)
        - Cache directories (__pycache__, .pytest_cache, .mypy_cache)
        - Build artifacts (.egg-info, dist, build)
        - Version control (.git)
        - IDE files (.vscode, .idea)

        Args:
            workspace: Workspace directory
            reference_paths: List of reference tool directories
        """
        ref_dir = workspace / "references"
        ref_dir.mkdir(exist_ok=True)

        # Define ignore patterns - exclude large/unnecessary directories
        def ignore_patterns(directory: str, files: list[str]) -> set[str]:
            """Return set of file/directory names to ignore."""
            ignored = set()
            for name in files:
                # Ignore virtual environments
                if (
                    name in {".venv", "venv", "env"}
                    or name
                    in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
                    or name in {".egg-info", "dist", "build", "*.egg-info"}
                    or name in {".git", ".gitignore"}
                    or name in {".vscode", ".idea", ".DS_Store"}
                    or name.endswith(".pyc")
                    or name.endswith(".pyo")
                ):
                    ignored.add(name)
            return ignored

        for ref_path in reference_paths:
            if not ref_path.exists():
                logger.warning(f"Reference path does not exist: {ref_path}")
                continue

            if not ref_path.is_dir():
                logger.warning(f"Reference path is not a directory: {ref_path}")
                continue

            try:
                dest = ref_dir / ref_path.name
                shutil.copytree(
                    ref_path, dest, ignore=ignore_patterns, dirs_exist_ok=True
                )

                # Count actual files copied (not cache/venv)
                file_count = sum(1 for _ in dest.rglob("*.py")) + sum(
                    1 for _ in dest.rglob("*.md")
                )
                logger.debug(
                    f"Copied reference: {ref_path.name} ({file_count} source files)"
                )
            except OSError as e:
                logger.error(f"Failed to copy reference {ref_path.name}: {e}")
                raise
