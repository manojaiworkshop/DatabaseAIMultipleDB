#!/bin/bash

# PGAIView License Validator
# Validates existing license keys

# Configuration
LICENSE_SERVER="http://localhost:5000"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     PGAIView License Validator v1.0                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if license server is running
echo -e "${YELLOW}🔍 Checking license server...${NC}"
if ! curl -s "$LICENSE_SERVER/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ License server is not running on $LICENSE_SERVER${NC}"
    echo ""
    echo "Start the server with: ./start_license_server.sh"
    exit 1
fi
echo -e "${GREEN}✅ License server is running${NC}"
echo ""

# Get license key
echo "Enter your license key:"
read -p "> " license_key

if [ -z "$license_key" ]; then
    echo -e "${RED}❌ License key cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔐 Validating license...${NC}"

# Validate license
response=$(curl -s -X POST "$LICENSE_SERVER/license/validate" \
    -H "Content-Type: application/json" \
    -d "{\"license_key\": \"$license_key\"}")

# Check if valid
is_valid=$(echo "$response" | grep -o '"valid":[^,}]*' | cut -d':' -f2 | tr -d ' ')

echo ""
if [ "$is_valid" = "true" ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ License is VALID!                              ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Extract details
    license_type=$(echo "$response" | grep -o '"license_type":"[^"]*"' | cut -d'"' -f4)
    deployment_id=$(echo "$response" | grep -o '"deployment_id":"[^"]*"' | cut -d'"' -f4)
    expiry_date=$(echo "$response" | grep -o '"expiry_date":"[^"]*"' | cut -d'"' -f4)
    days_remaining=$(echo "$response" | grep -o '"days_remaining":[0-9]*' | cut -d':' -f2)
    
    echo -e "${BLUE}License Type:${NC}      ${license_type}"
    echo -e "${BLUE}Deployment ID:${NC}     ${deployment_id}"
    echo -e "${BLUE}Expires:${NC}           ${expiry_date}"
    echo -e "${BLUE}Days Remaining:${NC}    ${days_remaining} days"
    echo ""
    
    if [ "$days_remaining" -lt 7 ]; then
        echo -e "${YELLOW}⚠️  Warning: License expires in less than 7 days!${NC}"
        echo -e "${YELLOW}   Consider renewing your license soon.${NC}"
    fi
else
    echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ License is INVALID or EXPIRED!                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    error=$(echo "$response" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
    if [ ! -z "$error" ]; then
        echo -e "${RED}Error: ${error}${NC}"
    fi
    
    echo ""
    echo "Please generate a new license with: ./generate_license.sh"
fi

echo ""
