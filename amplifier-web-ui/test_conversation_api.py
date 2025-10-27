#!/usr/bin/env python3
"""Test the workflow conversation API."""

import asyncio

import httpx


async def test_conversation():
    """Test the conversation API endpoint."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Start a new conversation
        print("🚀 Starting new conversation...")
        response = await client.post(
            f"{base_url}/api/workflow/conversation",
            json={"message": "I need to process customer feedback from CSV files and generate insights"},
            timeout=30.0,
        )

        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return

        result = response.json()
        print(f"\n✅ AI Response:\n{result['ai_message']}\n")
        print("📊 Workflow Preview:")
        print(f"  - Name: {result['workflow_preview']['name']}")
        print(f"  - Nodes: {len(result['workflow_preview']['nodes'])}")
        print(f"  - Ready to generate: {result['ready_to_generate']}\n")

        session_id = result["session_id"]
        print(f"🔑 Session ID: {session_id}\n")

        # Continue the conversation
        print("💬 Continuing conversation...")
        response2 = await client.post(
            f"{base_url}/api/workflow/conversation",
            json={
                "session_id": session_id,
                "message": "The CSV has columns: date, customer_id, rating, and comments. I want sentiment analysis and theme extraction.",
            },
            timeout=30.0,
        )

        if response2.status_code != 200:
            print(f"❌ Error: {response2.status_code}")
            print(response2.text)
            return

        result2 = response2.json()
        print(f"\n✅ AI Response:\n{result2['ai_message']}\n")
        print("📊 Updated Workflow:")
        print(f"  - Nodes: {len(result2['workflow_preview']['nodes'])}")
        print(f"  - Ready to generate: {result2['ready_to_generate']}\n")

        # Get session state
        print("📋 Getting session state...")
        response3 = await client.get(f"{base_url}/api/workflow/session/{session_id}")

        if response3.status_code != 200:
            print(f"❌ Error: {response3.status_code}")
            print(response3.text)
            return

        session = response3.json()
        print("\n✅ Session State:")
        print(f"  - Messages: {len(session['history'])}")
        print(f"  - Workflow nodes: {len(session['workflow']['nodes'])}")
        print(f"  - Input format: {session['workflow']['input_format']}")
        print(f"  - Output requirements: {session['workflow']['output_requirements']}")

        print("\n✨ Test completed successfully!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Workflow Conversation API")
    print("=" * 60)
    print()
    asyncio.run(test_conversation())
