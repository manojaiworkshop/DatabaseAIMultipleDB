#!/bin/bash

# Start DatabaseAI Backend Server

echo "🚀 Starting DatabaseAI Backend Server..."
echo ""

# Check if we're in the right directory
if [ ! -f "app_config.yml" ]; then
    echo "❌ Error: app_config.yml not found"
    echo "Please run this script from the DATABASEAI root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "/home/crl/mapenv" ]; then
    echo "📦 Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source backend/venv/bin/activate

# Start the server
echo "🌐 Starting backend server on http://0.0.0.0:8088"
echo "📚 API documentation: http://localhost:8088/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 run_backend.py
