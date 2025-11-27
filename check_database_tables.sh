#!/bin/bash
# Quick test to verify what tables are in the database

echo "==================================================="
echo "DATABASE TABLES VERIFICATION"
echo "==================================================="
echo ""

# Connect to PostgreSQL and list tables
echo "Connecting to database 'testing' at 192.168.1.2:5432..."
echo ""

PGPASSWORD=postgres psql -h 192.168.1.2 -p 5432 -U postgres -d testing -c "\dt" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Could not connect to database"
    echo "   Make sure PostgreSQL is running and accessible"
    exit 1
fi

echo ""
echo "==================================================="
echo "EXPECTED TABLES FOR ONTOLOGY"
echo "==================================================="
echo ""
echo "Your ontology should generate concepts for these tables:"
echo "  1. device_status"
echo "  2. hardware_info"
echo "  3. maintenance_logs"
echo "  4. network_alerts"
echo "  5. network_devices"
echo ""
echo "If ontology shows Port, Router, Switch, VLAN:"
echo "  → Those tables DON'T exist in your database"
echo "  → LLM is hallucinating / ignoring schema"
echo ""
