#!/bin/bash
# ============================================================================
# Oracle Network Management Test Database Setup Script
# ============================================================================

set -e

echo "=============================================="
echo "  Oracle Test Database Setup"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if oracledb is installed
if ! python3 -c "import oracledb" 2>/dev/null; then
    echo "❌ Error: oracledb module not found"
    echo "   Install with: pip install oracledb"
    exit 1
fi

# Set environment variables (optional - can be overridden)
export ORACLE_USER="${ORACLE_USER:-pgaiview}"
export ORACLE_PASSWORD="${ORACLE_PASSWORD:-pgaiview123}"
export ORACLE_DSN="${ORACLE_DSN:-localhost:1521/XE}"

# Display configuration
echo "📋 Configuration:"
echo "   Oracle User: ${ORACLE_USER}"
echo "   Oracle DSN: ${ORACLE_DSN}"
echo ""

# Check Oracle connection
echo "🔍 Checking Oracle connection..."
if python3 -c "import oracledb; oracledb.connect(user='${ORACLE_USER}', password='${ORACLE_PASSWORD}', dsn='${ORACLE_DSN}')" 2>/dev/null; then
    echo "   ✓ Connection successful"
    echo ""
else
    echo "   ❌ Connection failed"
    echo "   Please check your Oracle database is running:"
    echo "   docker compose -f docker-compose.oracle.yml up"
    exit 1
fi

# Run Python script
python3 "$(dirname "$0")/test_network_management_oracle.py"

echo ""
echo "✅ Setup completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Update your config.yml with Oracle connection details"
echo "   2. Start your DatabaseAI application"
echo "   3. Try the sample queries listed above"
echo ""
