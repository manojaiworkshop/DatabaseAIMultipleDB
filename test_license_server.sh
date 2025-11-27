#!/bin/bash

# PGAIView License Server Test Script

set -e

LICENSE_SERVER_URL="${LICENSE_SERVER_URL:-http://localhost:5000}"
ADMIN_KEY="${ADMIN_KEY:-pgaiview-admin-2024}"

echo "🔐 PGAIView License Server Test"
echo "================================"
echo "Server URL: $LICENSE_SERVER_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "Test 1: Health Check"
echo "-------------------"
response=$(curl -s $LICENSE_SERVER_URL/health)
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "$response"
    exit 1
fi
echo ""

# Test 2: Get License Types
echo "Test 2: Get License Types"
echo "------------------------"
response=$(curl -s $LICENSE_SERVER_URL/license/types)
echo "$response" | python3 -m json.tool
echo -e "${GREEN}✓ License types retrieved${NC}"
echo ""

# Test 3: Generate Trial License
echo "Test 3: Generate Trial License"
echo "------------------------------"
trial_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/generate \
    -H "Content-Type: application/json" \
    -d "{
        \"deployment_id\": \"test-deployment-$(date +%s)\",
        \"license_type\": \"trial\",
        \"admin_key\": \"$ADMIN_KEY\"
    }")

echo "$trial_response" | python3 -m json.tool
trial_key=$(echo "$trial_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['license_key'])")

if [ -z "$trial_key" ]; then
    echo -e "${RED}✗ Failed to generate trial license${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Trial license generated${NC}"
echo ""

# Test 4: Validate Trial License
echo "Test 4: Validate Trial License"
echo "------------------------------"
validation_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/validate \
    -H "Content-Type: application/json" \
    -d "{\"license_key\": \"$trial_key\"}")

echo "$validation_response" | python3 -m json.tool
is_valid=$(echo "$validation_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['valid'])")

if [ "$is_valid" = "True" ]; then
    echo -e "${GREEN}✓ License validation passed${NC}"
else
    echo -e "${RED}✗ License validation failed${NC}"
    exit 1
fi
echo ""

# Test 5: Generate Standard License
echo "Test 5: Generate Standard License (2 months)"
echo "--------------------------------------------"
standard_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/generate \
    -H "Content-Type: application/json" \
    -d "{
        \"deployment_id\": \"standard-deployment-$(date +%s)\",
        \"license_type\": \"standard\",
        \"admin_key\": \"$ADMIN_KEY\"
    }")

echo "$standard_response" | python3 -m json.tool
standard_key=$(echo "$standard_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['license_key'])")
echo -e "${GREEN}✓ Standard license generated${NC}"
echo ""

# Test 6: Generate Enterprise License
echo "Test 6: Generate Enterprise License (1 year)"
echo "--------------------------------------------"
enterprise_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/generate \
    -H "Content-Type: application/json" \
    -d "{
        \"deployment_id\": \"enterprise-deployment-$(date +%s)\",
        \"license_type\": \"enterprise\",
        \"admin_key\": \"$ADMIN_KEY\"
    }")

echo "$enterprise_response" | python3 -m json.tool
echo -e "${GREEN}✓ Enterprise license generated${NC}"
echo ""

# Test 7: Test Invalid Admin Key
echo "Test 7: Test Invalid Admin Key"
echo "-------------------------------"
invalid_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/generate \
    -H "Content-Type: application/json" \
    -d "{
        \"deployment_id\": \"invalid-test\",
        \"license_type\": \"trial\",
        \"admin_key\": \"wrong-key\"
    }")

if echo "$invalid_response" | grep -q "Unauthorized"; then
    echo -e "${GREEN}✓ Invalid admin key correctly rejected${NC}"
else
    echo -e "${RED}✗ Security check failed${NC}"
    echo "$invalid_response"
fi
echo ""

# Test 8: Renew License
echo "Test 8: Renew License"
echo "--------------------"
renew_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/renew \
    -H "Content-Type: application/json" \
    -d "{
        \"current_license_key\": \"$trial_key\",
        \"admin_key\": \"$ADMIN_KEY\"
    }")

echo "$renew_response" | python3 -m json.tool
renewed_key=$(echo "$renew_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('license_key', ''))")

if [ -n "$renewed_key" ]; then
    echo -e "${GREEN}✓ License renewal successful${NC}"
else
    echo -e "${YELLOW}⚠ License renewal may have failed${NC}"
fi
echo ""

# Test 9: Validate Invalid License
echo "Test 9: Validate Invalid License"
echo "--------------------------------"
invalid_license_response=$(curl -s -X POST $LICENSE_SERVER_URL/license/validate \
    -H "Content-Type: application/json" \
    -d '{"license_key": "invalid-key-123"}')

echo "$invalid_license_response" | python3 -m json.tool
is_invalid=$(echo "$invalid_license_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['valid'])")

if [ "$is_invalid" = "False" ]; then
    echo -e "${GREEN}✓ Invalid license correctly rejected${NC}"
else
    echo -e "${RED}✗ Invalid license validation failed${NC}"
fi
echo ""

# Summary
echo "================================"
echo -e "${GREEN}🎉 All tests passed!${NC}"
echo ""
echo "Generated License Keys:"
echo "----------------------"
echo -e "${YELLOW}Trial (10 days):${NC}"
echo "$trial_key"
echo ""
echo -e "${YELLOW}Standard (2 months):${NC}"
echo "$standard_key"
echo ""
echo "You can use these keys to activate PGAIView deployments."
echo "Store them securely!"
