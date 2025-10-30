"""
Repository extraction functionality.

Discovers and reads relevant files from the repository.
"""

from pathlib import Path
from typing import Any

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)

# Files and directories to automatically exclude
AUTO_IGNORE = [
    ".venv",
    "venv",
    "node_modules",
    "build",
    "dist",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    ".DS_Store",
]

# Source code file extensions to include
SOURCE_EXTENSIONS = [
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
]

# Documentation file patterns
DOC_PATTERNS = [
    "README*",
    "readme*",
    "*.md",
    "*.rst",
    "*.txt",
    "CONTRIBUTING*",
    "LICENSE*",
    "CHANGELOG*",
]


class RepositoryExtractor:
    """Extracts and filters repository files."""

    def __init__(self):
        """Initialize extractor - stateless, no setup required."""

    async def extract_repository(self, repo_path: Path, session_dir: Path) -> dict[str, Any]:
        """Extract relevant files from repository.

        Args:
            repo_path: Path to repository root
            session_dir: Session directory for storing extracted data

        Returns:
            Dictionary with extracted file information
        """
        # Validate repository path
        if not repo_path.exists() or not repo_path.is_dir():
            logger.error(f"Invalid repository path: {repo_path}")
            return {"source_files": [], "doc_files": [], "structure": {}}

        logger.info(f"Scanning repository: {repo_path}")

        # Discover source files using recursive glob
        source_files = []
        for ext in SOURCE_EXTENSIONS:
            pattern = f"**/*{ext}"
            for file_path in repo_path.glob(pattern):
                if self._should_include(file_path, repo_path):
                    source_files.append(file_path)

        logger.info(f"Found {len(source_files)} source files")

        # Discover documentation files using recursive glob
        doc_files = []
        for pattern in DOC_PATTERNS:
            for file_path in repo_path.glob(f"**/{pattern}"):
                if self._should_include(file_path, repo_path) and file_path not in source_files:
                    doc_files.append(file_path)

        logger.info(f"Found {len(doc_files)} documentation files")

        # Validate minimum inputs
        total_files = len(source_files) + len(doc_files)
        if total_files == 0:
            logger.warning("No files found in repository after filtering")
            return {"source_files": [], "doc_files": [], "structure": {}}

        if total_files < 3:
            logger.warning(f"Only {total_files} files found - may not be sufficient for comprehensive FAQ")

        # Read file contents (limit size for performance)
        source_contents = self._read_files(source_files, max_size_kb=100)
        doc_contents = self._read_files(doc_files, max_size_kb=500)

        # Extract directory structure
        structure = self._extract_structure(repo_path, source_files + doc_files)

        # Save extracted data to session
        extracted_file = session_dir / "extracted_data.txt"
        self._save_extraction_summary(extracted_file, source_files, doc_files, structure)

        return {
            "repo_path": str(repo_path),
            "source_files": source_contents,
            "doc_files": doc_contents,
            "structure": structure,
            "total_files": total_files,
        }

    def _should_include(self, file_path: Path, repo_root: Path) -> bool:
        """Check if file should be included.

        Args:
            file_path: Path to file
            repo_root: Repository root path

        Returns:
            True if file should be included
        """
        try:
            relative = file_path.relative_to(repo_root)
            parts = relative.parts

            # Check if any part matches ignore patterns
            for part in parts:
                for pattern in AUTO_IGNORE:
                    if pattern.startswith("*"):
                        # Handle wildcard patterns
                        if part.endswith(pattern[1:]):
                            return False
                    elif pattern == part:
                        return False

            return True

        except (ValueError, OSError):
            return False

    def _read_files(self, file_paths: list[Path], max_size_kb: int = 100) -> list[dict[str, Any]]:
        """Read file contents with size limit.

        Args:
            file_paths: List of file paths to read
            max_size_kb: Maximum file size in KB to read

        Returns:
            List of file dictionaries with path and content
        """
        contents = []
        max_bytes = max_size_kb * 1024

        for file_path in file_paths:
            try:
                # Check file size
                if file_path.stat().st_size > max_bytes:
                    logger.debug(f"Skipping large file: {file_path.name} (>{max_size_kb}KB)")
                    continue

                # Read content
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                contents.append(
                    {
                        "path": str(file_path),
                        "name": file_path.name,
                        "content": content,
                        "size": len(content),
                    }
                )

            except Exception as e:
                logger.warning(f"Could not read {file_path.name}: {e}")
                continue

        return contents

    def _extract_structure(self, repo_root: Path, file_paths: list[Path]) -> dict[str, Any]:
        """Extract directory structure information.

        Args:
            repo_root: Repository root path
            file_paths: List of included file paths

        Returns:
            Structure dictionary
        """
        structure: dict[str, Any] = {
            "directories": set(),
            "file_types": {},
        }

        for file_path in file_paths:
            try:
                relative = file_path.relative_to(repo_root)

                # Track directories
                if relative.parent != Path("."):
                    structure["directories"].add(str(relative.parent))

                # Track file types
                ext = file_path.suffix or "no_extension"
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1

            except (ValueError, OSError):
                continue

        # Convert set to sorted list
        structure["directories"] = sorted(structure["directories"])

        return structure

    def _save_extraction_summary(
        self,
        output_path: Path,
        source_files: list[Path],
        doc_files: list[Path],
        structure: dict[str, Any],
    ) -> None:
        """Save extraction summary to file.

        Args:
            output_path: Path to save summary
            source_files: List of source file paths
            doc_files: List of documentation file paths
            structure: Directory structure information
        """
        try:
            lines = [
                "# Repository Extraction Summary",
                "",
                f"## Source Files ({len(source_files)})",
                "",
            ]

            for f in sorted(source_files)[:50]:  # Limit to first 50
                lines.append(f"- {f.name}")

            if len(source_files) > 50:
                lines.append(f"... and {len(source_files) - 50} more")

            lines.extend(
                [
                    "",
                    f"## Documentation Files ({len(doc_files)})",
                    "",
                ]
            )

            for f in sorted(doc_files):
                lines.append(f"- {f.name}")

            lines.extend(
                [
                    "",
                    f"## Directory Structure ({len(structure['directories'])} directories)",
                    "",
                ]
            )

            for d in structure["directories"][:20]:  # Limit to first 20
                lines.append(f"- {d}")

            output_path.write_text("\n".join(lines))
            logger.debug(f"Saved extraction summary to {output_path}")

        except Exception as e:
            logger.warning(f"Could not save extraction summary: {e}")
