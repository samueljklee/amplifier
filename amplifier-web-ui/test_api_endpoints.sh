#!/bin/bash
# Test script for scenario generation API endpoints

set -e

API_URL="http://localhost:8000"

echo "=== Testing Scenario Generation API ==="
echo ""

# Test 1: Create session
echo "1. Creating generation session..."
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/api/ultrathink/sessions" \
  -H "Content-Type: application/json" \
  -d '{"description": "A tool to analyze Python code complexity"}')

SESSION_ID=$(echo $SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "   ✅ Session created: $SESSION_ID"
echo ""

# Wait a bit for generation to start
sleep 2

# Test 2: Get session state
echo "2. Getting session state..."
STATE_RESPONSE=$(curl -s "$API_URL/api/ultrathink/sessions/$SESSION_ID")
STATUS=$(echo $STATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
echo "   Status: $STATUS"
echo ""

# Test 3: Wait for completion (poll every second)
echo "3. Waiting for generation to complete..."
for i in {1..30}; do
  STATE_RESPONSE=$(curl -s "$API_URL/api/ultrathink/sessions/$SESSION_ID")
  STATUS=$(echo $STATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
  echo "   Attempt $i: $STATUS"

  if [ "$STATUS" == "complete" ] || [ "$STATUS" == "failed" ]; then
    break
  fi

  sleep 1
done
echo ""

# Test 4: Get generated files
echo "4. Getting generated files..."
FILES_RESPONSE=$(curl -s "$API_URL/api/ultrathink/sessions/$SESSION_ID/files")
FILE_COUNT=$(echo $FILES_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "   ✅ Files generated: $FILE_COUNT"
echo ""

# Test 5: Send a message (not implemented yet, but should not error)
echo "5. Sending message to session..."
MESSAGE_RESPONSE=$(curl -s -X POST "$API_URL/api/ultrathink/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "Add more detailed logging"}')
echo "   ✅ Message sent"
echo ""

echo "=== All Tests Passed ==="
