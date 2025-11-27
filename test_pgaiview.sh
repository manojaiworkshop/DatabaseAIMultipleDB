#!/bin/bash

# ====================================
# Quick Test PGAIView Locally
# ====================================

set -e

IMAGE_NAME="pgaiview"
DOCKER_USERNAME="${DOCKER_USERNAME:-opendockerai}"
VERSION="${VERSION:-1.0.0}"
TEST_PORT="${TEST_PORT:-8080}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Testing PGAIView Locally${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Stop any existing test container
if docker ps -a | grep -q pgaiview-test; then
  echo "Stopping existing test container..."
  docker stop pgaiview-test 2>/dev/null || true
  docker rm pgaiview-test 2>/dev/null || true
fi

# Build the image
echo -e "${GREEN}Building image...${NC}"
docker build -f Dockerfile.combined -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} .
echo ""

# Run the container
echo -e "${GREEN}Starting container on port ${TEST_PORT}...${NC}"
docker run -d \
  --name pgaiview-test \
  -p ${TEST_PORT}:80 \
  -v $(pwd)/app_config.yml:/app/app_config.yml:ro \
  ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

echo ""
echo "Waiting for services to start (15 seconds)..."
sleep 15

# Check health
echo ""
echo -e "${GREEN}Running health checks...${NC}"
if curl -f http://localhost:${TEST_PORT}/health > /dev/null 2>&1; then
  echo -e "  ✓ Health endpoint: ${GREEN}OK${NC}"
else
  echo -e "  ✗ Health endpoint: ${RED}FAILED${NC}"
fi

if curl -f http://localhost:${TEST_PORT}/ > /dev/null 2>&1; then
  echo -e "  ✓ Frontend: ${GREEN}OK${NC}"
else
  echo -e "  ✗ Frontend: ${RED}FAILED${NC}"
fi

if curl -f http://localhost:${TEST_PORT}/api/v1/health > /dev/null 2>&1; then
  echo -e "  ✓ Backend API: ${GREEN}OK${NC}"
else
  echo -e "  ✗ Backend API: ${RED}FAILED${NC}"
fi

echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Container Information${NC}"
echo -e "${BLUE}=====================================${NC}"
docker ps --filter name=pgaiview-test --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo -e "${GREEN}Image Size:${NC}"
docker images ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} --format "  {{.Repository}}:{{.Tag}} - {{.Size}}"
echo ""

echo -e "${YELLOW}Application is running at: http://localhost:${TEST_PORT}${NC}"
echo ""
echo "Commands:"
echo -e "  View logs:    ${YELLOW}docker logs -f pgaiview-test${NC}"
echo -e "  Stop:         ${YELLOW}docker stop pgaiview-test${NC}"
echo -e "  Remove:       ${YELLOW}docker rm pgaiview-test${NC}"
echo -e "  Shell access: ${YELLOW}docker exec -it pgaiview-test sh${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to exit (container will keep running)${NC}"
echo ""

# Follow logs
docker logs -f pgaiview-test
