#!/bin/bash
# ============================================================================
# Oracle User Creation Shell Script
# Wrapper for create_oracle_user.py
# ============================================================================

set -e

echo "=============================================="
echo "  Oracle User Creation Script"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if oracledb is installed
if ! python3 -c "import oracledb" 2>/dev/null; then
    echo "⚠️  Warning: oracledb module not found"
    echo "   Installing oracledb..."
    pip install oracledb
    echo ""
fi

# Set environment variables (optional - can be overridden)
export ORACLE_PASSWORD="${ORACLE_PASSWORD:-oracle123}"
export ORACLE_DSN="${ORACLE_DSN:-localhost:1521/XE}"
export NEW_USER="${NEW_USER:-pgaiview}"
export NEW_PASSWORD="${NEW_PASSWORD:-pgaiview123}"

# Display configuration
echo "📋 Configuration:"
echo "   Oracle DSN: ${ORACLE_DSN}"
echo "   Oracle Admin Password: ${ORACLE_PASSWORD}"
echo "   New Username: ${NEW_USER}"
echo "   New Password: ${NEW_PASSWORD}"
echo ""

# Run Python script
python3 "$(dirname "$0")/create_oracle_user.py"

echo ""
echo "✅ Script completed!"
