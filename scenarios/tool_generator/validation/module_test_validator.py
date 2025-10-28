"""Module-level testing validator.

Tests each module with realistic inputs to ensure functionality works end-to-end.
"""

import subprocess
import sys
from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models.generation import ValidationResult

logger = get_logger(__name__)


class ModuleTestValidator:
    """
    Validates tool modules work correctly with real inputs.

    Tests each module's core functionality:
    - Imports work correctly
    - Public API functions exist and are callable
    - Modules handle valid inputs without crashing
    - Modules handle invalid inputs gracefully
    - LLM-using modules return expected data structures
    """

    async def validate(self, tool_path: Path) -> ValidationResult:
        """
        Run module-level tests on generated tool.

        Args:
            tool_path: Path to generated tool directory

        Returns:
            ValidationResult with module test results
        """
        logger.info(f"Running module tests on {tool_path.name}")

        errors = []

        # 1. Find test file
        test_file = tool_path / "tests" / "test_modules.py"
        if not test_file.exists():
            # Not an error - tests are optional but recommended
            logger.info("No module tests found (tests/test_modules.py)")
            return ValidationResult(
                passed=True,
                stage="module_tests",
                errors=[],
                warnings=[
                    "No module tests found - consider adding tests/test_modules.py"
                ],
            )

        # 2. Run pytest on test file
        test_errors = await self._run_pytest(tool_path, test_file)
        errors.extend(test_errors)

        if errors:
            logger.error(f"Module tests failed with {len(errors)} error(s)")
            return ValidationResult(passed=False, stage="module_tests", errors=errors)

        logger.info("✓ Module tests passed")
        return ValidationResult(passed=True, stage="module_tests", errors=[])

    async def _run_pytest(self, tool_path: Path, test_file: Path) -> list[str]:
        """Run pytest on the test file."""
        errors = []

        logger.info(f"Running pytest: {test_file.relative_to(tool_path)}")

        try:
            # Run pytest with verbose output
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(test_file),
                    "-v",  # Verbose
                    "--tb=short",  # Short traceback
                    "--no-header",  # Skip header
                ],
                capture_output=True,
                text=True,
                cwd=tool_path,
                timeout=60,  # 1 minute for all module tests
            )

            if result.returncode != 0:
                # Parse pytest output for specific failures
                output = result.stdout + "\n" + result.stderr

                # Extract test failures
                if "FAILED" in output:
                    errors.append("Module tests failed (see details below)")
                    # Add first 20 lines of output for context
                    lines = output.split("\n")[:20]
                    errors.append("\n".join(lines))
                else:
                    errors.append(f"pytest exited with code {result.returncode}")
                    errors.append(output[:500])  # First 500 chars

                logger.error(f"pytest failed: {result.returncode}")
            else:
                logger.debug("pytest passed")

        except subprocess.TimeoutExpired:
            errors.append("Module tests timed out after 60 seconds")
            logger.error("pytest timed out")
        except FileNotFoundError:
            errors.append(
                "pytest not found - ensure pytest is installed (add to dependencies)"
            )
            logger.error("pytest command not found")
        except Exception as e:
            errors.append(f"pytest failed with exception: {str(e)}")
            logger.error(f"pytest exception: {e}")

        return errors
