#!/bin/bash

# ====================================
# Build and Deploy License Portal Docker Image
# ====================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="opendockerai/pgaiview-license"
VERSION="2.0.0"
CONTAINER_NAME="pgaiview-license"
PORT="8080"  # External port

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  License Portal Docker Build${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Parse arguments
BUILD_ONLY=false
PUSH=false
RUN=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD_ONLY=true
            RUN=false
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-run)
            RUN=false
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}Configuration:${NC}"
echo "  Image: ${IMAGE_NAME}:${VERSION}"
echo "  Container: ${CONTAINER_NAME}"
echo "  Port: ${PORT}"
echo ""

# Step 1: Build frontend
echo -e "${BLUE}[1/5] Building frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi
echo "  Building production bundle..."
npm run build
cd ..
echo -e "${GREEN}✓ Frontend built successfully${NC}"
echo ""

# Step 2: Build Docker image
echo -e "${BLUE}[2/5] Building Docker image...${NC}"
docker build \
    -f Dockerfile.combined \
    -t ${IMAGE_NAME}:${VERSION} \
    -t ${IMAGE_NAME}:latest \
    .

echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""

# Step 3: Tag image
echo -e "${BLUE}[3/5] Tagging image...${NC}"
docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:latest
echo -e "${GREEN}✓ Image tagged: ${IMAGE_NAME}:latest${NC}"
echo ""

# Step 4: Push to registry (optional)
if [ "$PUSH" = true ]; then
    echo -e "${BLUE}[4/5] Pushing to Docker registry...${NC}"
    docker push ${IMAGE_NAME}:${VERSION}
    docker push ${IMAGE_NAME}:latest
    echo -e "${GREEN}✓ Images pushed successfully${NC}"
else
    echo -e "${YELLOW}[4/5] Skipping push (use --push to enable)${NC}"
fi
echo ""

# Step 5: Run container (optional)
if [ "$RUN" = true ]; then
    echo -e "${BLUE}[5/5] Starting container...${NC}"
    
    # Stop and remove existing container
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "  Stopping existing container..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
    fi
    
    # Run new container
    echo "  Starting new container..."
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:80 \
        --restart unless-stopped \
        -e TZ=UTC \
        ${IMAGE_NAME}:latest
    
    # Wait for container to be healthy
    echo "  Waiting for container to be healthy..."
    COUNTER=0
    MAX_ATTEMPTS=30
    
    while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
        if docker ps --filter "name=${CONTAINER_NAME}" --filter "health=healthy" | grep -q ${CONTAINER_NAME}; then
            echo -e "${GREEN}✓ Container is healthy!${NC}"
            break
        fi
        
        if [ $COUNTER -eq $((MAX_ATTEMPTS - 1)) ]; then
            echo -e "${RED}✗ Container health check timeout${NC}"
            echo "Container logs:"
            docker logs ${CONTAINER_NAME} --tail 50
            exit 1
        fi
        
        echo -n "."
        sleep 2
        COUNTER=$((COUNTER + 1))
    done
    
    echo ""
    echo -e "${GREEN}✓ Container started successfully${NC}"
else
    echo -e "${YELLOW}[5/5] Skipping container run (use without --no-run to enable)${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  Build Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "${BLUE}Image Details:${NC}"
docker images ${IMAGE_NAME} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

if [ "$RUN" = true ]; then
    echo -e "${BLUE}Access the License Portal:${NC}"
    echo "  🌐 Web UI:  http://localhost:${PORT}"
    echo "  📚 API:     http://localhost:${PORT}/api/docs"
    echo "  💚 Health:  http://localhost:${PORT}/health"
    echo ""
    echo -e "${BLUE}Container Management:${NC}"
    echo "  View logs:     docker logs ${CONTAINER_NAME} -f"
    echo "  Stop:          docker stop ${CONTAINER_NAME}"
    echo "  Start:         docker start ${CONTAINER_NAME}"
    echo "  Remove:        docker rm -f ${CONTAINER_NAME}"
    echo ""
fi

echo -e "${BLUE}Docker Commands:${NC}"
echo "  Run on different port:  docker run -d --name ${CONTAINER_NAME} -p 9000:80 ${IMAGE_NAME}:latest"
echo "  Push to registry:       docker push ${IMAGE_NAME}:latest"
echo ""

# Show running containers
if [ "$RUN" = true ]; then
    echo -e "${BLUE}Container Status:${NC}"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
fi

echo ""
echo -e "${GREEN}Done! 🎉${NC}"
