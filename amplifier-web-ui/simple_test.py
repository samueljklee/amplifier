#!/usr/bin/env python3
"""
Simple test to validate interactive prompt endpoint works.
Tests the API endpoint directly with mock execution.
"""

import sys

import requests


def test_api_endpoint():
    """Test the respond endpoint structure."""
    print("\n=== Testing API Endpoint ===\n")

    # Test 1: Health check
    print("1. Health check...")
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Backend is healthy")
        else:
            print(f"   ❌ Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to backend: {e}")
        return False

    # Test 2: Check scenarios endpoint
    print("\n2. Checking scenarios...")
    try:
        resp = requests.get("http://localhost:8000/api/scenarios")
        if resp.status_code == 200:
            scenarios = resp.json()["scenarios"]
            print(f"   ✅ Found {len(scenarios)} scenarios")
            blog_writer = [s for s in scenarios if s["id"] == "blog_writer"]
            if blog_writer:
                print("   ✅ blog_writer scenario is available")
            else:
                print("   ⚠️  blog_writer scenario not found")
        else:
            print(f"   ❌ Failed to get scenarios: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Try respond endpoint with invalid execution (should fail gracefully)
    print("\n3. Testing respond endpoint with invalid execution...")
    try:
        resp = requests.post(
            "http://localhost:8000/api/executions/fake-id/respond", json={"response": "test"}, timeout=5
        )
        if resp.status_code == 404:
            print("   ✅ Endpoint correctly rejects invalid execution")
        else:
            print(f"   ⚠️  Unexpected status code: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Try respond endpoint without response field
    print("\n4. Testing validation...")
    try:
        resp = requests.post(
            "http://localhost:8000/api/executions/fake-id/respond",
            json={},  # Missing 'response' field
            timeout=5,
        )
        if resp.status_code == 400:
            print("   ✅ Endpoint correctly validates request body")
        else:
            print(f"   ⚠️  Unexpected status code: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n=== Basic API Tests Complete ===\n")
    return True


if __name__ == "__main__":
    success = test_api_endpoint()
    sys.exit(0 if success else 1)
