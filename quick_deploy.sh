#!/bin/bash
# Quick Start Script - Build Everything and Run Locally
# This script builds executables, Docker images, and starts the application

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  DatabaseAI - Quick Start${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Menu
echo "Choose deployment option:"
echo "1) Build & Run with Docker Compose (Recommended)"
echo "2) Build Standalone Executables"
echo "3) Build Docker Images Only (No Run)"
echo "4) Pull Published Images & Run"
echo "5) Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo -e "${BLUE}Building and running with Docker Compose...${NC}"
        
        # Build images
        echo -e "${BLUE}[1/2] Building Docker images...${NC}"
        docker compose build
        
        # Start services
        echo -e "${BLUE}[2/2] Starting services...${NC}"
        docker compose up -d
        
        echo ""
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        echo ""
        echo "🌐 Access the application:"
        echo "  Frontend:  http://localhost:3000"
        echo "  Backend:   http://localhost:8088"
        echo "  API Docs:  http://localhost:8088/docs"
        echo "  PostgreSQL: localhost:5432 (user: postgres, password: postgres)"
        echo ""
        echo "📊 View logs: docker compose logs -f"
        echo "🛑 Stop:      docker compose down"
        ;;
        
    2)
        echo -e "${BLUE}Building standalone executables...${NC}"
        
        # Check if virtual environment exists
        if [ ! -d "databaseenv" ]; then
            echo -e "${RED}Virtual environment not found!${NC}"
            echo "Creating virtual environment..."
            python3 -m venv databaseenv
            source databaseenv/bin/activate
            pip install -r requirements.txt
        fi
        
        # Build executables
        ./build_all_executables.sh
        
        echo ""
        echo -e "${GREEN}✅ Executables built successfully!${NC}"
        echo ""
        echo "📦 Backend executable: dist/databaseai-backend"
        echo "📂 Frontend build:     frontend/build/"
        echo ""
        echo "🚀 To run backend:"
        echo "  cd dist && ./databaseai-backend"
        echo ""
        echo "🌐 To serve frontend:"
        echo "  cd frontend/build && python -m http.server 3000"
        ;;
        
    3)
        echo -e "${BLUE}Building Docker images...${NC}"
        
        # Build images
        docker compose build
        
        echo ""
        echo -e "${GREEN}✅ Docker images built successfully!${NC}"
        echo ""
        echo "📦 Images:"
        docker images | grep databaseai
        echo ""
        echo "🚀 To run: docker compose up -d"
        ;;
        
    4)
        echo -e "${BLUE}Pulling and running published images...${NC}"
        
        # Check if .env exists
        if [ ! -f ".env" ]; then
            echo -e "${YELLOW}Creating .env file...${NC}"
            read -p "Enter Docker Hub username: " docker_user
            cat > .env << EOF
DOCKER_USERNAME=${docker_user}
VERSION=latest
EOF
        fi
        
        # Pull images
        echo -e "${BLUE}Pulling images from Docker Hub...${NC}"
        docker compose pull
        
        # Start services
        echo -e "${BLUE}Starting services...${NC}"
        docker compose up -d
        
        echo ""
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        echo ""
        echo "🌐 Access: http://localhost:3000"
        ;;
        
    5)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice!${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
