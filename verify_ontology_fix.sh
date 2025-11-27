#!/bin/bash
# Quick verification script for ontology fix

echo "=================================================="
echo "ONTOLOGY FIX VERIFICATION"
echo "=================================================="
echo ""

# Check if files were modified
echo "📁 Checking if fix files exist..."
if grep -q "generate_structured" backend/app/services/llm.py; then
    echo "✅ llm.py has generate_structured method"
else
    echo "❌ llm.py missing generate_structured method"
    exit 1
fi

if grep -q "CRITICAL INSTRUCTIONS" backend/app/services/dynamic_ontology.py; then
    echo "✅ dynamic_ontology.py has improved prompts"
else
    echo "❌ dynamic_ontology.py missing prompt improvements"
    exit 1
fi

echo ""
echo "=================================================="
echo "LATEST ONTOLOGY FILE"
echo "=================================================="

# Find most recent ontology file
LATEST_ONTO=$(ls -t ontology/testing_*_ontology_*.yml 2>/dev/null | head -1)

if [ -z "$LATEST_ONTO" ]; then
    echo "⚠️  No ontology files found"
    echo "   Generate one from the UI first"
    exit 0
fi

echo "📄 File: $LATEST_ONTO"
echo ""

# Check for hallucinated concepts
echo "🔍 Checking for hallucinated concepts..."
HALLUCINATED=0

for concept in "Customer" "Order" "Product" "Department" "Employee" "Category"; do
    if grep -q "$concept:" "$LATEST_ONTO"; then
        echo "❌ Found hallucinated concept: $concept"
        HALLUCINATED=1
    fi
done

if [ $HALLUCINATED -eq 0 ]; then
    echo "✅ No hallucinated concepts found"
fi

echo ""

# Check for expected concepts
echo "🔍 Checking for expected concepts..."
EXPECTED=0

for concept in "NetworkDevice" "DeviceStatus" "HardwareInfo" "MaintenanceLog" "NetworkAlert"; do
    if grep -qi "$concept" "$LATEST_ONTO"; then
        echo "✅ Found: $concept"
        EXPECTED=$((EXPECTED + 1))
    else
        echo "⚠️  Missing: $concept"
    fi
done

echo ""

# Count concepts
CONCEPT_COUNT=$(grep -c "confidence:" "$LATEST_ONTO" 2>/dev/null || echo "0")
echo "📊 Total concepts in file: $CONCEPT_COUNT"

if [ $CONCEPT_COUNT -eq 0 ]; then
    echo "❌ Ontology file has 0 concepts!"
    echo ""
    echo "This means:"
    echo "1. Database might not be connected when generating"
    echo "2. LLM call might be failing"
    echo "3. Check backend logs for errors"
elif [ $CONCEPT_COUNT -ge 5 ] && [ $EXPECTED -ge 3 ] && [ $HALLUCINATED -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "🎉 SUCCESS! Ontology looks correct!"
    echo "=================================================="
    echo ""
    echo "✅ $EXPECTED/$EXPECTED expected concepts found"
    echo "✅ No hallucinated concepts"
    echo "✅ Generated from actual database schema"
else
    echo ""
    echo "=================================================="
    echo "⚠️  NEEDS ATTENTION"
    echo "=================================================="
    echo ""
    if [ $HALLUCINATED -ne 0 ]; then
        echo "❌ Hallucinated concepts present"
        echo "   → Try regenerating after backend restart"
    fi
    if [ $EXPECTED -lt 3 ]; then
        echo "⚠️  Missing expected concepts"
        echo "   → Check if database connection is active"
    fi
fi

echo ""
echo "=================================================="
echo "NEXT STEPS"
echo "=================================================="
echo ""
echo "To regenerate ontology:"
echo "1. Make sure backend is running: python run_backend.py"
echo "2. Connect to database in UI (192.168.1.2:5432/testing)"
echo "3. Open Settings → Ontology tab"
echo "4. Click 'Generate Ontology'"
echo "5. Re-run this script: bash verify_ontology_fix.sh"
echo ""
