"""Static validation - linting and type checking."""

import subprocess
from pathlib import Path

from amplifier.utils.logger import get_logger

from ..models.generation import ValidationResult

logger = get_logger(__name__)


class StaticValidator:
    """
    Validates tool passes static checks.

    Runs:
    - ruff format --check
    - ruff check
    - pyright
    """

    async def validate(self, tool_path: Path) -> ValidationResult:
        """
        Run static validation on generated tool.

        Runs checks directly on the tool (no Makefile needed):
        - ruff format --check
        - ruff check
        - pyright

        Args:
            tool_path: Path to generated tool directory

        Returns:
            ValidationResult with static check results
        """
        logger.info(f"Running static validation on {tool_path.name}")

        errors = []

        # Define checks to run (in order)
        checks = [
            (["uv", "run", "ruff", "format", "--check", "."], "format check"),
            (["uv", "run", "ruff", "check", "."], "linting"),
            (["uv", "run", "pyright", "."], "type checking"),
        ]

        # Run each check
        for cmd, check_name in checks:
            logger.info(f"Running {check_name}...")
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=tool_path,
                    timeout=120,  # 2 minutes per check (generous for pyright)
                )

                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip()

                    # Filter out benign pyright warnings about VIRTUAL_ENV mismatch
                    if (
                        check_name == "type checking"
                        and "VIRTUAL_ENV" in error_msg
                        and "does not match" in error_msg
                    ):
                        logger.debug("Ignoring pyright VIRTUAL_ENV mismatch warning")
                        logger.debug(f"✓ {check_name} passed (warning ignored)")
                        continue

                    errors.append(f"{check_name} failed: {error_msg}")
                    logger.error(f"{check_name} failed:\n{error_msg}")
                else:
                    logger.debug(f"✓ {check_name} passed")

            except subprocess.TimeoutExpired:
                errors.append(f"{check_name} timed out after 120 seconds")
                logger.error(f"{check_name} timed out")
            except FileNotFoundError:
                errors.append(
                    f"{check_name} failed: command not found (check PATH and dependencies)"
                )
                logger.error(f"{check_name} command not found")
            except Exception as e:
                errors.append(f"{check_name} failed with exception: {str(e)}")
                logger.error(f"{check_name} exception: {e}")

        # Return results
        if errors:
            return ValidationResult(
                passed=False,
                stage="static",
                errors=errors,
            )

        logger.info("✓ Static validation passed")
        return ValidationResult(passed=True, stage="static", errors=[])
