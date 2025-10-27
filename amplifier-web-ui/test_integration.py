#!/usr/bin/env python3
"""Integration test for scenario generation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.generation_session import GenerationSessionManager


async def test_full_workflow():
    """Test complete generation workflow."""
    print("=== Integration Test: Full Generation Workflow ===\n")

    # Create manager
    manager = GenerationSessionManager()
    print("✅ Manager created\n")

    # Create session
    print("1. Creating session...")
    session = manager.create_session(
        description="A tool to summarize long documents into key points", name="document_summarizer"
    )
    print(f"   ✅ Session: {session.session_id}")
    print(f"   📝 Scenario: {session.scenario_name}\n")

    # Run full generation
    print("2. Running full generation pipeline...")
    await session.run_full_generation()

    # Check state
    state = session.get_state()
    print(f"   Status: {state.status.value}")

    if state.status.value != "complete":
        print("   ❌ Generation failed!")
        if state.error:
            print(f"   Error: {state.error}")
        return 1

    print("   ✅ Generation complete!\n")

    # Verify files
    print("3. Verifying generated files...")
    files = session.get_files()
    print(f"   Files: {len(files)}")

    expected_files = ["__init__.py", "__main__.py", "README.md", "state.py", "main.py"]
    for expected in expected_files:
        if expected in files:
            print(f"   ✅ {expected}")
        else:
            print(f"   ❌ Missing: {expected}")
            return 1

    print("")

    # Verify spec
    print("4. Verifying spec...")
    if state.spec_json:
        print(f"   ✅ Name: {state.spec_json['name']}")
        print(f"   ✅ Workflow: {state.spec_json['workflow_type']}")
        print(f"   ✅ Stages: {len(state.spec_json['stages'])}")
        print(f"   ✅ Inputs: {len(state.spec_json['inputs'])}")
        print(f"   ✅ Outputs: {len(state.spec_json['outputs'])}")
    else:
        print("   ❌ No spec generated")
        return 1

    print("")

    # Verify events
    print("5. Verifying events...")
    events = session.get_events()
    print(f"   Total events: {len(events)}")

    expected_event_types = ["spec.generating", "spec.ready", "code.generating", "code.generated", "validation.started"]
    for event_type in expected_event_types:
        found = any(e.type == event_type for e in events)
        if found:
            print(f"   ✅ {event_type}")
        else:
            print(f"   ❌ Missing event: {event_type}")

    print("")

    # Test session reload
    print("6. Testing session reload...")
    loaded_session = manager.get_session(session.session_id)
    if loaded_session:
        print("   ✅ Session reloaded")
        print(f"   Status: {loaded_session.state.status.value}")
    else:
        print("   ❌ Failed to reload session")
        return 1

    print("")
    print("=== All Integration Tests Passed ===")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_full_workflow())
    sys.exit(exit_code)
