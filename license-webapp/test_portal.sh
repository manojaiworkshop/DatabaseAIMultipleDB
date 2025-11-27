#!/bin/bash

# License Web Portal - Quick Test Script
# This script demonstrates the portal functionality

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         PGAIView License Web Portal - Demo Test           ║"
echo "╔════════════════════════════════════════════════════════════╗"
echo ""

# Check if license server is running
echo "🔍 Checking License Server..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ License Server is running on port 5000"
else
    echo "❌ License Server is NOT running!"
    echo ""
    echo "Please start it first:"
    echo "  python3 license_server.py"
    exit 1
fi

echo ""
echo "🔍 Checking Web Portal..."
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "✅ Web Portal is accessible on port 8080"
else
    echo "⚠️  Web Portal is not running on port 8080"
    echo ""
    echo "You can start it with:"
    echo "  cd license-webapp && python3 -m http.server 8080"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Available License Types:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

curl -s http://localhost:5000/license/types | python3 -m json.tool 2>/dev/null || echo "Cannot fetch license types"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing API Endpoints:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test generate endpoint (will fail without admin key - expected)
echo "1️⃣  Testing Generate License Endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{"deployment_id":"test-123","license_type":"trial","admin_key":"wrong-key"}')

if echo "$RESPONSE" | grep -q "Unauthorized"; then
    echo "✅ Generate endpoint is working (correctly rejecting invalid admin key)"
else
    echo "⚠️  Unexpected response from generate endpoint"
fi

echo ""
echo "2️⃣  Testing Validate License Endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:5000/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"invalid-key"}')

if echo "$RESPONSE" | grep -q "valid"; then
    echo "✅ Validate endpoint is working"
else
    echo "⚠️  Unexpected response from validate endpoint"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Portal Features:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Generate License"
echo "   • Enter email and deployment ID"
echo "   • Select license type (Trial/Standard/Enterprise)"
echo "   • Auto-generate deployment IDs"
echo "   • Copy license key to clipboard"
echo ""
echo "🔍 Validate License"
echo "   • Paste license key"
echo "   • View all license details"
echo "   • Check validity status"
echo "   • See days remaining"
echo ""
echo "🔄 Renew License"
echo "   • Extend existing licenses"
echo "   • Generate new keys automatically"
echo "   • Same deployment ID preserved"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Access Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Web Portal:     http://localhost:8080"
echo "🔌 License Server: http://localhost:5000"
echo "🔑 Default Admin:  pgaiview-admin-2024"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Quick Start Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Start Everything:"
echo "  cd license-webapp && ./start_portal.sh"
echo ""
echo "Start License Server Only:"
echo "  python3 license_server.py"
echo ""
echo "Start Web Portal Only:"
echo "  cd license-webapp && python3 -m http.server 8080"
echo ""
echo "Open in Browser:"
echo "  firefox http://localhost:8080"
echo "  # or"
echo "  google-chrome http://localhost:8080"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
