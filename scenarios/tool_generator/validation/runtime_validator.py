"""Runtime validation - import and execution checks."""

import subprocess
from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models.generation import ValidationResult

logger = get_logger(__name__)


class RuntimeValidator:
    """
    Validates tool can be imported and executed.

    Checks:
    - Python imports work
    - CLI can be invoked (--help)
    - No runtime errors in basic execution
    """

    async def validate(self, tool_path: Path) -> ValidationResult:
        """
        Run runtime validation on generated tool.

        Args:
            tool_path: Path to generated tool directory

        Returns:
            ValidationResult with runtime check results
        """
        logger.info(f"Running runtime validation on {tool_path.name}")

        errors = []

        # 0. Install dependencies first (CRITICAL - must come before imports)
        install_errors = await self._install_dependencies(tool_path)
        errors.extend(install_errors)

        if errors:
            return ValidationResult(
                passed=False,
                stage="runtime",
                errors=errors,
            )

        # 1. Test imports
        import_errors = await self._test_imports(tool_path)
        errors.extend(import_errors)

        if errors:
            return ValidationResult(passed=False, stage="runtime", errors=errors)

        # 2. Test CLI execution
        cli_errors = await self._test_cli(tool_path)
        errors.extend(cli_errors)

        if errors:
            return ValidationResult(passed=False, stage="runtime", errors=errors)

        logger.info("✓ Runtime validation passed")
        return ValidationResult(passed=True, stage="runtime", errors=[])

    async def _install_dependencies(self, tool_path: Path) -> list[str]:
        """
        Install tool dependencies using uv sync.

        This MUST run before import/CLI tests to ensure all dependencies are available.
        """
        errors = []

        # Check for pyproject.toml
        pyproject = tool_path / "pyproject.toml"
        if not pyproject.exists():
            errors.append(
                f"pyproject.toml not found at {tool_path} - cannot install dependencies"
            )
            return errors

        logger.info(f"Installing dependencies for {tool_path.name}")

        try:
            result = subprocess.run(
                ["uv", "sync"],
                capture_output=True,
                text=True,
                cwd=tool_path,
                timeout=120,  # 2 minutes for dependency resolution
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                errors.append(f"Dependency installation failed: {error_msg}")
                logger.error(f"uv sync failed: {error_msg}")
            else:
                logger.info("✓ Dependencies installed successfully")
                # Log what was installed for debugging
                if "Resolved" in result.stdout or "Installed" in result.stdout:
                    logger.debug(f"uv sync output: {result.stdout[:500]}")
        except subprocess.TimeoutExpired:
            errors.append("Dependency installation timed out after 120 seconds")
            logger.error("uv sync timed out")
        except FileNotFoundError:
            errors.append("uv command not found - ensure uv is installed and in PATH")
            logger.error("uv command not found")
        except Exception as e:
            errors.append(f"Dependency installation failed with exception: {str(e)}")
            logger.error(f"uv sync exception: {e}")

        return errors

    async def _test_imports(self, tool_path: Path) -> list[str]:
        """Test that tool can be imported."""
        errors = []

        # Find main module name
        main_py = tool_path / "main.py"
        if not main_py.exists():
            errors.append("main.py not found")
            return errors

        # Try to import the tool
        module_name = tool_path.name
        try:
            result = subprocess.run(
                [
                    "python",
                    "-c",
                    f"import sys; sys.path.insert(0, '{tool_path.parent}'); import {module_name}.main",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                errors.append(f"Import failed: {error_msg}")
                logger.error(f"Import test failed: {error_msg}")
            else:
                logger.debug("Import test passed")
        except subprocess.TimeoutExpired:
            errors.append("Import test timed out after 30 seconds")
            logger.error("Import test timed out")
        except Exception as e:
            errors.append(f"Import test failed with exception: {str(e)}")
            logger.error(f"Import test exception: {e}")

        return errors

    async def _test_cli(self, tool_path: Path) -> list[str]:
        """Test that CLI can be invoked."""
        errors = []

        # Try --help flag
        try:
            result = subprocess.run(
                ["python", "-m", tool_path.name, "--help"],
                capture_output=True,
                text=True,
                cwd=tool_path.parent,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                errors.append(f"CLI execution failed: {error_msg}")
                logger.error(f"CLI test failed: {error_msg}")
            else:
                logger.debug("CLI test passed")
        except subprocess.TimeoutExpired:
            errors.append("CLI test timed out after 30 seconds")
            logger.error("CLI test timed out")
        except Exception as e:
            errors.append(f"CLI test failed with exception: {str(e)}")
            logger.error(f"CLI test exception: {e}")

        return errors
