#!/usr/bin/env python3
"""
Test CLI for Scenario Generator

Usage:
    python test_generator.py "Email to action items extractor"
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.backend_generator import BackendGenerator
from generators.spec_generator import SpecGenerator
from generators.validation_pipeline import ValidationPipeline


async def test_generation(description: str, output_name: str) -> bool:
    """Test the full generation pipeline.

    Args:
        description: What the scenario should do
        output_name: Directory name for output

    Returns:
        True if validation passed, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"Generating: {description}")
    print(f"{'=' * 60}\n")

    output_dir = Path(__file__).parent.parent.parent.parent / "scenarios" / "_test_generated" / output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print("1️⃣ Generating specification...")
    spec_gen = SpecGenerator()
    spec = await spec_gen.generate_spec(description)

    print(f"\n✅ Generated spec: {spec.display_name}")
    print(f"   Type: {spec.workflow_type.value}")
    print(f"   Stages: {len(spec.stages)}")
    print(f"   Inputs: {len(spec.inputs)}")
    print(f"   Outputs: {len(spec.outputs)}")

    spec_path = output_dir / "spec.json"
    spec_path.write_text(spec.model_dump_json())
    print(f"\n💾 Saved spec to: {spec_path}")

    print("\n2️⃣ Generating backend code...")
    backend_gen = BackendGenerator()
    files = await backend_gen.generate_code(spec, output_dir)

    print(f"\n✅ Generated {len(files)} files:")
    for file_path in sorted(files.keys()):
        print(f"   - {file_path}")

    print("\n3️⃣ Running validation...")
    validator = ValidationPipeline(output_dir)
    passed = validator.validate_all()

    validator.print_results()

    if passed:
        print(f"🎉 SUCCESS! Scenario generated at:\n   {output_dir}")
    else:
        print(f"❌ Validation failed. Check output at:\n   {output_dir}")

    return passed


async def main() -> None:
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python test_generator.py <description> [output_name]")
        print("\nExamples:")
        print('  python test_generator.py "Extract action items from emails"')
        print('  python test_generator.py "Generate report from data" report_gen')
        sys.exit(1)

    description = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "test_scenario"

    success = await test_generation(description, output_name)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
