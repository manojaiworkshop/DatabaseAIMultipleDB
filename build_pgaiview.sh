#!/bin/bash

# ====================================
# Build and Publish PGAIView Docker Image
# ====================================

set -e

# Configuration
IMAGE_NAME="pgaiview"
DOCKER_USERNAME="${DOCKER_USERNAME:-opendockerai}"
VERSION="${VERSION:-1.0.0}"
LATEST_TAG="latest"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}PGAIView Docker Build & Publish${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Step 1: Build the combined Docker image
echo -e "${GREEN}[1/4] Building combined Docker image...${NC}"
docker build -f Dockerfile.combined -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} .
docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} ${DOCKER_USERNAME}/${IMAGE_NAME}:${LATEST_TAG}
echo -e "${GREEN}✓ Image built successfully${NC}"
echo ""

# Step 2: Test the image locally
echo -e "${GREEN}[2/4] Testing image locally...${NC}"
echo "Starting container on port 8080..."
docker run -d \
  --name pgaiview-test \
  -p 8080:80 \
  -v $(pwd)/app_config.yml:/app/app_config.yml:ro \
  ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

echo "Waiting 15 seconds for services to start..."
sleep 15

# Check health
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Health check passed${NC}"
else
  echo -e "${RED}✗ Health check failed${NC}"
  docker logs pgaiview-test
  docker stop pgaiview-test
  docker rm pgaiview-test
  exit 1
fi

# Check frontend
if curl -f http://localhost:8080/ > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Frontend accessible${NC}"
else
  echo -e "${RED}✗ Frontend not accessible${NC}"
  docker logs pgaiview-test
  docker stop pgaiview-test
  docker rm pgaiview-test
  exit 1
fi

echo ""
echo -e "${YELLOW}Testing complete. Container running on http://localhost:8080${NC}"
echo -e "${YELLOW}Press Enter to stop test container and continue with publish, or Ctrl+C to exit${NC}"
read

# Stop and remove test container
docker stop pgaiview-test
docker rm pgaiview-test
echo ""

# Step 3: Login to Docker Hub
echo -e "${GREEN}[3/4] Docker Hub Login${NC}"
if ! docker info | grep -q "Username: ${DOCKER_USERNAME}"; then
  echo "Please login to Docker Hub:"
  docker login
else
  echo -e "${GREEN}✓ Already logged in to Docker Hub${NC}"
fi
echo ""

# Step 4: Push to Docker Hub
echo -e "${GREEN}[4/4] Pushing image to Docker Hub...${NC}"
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${LATEST_TAG}
echo -e "${GREEN}✓ Images pushed successfully${NC}"
echo ""

# Summary
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Build and Publish Complete!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "Images published:"
echo -e "  ${GREEN}${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
echo -e "  ${GREEN}${DOCKER_USERNAME}/${IMAGE_NAME}:${LATEST_TAG}${NC}"
echo ""
echo -e "Image size:"
docker images ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} --format "  {{.Repository}}:{{.Tag}} - {{.Size}}"
echo ""
echo -e "To pull and run:"
echo -e "  ${YELLOW}docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
echo -e "  ${YELLOW}docker run -d -p 80:80 -v \$(pwd)/app_config.yml:/app/app_config.yml:ro ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"
echo ""
echo -e "Or use docker-compose:"
echo -e "  ${YELLOW}docker compose -f docker-compose.pgaiview.yml up -d${NC}"
echo ""
echo -e "${GREEN}Done!${NC}"
