#!/usr/bin/env python3
"""
Validate Generated Scenarios

Runs validation pipeline on all generated scenarios.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.validation_pipeline import ValidationPipeline


def main() -> None:
    """Validate all generated scenarios."""
    base_dir = Path(__file__).parent.parent.parent.parent / "scenarios" / "_test_generated"

    if not base_dir.exists():
        print(f"❌ Generated scenarios directory not found: {base_dir}")
        sys.exit(1)

    scenarios = [d for d in base_dir.iterdir() if d.is_dir()]

    if not scenarios:
        print(f"❌ No generated scenarios found in: {base_dir}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"Validating {len(scenarios)} Generated Scenarios")
    print(f"{'=' * 60}\n")

    all_passed = True

    for scenario_dir in sorted(scenarios):
        print(f"\n--- {scenario_dir.name} ---\n")

        validator = ValidationPipeline(scenario_dir)
        passed = validator.validate_all()
        validator.print_results()

        if not passed:
            all_passed = False

    print(f"\n{'=' * 60}")
    if all_passed:
        print("✅ ALL SCENARIOS PASSED VALIDATION")
    else:
        print("❌ SOME SCENARIOS FAILED VALIDATION")
    print(f"{'=' * 60}\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
