"""
Validation Pipeline

Multi-stage validation for generated scenarios.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any


class ValidationResult:
    """Result of a validation stage."""

    def __init__(
        self: "ValidationResult", stage: str, passed: bool, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize validation result.

        Args:
            stage: Validation stage name
            passed: Whether validation passed
            message: Result message
            details: Optional additional details
        """
        self.stage = stage
        self.passed = passed
        self.message = message
        self.details = details or {}


class ValidationPipeline:
    """Multi-stage validation for generated scenarios."""

    def __init__(self: "ValidationPipeline", scenario_dir: Path) -> None:
        """Initialize validation pipeline.

        Args:
            scenario_dir: Path to generated scenario directory
        """
        self.scenario_dir = scenario_dir
        self.results: list[ValidationResult] = []

    def validate_all(self: "ValidationPipeline") -> bool:
        """Run all validation stages.

        Returns:
            True if all validations pass
        """
        self.results = []

        self.results.append(self._validate_structure())
        self.results.append(self._validate_imports())
        self.results.append(self._validate_syntax())

        return all(r.passed for r in self.results)

    def _validate_structure(self: "ValidationPipeline") -> ValidationResult:
        """Validate directory structure."""
        required_files = ["__init__.py", "__main__.py", "main.py", "state.py", "README.md"]

        missing = []
        for file in required_files:
            if not (self.scenario_dir / file).exists():
                missing.append(file)

        if missing:
            return ValidationResult(
                stage="structure",
                passed=False,
                message=f"Missing required files: {', '.join(missing)}",
                details={"missing_files": missing},
            )

        return ValidationResult(stage="structure", passed=True, message="All required files present")

    def _validate_imports(self: "ValidationPipeline") -> ValidationResult:
        """Validate Python imports can be resolved."""
        python_files = list(self.scenario_dir.rglob("*.py"))

        for py_file in python_files:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)], capture_output=True, text=True, timeout=10
                )

                if result.returncode != 0:
                    return ValidationResult(
                        stage="imports",
                        passed=False,
                        message=f"Import error in {py_file.name}",
                        details={"file": str(py_file), "error": result.stderr},
                    )

            except Exception as e:
                return ValidationResult(
                    stage="imports",
                    passed=False,
                    message=f"Failed to validate {py_file.name}: {e}",
                    details={"file": str(py_file)},
                )

        return ValidationResult(stage="imports", passed=True, message="All imports valid")

    def _validate_syntax(self: "ValidationPipeline") -> ValidationResult:
        """Validate Python syntax."""
        python_files = list(self.scenario_dir.rglob("*.py"))

        for py_file in python_files:
            try:
                content = py_file.read_text()
                compile(content, str(py_file), "exec")

            except SyntaxError as e:
                return ValidationResult(
                    stage="syntax",
                    passed=False,
                    message=f"Syntax error in {py_file.name}: {e}",
                    details={"file": str(py_file), "line": e.lineno},
                )

        return ValidationResult(stage="syntax", passed=True, message="All Python syntax valid")

    def print_results(self: "ValidationPipeline") -> None:
        """Print validation results."""
        print("\n=== Validation Results ===\n")

        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.stage}: {result.message}")

            if result.details:
                for key, value in result.details.items():
                    print(f"  {key}: {value}")

        overall = "✅ ALL CHECKS PASSED" if all(r.passed for r in self.results) else "❌ VALIDATION FAILED"
        print(f"\n{overall}\n")
