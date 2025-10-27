#!/usr/bin/env python3
"""
Test script for interactive prompt functionality.

This script validates the interactive prompt response endpoint by:
1. Creating a test scenario that emits an interactive prompt
2. Monitoring for the prompt event
3. Submitting a response via the API endpoint
4. Validating the response was received by the scenario

Usage:
    # Start the backend server first
    cd backend && uv run uvicorn api.main:app --reload --port 8000

    # In another terminal, run this test
    python test_interactive_prompt.py
"""

import asyncio
import json
import sys
import time

import httpx


class InteractivePromptTester:
    """Test interactive prompt functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize tester.

        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def create_test_execution(self) -> str:
        """Create a test execution with blog_writer scenario.

        Returns:
            Execution ID
        """
        print("\n📋 Step 1: Creating test execution with blog_writer scenario...")

        # Use minimal test data
        test_idea = """
# Test Blog Post Idea

This is a simple test to validate interactive prompts.
We want to write a short blog post about testing.
"""

        test_writing = """
# Sample Writing

This is my writing style. I like to keep things simple and clear.
Testing is important for quality software.
"""

        response = await self.client.post(
            f"{self.base_url}/api/scenarios/blog_writer/execute",
            json={
                "parameters": {
                    "idea": "__INLINE__",
                    "idea_content": test_idea,
                    "writings_dir": "__INLINE__",
                    "writings_dir_files": [
                        {"content": test_writing, "filename": "sample1.md"},
                        {"content": test_writing, "filename": "sample2.md"},
                        {"content": test_writing, "filename": "sample3.md"},
                    ],
                }
            },
        )

        if response.status_code != 200:
            print(f"❌ Failed to create execution: {response.status_code}")
            print(response.text)
            sys.exit(1)

        data = response.json()
        execution_id = data["execution_id"]
        print(f"✅ Execution created: {execution_id}")
        return execution_id

    async def monitor_for_prompt(self, execution_id: str, timeout: int = 120) -> dict | None:
        """Monitor execution events for interactive prompt.

        Args:
            execution_id: Execution ID to monitor
            timeout: Maximum seconds to wait

        Returns:
            Prompt event data or None if timeout
        """
        print(f"\n📡 Step 2: Monitoring for interactive prompt (timeout: {timeout}s)...")

        start_time = time.time()

        async with self.client.stream("GET", f"{self.base_url}/api/ws/executions/{execution_id}") as stream:
            async for line in stream.aiter_lines():
                if time.time() - start_time > timeout:
                    print("⏱️ Timeout waiting for prompt")
                    return None

                try:
                    event = json.loads(line)
                    event_type = event.get("type")

                    # Show progress
                    if event_type == "stage.transition":
                        stage = event.get("to_stage", "unknown")
                        print(f"   🔄 Stage: {stage}")
                    elif event_type == "log":
                        message = event.get("message", "")
                        if "error" in message.lower() or "fail" in message.lower():
                            print(f"   ⚠️  {message[:80]}")

                    # Found the prompt!
                    if event_type == "interactive.prompt":
                        print("✅ Interactive prompt detected!")
                        print(f"   Prompt: {event.get('prompt_text')}")
                        print(f"   Options: {event.get('prompt_options')}")
                        print(f"   Type: {event.get('prompt_type')}")
                        return event

                    # Check if execution completed without prompt
                    if event_type == "execution.complete":
                        print("⚠️  Execution completed without showing prompt")
                        return None

                    if event_type == "execution.error":
                        print(f"❌ Execution error: {event.get('error')}")
                        return None

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing event: {e}")
                    continue

        return None

    async def submit_response(self, execution_id: str, response: str) -> bool:
        """Submit response to interactive prompt.

        Args:
            execution_id: Execution ID
            response: Response text

        Returns:
            True if successful
        """
        print(f"\n📤 Step 3: Submitting response '{response}'...")

        try:
            result = await self.client.post(
                f"{self.base_url}/api/executions/{execution_id}/respond",
                json={"response": response},
            )

            if result.status_code == 200:
                print("✅ Response submitted successfully")
                return True
            else:
                print(f"❌ Failed to submit response: {result.status_code}")
                print(result.text)
                return False

        except Exception as e:
            print(f"❌ Error submitting response: {e}")
            return False

    async def verify_continuation(self, execution_id: str, timeout: int = 60) -> bool:
        """Verify that execution continued after response.

        Args:
            execution_id: Execution ID
            timeout: Maximum seconds to wait

        Returns:
            True if execution continued
        """
        print("\n🔍 Step 4: Verifying execution continuation...")

        start_time = time.time()

        async with self.client.stream("GET", f"{self.base_url}/api/ws/executions/{execution_id}") as stream:
            async for line in stream.aiter_lines():
                if time.time() - start_time > timeout:
                    print("⏱️ Timeout waiting for continuation")
                    return False

                try:
                    event = json.loads(line)
                    event_type = event.get("type")

                    # Show progress
                    if event_type == "log":
                        message = event.get("message", "")
                        if "response submitted" in message.lower():
                            print(f"   ✅ {message}")
                        elif "iteration" in message.lower() or "draft" in message.lower():
                            print(f"   📝 {message[:80]}")

                    # Success!
                    if event_type == "execution.complete":
                        exit_code = event.get("exit_code", -1)
                        if exit_code == 0:
                            print("✅ Execution completed successfully!")
                            return True
                        else:
                            print(f"⚠️  Execution completed with exit code {exit_code}")
                            return False

                    if event_type == "execution.error":
                        print(f"❌ Execution error: {event.get('error')}")
                        return False

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing event: {e}")
                    continue

        return False

    async def run_test(self) -> bool:
        """Run complete test flow.

        Returns:
            True if all tests passed
        """
        print("=" * 60)
        print("INTERACTIVE PROMPT TEST")
        print("=" * 60)

        try:
            # Step 1: Create execution
            execution_id = await self.create_test_execution()

            # Step 2: Monitor for prompt
            prompt_event = await self.monitor_for_prompt(execution_id)
            if not prompt_event:
                print("\n❌ TEST FAILED: No interactive prompt detected")
                return False

            # Step 3: Submit response
            success = await self.submit_response(execution_id, "skip")
            if not success:
                print("\n❌ TEST FAILED: Could not submit response")
                return False

            # Step 4: Verify continuation
            continued = await self.verify_continuation(execution_id)
            if not continued:
                print("\n❌ TEST FAILED: Execution did not continue after response")
                return False

            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            return True

        except Exception as e:
            print(f"\n❌ TEST FAILED with exception: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            await self.client.aclose()


async def main():
    """Run tests."""
    tester = InteractivePromptTester()
    success = await tester.run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
