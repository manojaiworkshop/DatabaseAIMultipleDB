#!/bin/bash

# DatabaseAI Quick Start Script

echo "🚀 DatabaseAI Quick Start"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

cd ..
echo -e "${GREEN}✅ Backend setup complete${NC}"
echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install --silent
fi

cd ..
echo -e "${GREEN}✅ Frontend setup complete${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo "Creating frontend .env file..."
    echo "REACT_APP_API_URL=http://localhost:8088/api/v1" > frontend/.env
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "=========================================="
echo ""
echo "To start the application:"
echo ""
echo "1️⃣  Start the backend (in one terminal):"
echo -e "   ${YELLOW}cd backend && source venv/bin/activate${NC}"
echo -e "   ${YELLOW}python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8088${NC}"
echo ""
echo "2️⃣  Start the frontend (in another terminal):"
echo -e "   ${YELLOW}cd frontend && npm start${NC}"
echo ""
echo "3️⃣  Open your browser to:"
echo -e "   ${GREEN}http://localhost:3000${NC}"
echo ""
echo "📚 Documentation: README_APP.md"
echo ""
