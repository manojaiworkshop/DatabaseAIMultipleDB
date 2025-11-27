#!/bin/bash
# Build Backend Executable using PyInstaller
# Creates standalone executable with all dependencies

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  DatabaseAI Backend - Build Executable${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "databaseenv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Run: python3 -m venv databaseenv && source databaseenv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}[1/4] Activating virtual environment...${NC}"
source databaseenv/bin/activate

# Install PyInstaller if not already installed
echo -e "${BLUE}[2/4] Installing PyInstaller...${NC}"
pip install pyinstaller --quiet

# Clean previous build
echo -e "${BLUE}[3/4] Cleaning previous build...${NC}"
rm -rf build dist
mkdir -p dist

# Build executable
echo -e "${BLUE}[4/4] Building executable...${NC}"
pyinstaller backend.spec --clean --noconfirm

# Check if build was successful
if [ -f "dist/databaseai-backend" ]; then
    echo ""
    echo -e "${GREEN}✅ Build Successful!${NC}"
    echo ""
    echo "📦 Executable: dist/databaseai-backend"
    echo "📁 Size: $(du -h dist/databaseai-backend | cut -f1)"
    echo ""
    echo "🚀 To run:"
    echo "  cd dist && ./databaseai-backend"
    echo ""
    echo -e "${YELLOW}Note: Make sure app_config.yml is in the same directory${NC}"
else
    echo ""
    echo -e "${RED}❌ Build Failed!${NC}"
    echo "Check build/backend/ for error logs"
    exit 1
fi
