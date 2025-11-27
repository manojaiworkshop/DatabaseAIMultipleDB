#!/bin/bash
# Quick Test Script for Sample Ontology Demo
# ==========================================

echo "======================================================================"
echo "SAMPLE ONTOLOGY DEMONSTRATION - QUICK TEST"
echo "======================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Test 1: Without Ontology
echo "======================================================================"
echo "TEST 1: Running WITHOUT Ontology Demo"
echo "======================================================================"
python3 1_without_ontology.py
echo ""
echo "Press Enter to continue to Test 2..."
read

# Test 2: With Ontology
echo "======================================================================"
echo "TEST 2: Running WITH Ontology Demo"
echo "======================================================================"
python3 2_with_ontology.py
echo ""
echo "Press Enter to continue to Test 3..."
read

# Test 3: Context Comparison
echo "======================================================================"
echo "TEST 3: Context Comparison"
echo "======================================================================"
python3 4_context_comparison.py
echo ""
echo "Press Enter to continue to Test 4..."
read

# Test 4: Build Ontology
echo "======================================================================"
echo "TEST 4: Building Sample Ontology"
echo "======================================================================"
python3 3_ontology_builder.py
echo ""

# Summary
echo "======================================================================"
echo "ALL TESTS COMPLETED!"
echo "======================================================================"
echo ""
echo "Generated files:"
ls -lh sample_ontology.yml sample_ontology.json 2>/dev/null || echo "No files generated yet"
echo ""
echo "Next steps:"
echo "1. Review sample_ontology.yml"
echo "2. Review EXPLANATION.md for detailed theory"
echo "3. Customize vllm_config.yml for your deployment"
echo "4. Integrate ontology into your application"
echo ""
echo "For production deployment:"
echo "- See vllm_config.yml for VLLM setup"
echo "- See ../ONTOLOGY_USAGE_GUIDE.md for integration"
echo "- See ../ONTOLOGY_ARCHITECTURE.md for architecture"
echo ""
