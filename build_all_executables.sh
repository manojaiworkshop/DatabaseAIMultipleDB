#!/bin/bash
# Build Both Backend and Frontend Executables
# Standalone executables for Windows/Linux/Mac

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  DatabaseAI - Build Executables${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Build Backend Executable
echo -e "${BLUE}[1/2] Building Backend Executable...${NC}"
./build_backend_exe.sh

# Build Frontend Static Files
echo ""
echo -e "${BLUE}[2/2] Building Frontend Static Files...${NC}"
cd frontend
npm run build
cd ..

echo ""
echo -e "${GREEN}✅ Build Complete!${NC}"
echo ""
echo "📦 Artifacts:"
echo "  Backend:  dist/databaseai-backend"
echo "  Frontend: frontend/build/"
echo ""
echo "🚀 To run backend:"
echo "  cd dist && ./databaseai-backend"
echo ""
echo "🌐 To serve frontend:"
echo "  cd frontend/build && python -m http.server 3000"
