"""Code file scanner and language identifier."""

from pathlib import Path

from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.logger import LogFormat

logger = ToolkitLogger(name="scanner", format=LogFormat.PLAIN)


class CodeScanner:
    """Discovers and identifies code files."""

    # Mapping of file extensions to programming languages
    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".hpp": "C++",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".m": "Objective-C",
        ".r": "R",
        ".jl": "Julia",
        ".sh": "Shell",
        ".bash": "Bash",
    }

    async def discover_files(self, directory: Path) -> list[dict]:
        """Discover all code files in directory recursively.

        Args:
            directory: Root directory to scan

        Returns:
            List of file dictionaries with path, language, and size info
        """
        files = []

        # Use recursive glob patterns for all supported extensions
        for ext, language in self.LANGUAGE_EXTENSIONS.items():
            pattern = f"**/*{ext}"
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    try:
                        # Get file size and basic stats
                        size_bytes = file_path.stat().st_size

                        # Skip very large files (>1MB)
                        if size_bytes > 1_000_000:
                            logger.info(f"Skipping large file: {file_path.name} ({size_bytes} bytes)")
                            continue

                        # Count lines
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            lines = len(content.splitlines())
                        except (UnicodeDecodeError, PermissionError):
                            logger.info(f"Skipping unreadable file: {file_path}")
                            continue

                        files.append(
                            {
                                "path": str(file_path),
                                "name": file_path.name,
                                "language": language,
                                "extension": ext,
                                "size_bytes": size_bytes,
                                "lines": lines,
                                "relative_path": str(file_path.relative_to(directory)),
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        continue

        # Sort by relative path for consistent ordering
        files.sort(key=lambda f: f["relative_path"])

        # Log summary by language
        languages = {}
        for f in files:
            lang = f["language"]
            languages[lang] = languages.get(lang, 0) + 1

        logger.info(f"Discovered {len(files)} code files:")
        for lang, count in sorted(languages.items()):
            logger.info(f"  {lang}: {count} files")

        return files

    def identify_language(self, file_path: Path) -> str | None:
        """Identify programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if unknown
        """
        ext = file_path.suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(ext)
