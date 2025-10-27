"""Dependency validation - checks imports against available parent dependencies."""

import ast
import re
import tomllib
from pathlib import Path

from amplifier.utils.logger import get_logger
from rapidfuzz import fuzz

from ..models.generation import ValidationResult

logger = get_logger(__name__)


class DependencyValidator:
    """
    Validates that generated code imports match available parent dependencies.

    Prevents issues where generated code uses libraries not available in the
    parent environment (e.g., using PyPDF2 when only pypdf is available).
    """

    def __init__(self: "DependencyValidator", parent_project_root: Path | None = None):
        """
        Initialize dependency validator.

        Args:
            parent_project_root: Path to parent project root (default: ../../)
        """
        if parent_project_root is None:
            # Default: scenarios/tool_generator -> amplifier root
            parent_project_root = Path(__file__).parent.parent.parent.parent

        self.parent_root = parent_project_root
        self.parent_deps = self._load_parent_dependencies()

    def _load_parent_dependencies(self: "DependencyValidator") -> dict[str, str]:
        """
        Load dependencies from parent pyproject.toml.

        Returns:
            Dict mapping package name to version spec (e.g., {'click': '>=8.0'})
        """
        pyproject_path = self.parent_root / "pyproject.toml"
        if not pyproject_path.exists():
            logger.warning(f"Parent pyproject.toml not found: {pyproject_path}")
            return {}

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            deps = {}

            # Load main dependencies
            for dep_spec in data.get("project", {}).get("dependencies", []):
                # Parse "package>=version" -> {"package": ">=version"}
                name = re.split(r"[><=!]", dep_spec)[0].strip()
                deps[name] = dep_spec

            logger.info(f"Loaded {len(deps)} parent dependencies")
            return deps

        except Exception as e:
            logger.error(f"Failed to load parent dependencies: {e}")
            return {}

    def _extract_imports(self: "DependencyValidator", tool_path: Path) -> set[str]:
        """
        Extract all import statements from Python files in tool.

        Args:
            tool_path: Path to generated tool directory

        Returns:
            Set of imported package names
        """
        imports = set()

        for py_file in tool_path.rglob("*.py"):
            # Skip __pycache__ and .venv
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Get top-level package name
                            package = alias.name.split(".")[0]
                            imports.add(package)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Get top-level package name
                            package = node.module.split(".")[0]
                            imports.add(package)

            except Exception as e:
                logger.warning(f"Failed to parse {py_file}: {e}")

        return imports

    def _find_similar_dependency(
        self: "DependencyValidator", import_name: str, threshold: int = 70
    ) -> str | None:
        """
        Find similar dependency name using fuzzy matching.

        Args:
            import_name: Import name to match (e.g., "PyPDF2")
            threshold: Minimum similarity score (0-100)

        Returns:
            Similar dependency name if found, else None
        """
        best_match = None
        best_score = 0

        for dep_name in self.parent_deps:
            score = fuzz.ratio(import_name.lower(), dep_name.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_match = dep_name

        return best_match

    async def validate(
        self: "DependencyValidator", tool_path: Path
    ) -> ValidationResult:
        """
        Validate that tool imports match available parent dependencies.

        Args:
            tool_path: Path to generated tool directory

        Returns:
            ValidationResult with dependency check results
        """
        logger.info(f"Running dependency validation on {tool_path.name}")

        errors = []
        warnings = []

        # Extract imports from generated code
        imports = self._extract_imports(tool_path)
        logger.info(f"Found {len(imports)} unique imports")

        # Check each import against parent dependencies
        for import_name in sorted(imports):
            # Skip standard library and local imports
            if self._is_standard_library(import_name):
                continue
            if import_name.startswith("amplifier"):
                continue  # Parent package
            if import_name == tool_path.name:
                continue  # Self-import

            # Check if import is available
            if import_name not in self.parent_deps:
                # Try to find similar dependency
                similar = self._find_similar_dependency(import_name)

                if similar:
                    errors.append(
                        f"Import '{import_name}' not available. "
                        f"Did you mean '{similar}'? "
                        f"(Available: {self.parent_deps[similar]})"
                    )
                else:
                    warnings.append(
                        f"Import '{import_name}' not found in parent dependencies. "
                        "Ensure this is a standard library or add to parent pyproject.toml"
                    )

        # Log results
        if errors:
            logger.error(f"Found {len(errors)} dependency errors")
            for error in errors:
                logger.error(f"  - {error}")

        if warnings:
            logger.warning(f"Found {len(warnings)} dependency warnings")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        # Return validation result
        if errors:
            return ValidationResult(
                passed=False,
                stage="dependency",
                errors=errors,
            )

        if not errors and not warnings:
            logger.info("✓ Dependency validation passed")

        return ValidationResult(passed=True, stage="dependency", errors=[])

    def _is_standard_library(self: "DependencyValidator", module_name: str) -> bool:
        """
        Check if module is part of Python standard library.

        Args:
            module_name: Module name to check

        Returns:
            True if standard library module
        """
        # Common standard library modules
        stdlib = {
            "abc",
            "argparse",
            "ast",
            "asyncio",
            "base64",
            "collections",
            "contextlib",
            "copy",
            "csv",
            "dataclasses",
            "datetime",
            "decimal",
            "enum",
            "functools",
            "glob",
            "hashlib",
            "io",
            "itertools",
            "json",
            "logging",
            "math",
            "os",
            "pathlib",
            "pickle",
            "platform",
            "random",
            "re",
            "shutil",
            "socket",
            "sqlite3",
            "string",
            "subprocess",
            "sys",
            "tempfile",
            "textwrap",
            "time",
            "tomllib",
            "traceback",
            "typing",
            "unittest",
            "urllib",
            "uuid",
            "warnings",
            "weakref",
            "xml",
            "zipfile",
        }

        return module_name in stdlib
