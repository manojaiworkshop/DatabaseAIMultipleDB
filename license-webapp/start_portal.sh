#!/bin/bash

# PGAIView License Portal Startup Script
# This script starts both the license server and web portal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  PGAIView License Portal${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if license_server.py exists
if [ ! -f "$PROJECT_ROOT/license_server.py" ]; then
    echo -e "${RED}Error: license_server.py not found!${NC}"
    echo "Please ensure you're running this from the correct directory."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Flask not found. Installing requirements...${NC}"
    pip3 install flask flask-cors cryptography
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    # Kill license server if running
    if [ ! -z "$LICENSE_SERVER_PID" ]; then
        kill $LICENSE_SERVER_PID 2>/dev/null || true
        echo -e "${GREEN}✓ License server stopped${NC}"
    fi
    
    # Kill web server if running
    if [ ! -z "$WEB_SERVER_PID" ]; then
        kill $WEB_SERVER_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Web server stopped${NC}"
    fi
    
    echo -e "${BLUE}Goodbye!${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start License Server
echo -e "${BLUE}Starting License Server...${NC}"
cd "$PROJECT_ROOT"
python3 license_server.py > /tmp/license_server.log 2>&1 &
LICENSE_SERVER_PID=$!

# Wait for license server to start
sleep 2

# Check if license server is running
if ! kill -0 $LICENSE_SERVER_PID 2>/dev/null; then
    echo -e "${RED}Error: Failed to start license server!${NC}"
    echo "Check logs: tail /tmp/license_server.log"
    exit 1
fi

# Test license server
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ License Server running on http://localhost:5000${NC}"
else
    echo -e "${YELLOW}⚠ License Server started but not responding yet...${NC}"
fi

# Start Web Portal
echo -e "${BLUE}Starting Web Portal...${NC}"
cd "$SCRIPT_DIR"

# Function to find available port
find_available_port() {
    local port=$1
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        echo -e "${YELLOW}Port $port is in use, trying $((port + 1))...${NC}"
        port=$((port + 1))
    done
    echo $port
}

# Find available port starting from 8080
WEB_PORT=$(find_available_port 8080)

# Try to find a suitable HTTP server
if command -v python3 &> /dev/null; then
    python3 -m http.server $WEB_PORT > /tmp/web_portal.log 2>&1 &
    WEB_SERVER_PID=$!
    
    # Wait a moment and verify it started
    sleep 1
    if kill -0 $WEB_SERVER_PID 2>/dev/null; then
        echo -e "${GREEN}✓ Web Portal running on http://localhost:$WEB_PORT${NC}"
        WEB_PORTAL_URL="http://localhost:$WEB_PORT"
    else
        echo -e "${RED}✗ Failed to start web server${NC}"
        WEB_SERVER_PID=""
    fi
elif command -v npx &> /dev/null; then
    npx http-server -p $WEB_PORT > /tmp/web_portal.log 2>&1 &
    WEB_SERVER_PID=$!
    
    sleep 1
    if kill -0 $WEB_SERVER_PID 2>/dev/null; then
        echo -e "${GREEN}✓ Web Portal running on http://localhost:$WEB_PORT${NC}"
        WEB_PORTAL_URL="http://localhost:$WEB_PORT"
    else
        echo -e "${RED}✗ Failed to start web server${NC}"
        WEB_SERVER_PID=""
    fi
else
    echo -e "${YELLOW}⚠ No HTTP server found. Opening file directly...${NC}"
    WEB_PORTAL_URL="file://$SCRIPT_DIR/index.html"
    # Try to open in browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "$SCRIPT_DIR/index.html" &
    elif command -v open &> /dev/null; then
        open "$SCRIPT_DIR/index.html" &
    elif command -v firefox &> /dev/null; then
        firefox "$SCRIPT_DIR/index.html" &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$SCRIPT_DIR/index.html" &
    else
        echo -e "${YELLOW}Please open $SCRIPT_DIR/index.html in your browser${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}License Server:${NC} http://localhost:5000"
echo -e "${BLUE}Web Portal:${NC}     ${WEB_PORTAL_URL:-http://localhost:8080}"
echo ""
echo -e "${YELLOW}💡 Tip: Opening browser automatically...${NC}"

# Try to open browser automatically
sleep 1
if [ ! -z "$WEB_PORTAL_URL" ] && [[ "$WEB_PORTAL_URL" == http* ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "$WEB_PORTAL_URL" 2>/dev/null &
    elif command -v firefox &> /dev/null; then
        firefox "$WEB_PORTAL_URL" 2>/dev/null &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$WEB_PORTAL_URL" 2>/dev/null &
    fi
fi

echo ""
echo -e "${YELLOW}Default Admin Key:${NC} pgaiview-admin-2024"
echo ""
echo -e "${BLUE}License Types Available:${NC}"
echo "  • Trial      - 10 days"
echo "  • Standard   - 60 days"
echo "  • Enterprise - 365 days"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running
while true; do
    # Check if license server is still running
    if ! kill -0 $LICENSE_SERVER_PID 2>/dev/null; then
        echo -e "${RED}License server stopped unexpectedly!${NC}"
        exit 1
    fi
    
    # Check if web server is still running (if it was started)
    if [ ! -z "$WEB_SERVER_PID" ] && ! kill -0 $WEB_SERVER_PID 2>/dev/null; then
        echo -e "${RED}Web server stopped unexpectedly!${NC}"
        exit 1
    fi
    
    sleep 5
done
