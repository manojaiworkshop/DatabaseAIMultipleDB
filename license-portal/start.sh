#!/bin/bash

# PGAIView License Portal - Startup Script
# Starts both backend and frontend servers

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     PGAIView License Portal v2.0 - Starting...        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi
    
    echo -e "${BLUE}Goodbye!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Backend setup
echo ""
echo -e "${BLUE}Setting up backend...${NC}"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

if ! pip show fastapi &> /dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r requirements.txt
fi
echo -e "${GREEN}✓ Backend dependencies ready${NC}"

# Frontend setup
echo ""
echo -e "${BLUE}Setting up frontend...${NC}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

# Check if ports are available
echo ""
echo -e "${BLUE}Checking ports...${NC}"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 8000 is in use. Stopping existing process...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 3000 is in use. Stopping existing process...${NC}"
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    sleep 1
fi
echo -e "${GREEN}✓ Ports are available${NC}"

# Start Backend
echo ""
echo -e "${BLUE}Starting FastAPI backend...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate
python main.py > /tmp/license_portal_backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start!${NC}"
    echo "Check logs: tail /tmp/license_portal_backend.log"
    exit 1
fi
echo -e "${GREEN}✓ Backend running on http://localhost:8000${NC}"

# Start Frontend
echo ""
echo -e "${BLUE}Starting React frontend...${NC}"
cd "$FRONTEND_DIR"
npm run dev > /tmp/license_portal_frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 3

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Frontend failed to start!${NC}"
    echo "Check logs: tail /tmp/license_portal_frontend.log"
    exit 1
fi
echo -e "${GREEN}✓ Frontend running on http://localhost:3000${NC}"

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Services Started Successfully!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🌐 Frontend:${NC}     http://localhost:3000"
echo -e "${BLUE}🔌 Backend API:${NC}  http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC}     http://localhost:8000/api/docs"
echo ""
echo -e "${YELLOW}🔑 Default Admin Key:${NC} pgaiview-admin-2024"
echo ""
echo -e "${BLUE}📋 License Types:${NC}"
echo "  • Trial      - 10 days"
echo "  • Standard   - 60 days"  
echo "  • Enterprise - 365 days"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Try to open browser
sleep 2
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:3000" 2>/dev/null &
elif command -v open &> /dev/null; then
    open "http://localhost:3000" 2>/dev/null &
fi

# Keep running
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend stopped unexpectedly!${NC}"
        exit 1
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend stopped unexpectedly!${NC}"
        exit 1
    fi
    
    sleep 5
done
