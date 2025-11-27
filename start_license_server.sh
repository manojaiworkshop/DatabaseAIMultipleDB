#!/bin/bash

# Quick Start Script for PGAIView License Server

set -e

echo "🔐 PGAIView License Server - Quick Start"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✓ pip3 found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r license_requirements.txt

# Set environment variables
export LICENSE_SECRET_KEY="${LICENSE_SECRET_KEY:-$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')}"
export ADMIN_KEY="${ADMIN_KEY:-pgaiview-admin-2024}"
export PORT="${PORT:-5000}"

echo ""
echo "🔑 Configuration:"
echo "   Port: $PORT"
echo "   Admin Key: $ADMIN_KEY"
echo "   Secret Key: ${LICENSE_SECRET_KEY:0:20}... (keep secure!)"
echo ""

# Save configuration
cat > .license_server_env << EOF
# PGAIView License Server Configuration
# Generated: $(date)

export LICENSE_SECRET_KEY="$LICENSE_SECRET_KEY"
export ADMIN_KEY="$ADMIN_KEY"
export PORT="$PORT"
EOF

echo "✓ Configuration saved to .license_server_env"
echo "  (Load with: source .license_server_env)"
echo ""

# Start the server
echo "🚀 Starting License Server on port $PORT..."
echo ""
python3 license_server.py
