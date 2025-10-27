#!/usr/bin/env python3
"""Test script for scenario generation API."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.generation_session import GenerationSession


async def test_generation():
    """Test the generation session."""
    print("=== Testing Scenario Generation ===\n")

    # Create a session
    print("1. Creating generation session...")
    session = GenerationSession(
        session_id="test-001", description="A tool to convert markdown files to HTML", scenario_name="markdown_to_html"
    )
    print(f"   ✅ Session created: {session.session_id}")
    print(f"   📝 Scenario: {session.scenario_name}")

    # Generate spec
    print("\n2. Generating specification...")
    await session.generate_spec()
    print("   ✅ Spec generated")
    print(f"   Status: {session.state.status.value}")

    # Print spec
    if session.state.spec_json:
        print("\n   Generated Spec:")
        print(f"   - Name: {session.state.spec_json['name']}")
        print(f"   - Workflow: {session.state.spec_json['workflow_type']}")
        print(f"   - Stages: {len(session.state.spec_json['stages'])}")

    # Generate code
    print("\n3. Generating code...")
    await session.generate_code()
    print("   ✅ Code generated")
    print(f"   Files: {len(session.state.generated_files or {})}")

    if session.state.generated_files:
        print("\n   Generated Files:")
        for filename in list(session.state.generated_files.keys())[:5]:
            print(f"   - {filename}")

    # Validate
    print("\n4. Validating generated code...")
    await session.validate()
    print(f"   Status: {session.state.status.value}")

    if session.state.validation_results:
        print("\n   Validation Results:")
        for result in session.state.validation_results:
            status = "✅" if result["passed"] else "❌"
            print(f"   {status} {result['stage']}: {result['message']}")

    # Check final state
    print("\n5. Final State:")
    print(f"   Status: {session.state.status.value}")
    print(f"   Output dir: {session.output_dir}")

    # Print events
    print("\n6. Events:")
    for event in session.get_events():
        print(f"   - {event.type}: {event.message}")

    print("\n=== Test Complete ===")

    if session.state.status.value == "complete":
        print("✅ Generation succeeded!")
        return 0
    else:
        print("❌ Generation failed!")
        if session.state.error:
            print(f"   Error: {session.state.error}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_generation())
    sys.exit(exit_code)
