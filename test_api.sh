#!/bin/bash

# Test script for the AI Assistant API
# Tests all endpoints and provides example responses

API_URL="${1:-http://localhost:8000}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  VodafoneZiggo AI Assistant - Tests  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Testing API at: $API_URL"
echo ""

# Test 1: Health Check
echo -e "${YELLOW}[TEST 1] Health Check${NC}"
echo "Endpoint: GET $API_URL/api/health"
RESPONSE=$(curl -s "$API_URL/api/health")
if echo "$RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 2: Get Stats
echo -e "${YELLOW}[TEST 2] Vector Store Statistics${NC}"
echo "Endpoint: GET $API_URL/api/stats"
RESPONSE=$(curl -s "$API_URL/api/stats")
if echo "$RESPONSE" | grep -q "initialized\|num_documents"; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 3: Ask a Question (Simple endpoint)
echo -e "${YELLOW}[TEST 3] Ask a Question (Simple Endpoint)${NC}"
echo "Endpoint: POST $API_URL/api/ask-simple"
QUESTION="What internet packages do you offer?"
echo "Question: $QUESTION"
RESPONSE=$(curl -s -X POST "$API_URL/api/ask-simple" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"$QUESTION\"}")

if echo "$RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 4: Ask another question
echo -e "${YELLOW}[TEST 4] Another Question${NC}"
echo "Endpoint: POST $API_URL/api/ask"
QUESTION="Do you have 5G coverage?"
echo "Question: $QUESTION"
RESPONSE=$(curl -s -X POST "$API_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"$QUESTION\"}")

if echo "$RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 5: Error Handling - Empty question
echo -e "${YELLOW}[TEST 5] Error Handling - Empty Question${NC}"
echo "Endpoint: POST $API_URL/api/ask"
echo "Question: (empty)"
RESPONSE=$(curl -s -X POST "$API_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"\"}")

if echo "$RESPONSE" | grep -q "error\|detail"; then
    echo -e "${GREEN}✓ PASS${NC} - Correctly rejected empty question"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC} - Should have rejected empty question"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 6: Root endpoint
echo -e "${YELLOW}[TEST 6] Root Endpoint${NC}"
echo "Endpoint: GET $API_URL/"
RESPONSE=$(curl -s "$API_URL/")
if echo "$RESPONSE" | grep -q "VodafoneZiggo\|endpoints"; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 7: API Docs
echo -e "${YELLOW}[TEST 7] API Documentation${NC}"
echo "Endpoint: GET $API_URL/docs"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Swagger UI available at $API_URL/docs"
else
    echo -e "${RED}✗ FAIL${NC} - HTTP $HTTP_CODE"
fi
echo ""

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Test Suite Complete               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "💡 Tips:"
echo "  - Interactive API: $API_URL/docs"
echo "  - View logs: docker-compose logs -f ai-assistant"
echo "  - Performance test: Load testing with Apache Bench"
echo "    ab -n 100 -c 10 -p payload.json -T 'application/json' $API_URL/api/ask"
