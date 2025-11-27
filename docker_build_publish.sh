#!/bin/bash
# Build and Publish DatabaseAI Docker Images
# This script builds both backend and frontend images and pushes to Docker Hub

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_VERSION="1.0.0"
DEFAULT_DOCKER_USERNAME="your-dockerhub-username"

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Get Docker username
get_docker_username() {
    read -p "Enter your Docker Hub username [$DEFAULT_DOCKER_USERNAME]: " DOCKER_USERNAME
    DOCKER_USERNAME=${DOCKER_USERNAME:-$DEFAULT_DOCKER_USERNAME}
    
    if [ "$DOCKER_USERNAME" = "your-dockerhub-username" ]; then
        print_error "Please set a valid Docker Hub username"
        exit 1
    fi
}

# Get version
get_version() {
    read -p "Enter version tag [$DEFAULT_VERSION]: " VERSION
    VERSION=${VERSION:-$DEFAULT_VERSION}
}

# Docker login
docker_login() {
    print_header "Docker Hub Authentication"
    if docker login; then
        print_success "Successfully logged in to Docker Hub"
    else
        print_error "Docker login failed"
        exit 1
    fi
}

# Build backend image
build_backend() {
    print_header "Building Backend Image"
    print_info "Building databaseai-backend:$VERSION..."
    
    if docker build -f Dockerfile.backend -t ${DOCKER_USERNAME}/databaseai-backend:${VERSION} -t ${DOCKER_USERNAME}/databaseai-backend:latest .; then
        print_success "Backend image built successfully"
        
        # Show image size
        SIZE=$(docker images ${DOCKER_USERNAME}/databaseai-backend:${VERSION} --format "{{.Size}}")
        print_info "Image size: $SIZE"
    else
        print_error "Backend build failed"
        exit 1
    fi
}

# Build frontend image
build_frontend() {
    print_header "Building Frontend Image"
    print_info "Building databaseai-frontend:$VERSION..."
    
    if docker build -f Dockerfile.frontend -t ${DOCKER_USERNAME}/databaseai-frontend:${VERSION} -t ${DOCKER_USERNAME}/databaseai-frontend:latest .; then
        print_success "Frontend image built successfully"
        
        # Show image size
        SIZE=$(docker images ${DOCKER_USERNAME}/databaseai-frontend:${VERSION} --format "{{.Size}}")
        print_info "Image size: $SIZE"
    else
        print_error "Frontend build failed"
        exit 1
    fi
}

# Test images locally
test_images() {
    print_header "Testing Images Locally"
    
    # Create temporary docker compose with test configuration
    export DOCKER_USERNAME
    export VERSION
    
    print_info "Starting containers for testing..."
    if docker compose up -d; then
        print_success "Containers started successfully"
        
        echo ""
        print_info "Waiting for services to be healthy (30 seconds)..."
        sleep 30
        
        # Check backend health
        if curl -f http://localhost:8088/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
        else
            print_warning "Backend health check failed (this might be expected if /health endpoint doesn't exist)"
        fi
        
        # Check frontend
        if curl -f http://localhost:80 > /dev/null 2>&1; then
            print_success "Frontend is accessible"
        else
            print_warning "Frontend not accessible"
        fi
        
        echo ""
        print_info "Services are running. Press Enter to continue with publishing, or Ctrl+C to stop and inspect..."
        read
        
        # Stop test containers
        print_info "Stopping test containers..."
        docker compose down
        print_success "Test containers stopped"
    else
        print_error "Failed to start test containers"
        exit 1
    fi
}

# Push images to Docker Hub
push_images() {
    print_header "Publishing Images to Docker Hub"
    
    # Push backend
    print_info "Pushing backend image (version: $VERSION)..."
    docker push ${DOCKER_USERNAME}/databaseai-backend:${VERSION}
    docker push ${DOCKER_USERNAME}/databaseai-backend:latest
    print_success "Backend image pushed"
    
    # Push frontend
    print_info "Pushing frontend image (version: $VERSION)..."
    docker push ${DOCKER_USERNAME}/databaseai-frontend:${VERSION}
    docker push ${DOCKER_USERNAME}/databaseai-frontend:latest
    print_success "Frontend image pushed"
}

# Generate deployment instructions
generate_deployment_guide() {
    print_header "Generating Deployment Guide"
    
    cat > DOCKER_DEPLOYMENT.md << EOF
# DatabaseAI Docker Deployment Guide

## Published Images

- **Backend**: \`${DOCKER_USERNAME}/databaseai-backend:${VERSION}\`
- **Frontend**: \`${DOCKER_USERNAME}/databaseai-frontend:${VERSION}\`

## Quick Start

### Using Docker Compose (Recommended)

1. **Download the docker compose.yml file**:
   \`\`\`bash
   wget https://raw.githubusercontent.com/manojaiworkshop/DatabaseAI/main/docker compose.yml
   \`\`\`

2. **Create environment file**:
   \`\`\`bash
   export DOCKER_USERNAME=${DOCKER_USERNAME}
   export VERSION=${VERSION}
   \`\`\`

3. **Start the services**:
   \`\`\`bash
   docker compose up -d
   \`\`\`

4. **Access the application**:
   - Frontend: http://localhost
   - Backend API: http://localhost:8088
   - API Docs: http://localhost:8088/docs

### Using Docker CLI

**Backend**:
\`\`\`bash
docker run -d \\
  --name databaseai-backend \\
  -p 8088:8088 \\
  -v \$(pwd)/app_config.yml:/app/app_config.yml:ro \\
  ${DOCKER_USERNAME}/databaseai-backend:${VERSION}
\`\`\`

**Frontend**:
\`\`\`bash
docker run -d \\
  --name databaseai-frontend \\
  -p 80:80 \\
  --link databaseai-backend:backend \\
  ${DOCKER_USERNAME}/databaseai-frontend:${VERSION}
\`\`\`

## Configuration

Mount your custom \`app_config.yml\` to configure:
- LLM provider (OpenAI, vLLM, Ollama)
- Model settings
- Token limits
- CORS settings

\`\`\`bash
docker run -v /path/to/your/app_config.yml:/app/app_config.yml:ro \\
  ${DOCKER_USERNAME}/databaseai-backend:${VERSION}
\`\`\`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DOCKER_USERNAME | - | Your Docker Hub username |
| VERSION | latest | Image version tag |

## Health Checks

Both containers include health checks:
- **Backend**: HTTP GET to \`/health\` endpoint
- **Frontend**: HTTP GET to \`/\`

Check health status:
\`\`\`bash
docker ps
docker inspect databaseai-backend | grep Health
\`\`\`

## Logs

View logs:
\`\`\`bash
# Backend logs
docker logs -f databaseai-backend

# Frontend logs
docker logs -f databaseai-frontend

# Both services (using docker compose)
docker compose logs -f
\`\`\`

## Updating

Pull latest images:
\`\`\`bash
docker pull ${DOCKER_USERNAME}/databaseai-backend:latest
docker pull ${DOCKER_USERNAME}/databaseai-frontend:latest
docker compose up -d
\`\`\`

## Stopping Services

\`\`\`bash
# Using docker compose
docker compose down

# Using docker CLI
docker stop databaseai-backend databaseai-frontend
docker rm databaseai-backend databaseai-frontend
\`\`\`

## Troubleshooting

### Backend not starting
\`\`\`bash
docker logs databaseai-backend
\`\`\`

### Frontend can't connect to backend
- Check network: \`docker network ls\`
- Verify backend is running: \`curl http://localhost:8088/health\`

### Port conflicts
Change ports in docker compose.yml or use:
\`\`\`bash
docker run -p 8089:8088 ${DOCKER_USERNAME}/databaseai-backend:${VERSION}
\`\`\`

## Production Recommendations

1. **Use specific version tags** instead of \`latest\`
2. **Set up SSL/TLS** using reverse proxy (nginx, traefik)
3. **Configure resource limits**:
   \`\`\`yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 2G
   \`\`\`
4. **Use secrets** for API keys (Docker secrets or environment variables)
5. **Enable monitoring** (Prometheus, Grafana)

## Security Notes

- Change default ports in production
- Use environment variables for sensitive data
- Run behind a reverse proxy with SSL
- Regularly update images for security patches

## Support

For issues or questions:
- GitHub: https://github.com/manojaiworkshop/DatabaseAI
- Docker Hub: https://hub.docker.com/u/${DOCKER_USERNAME}

---
Built on: $(date)
Version: ${VERSION}
EOF

    print_success "Deployment guide created: DOCKER_DEPLOYMENT.md"
}

# Main execution
main() {
    clear
    print_header "DatabaseAI Docker Build & Publish"
    
    echo ""
    print_info "This script will:"
    echo "  1. Build Docker images for backend and frontend"
    echo "  2. Test images locally"
    echo "  3. Publish images to Docker Hub"
    echo "  4. Generate deployment documentation"
    echo ""
    
    # Get configuration
    get_docker_username
    get_version
    
    echo ""
    print_info "Configuration:"
    echo "  Docker Hub Username: $DOCKER_USERNAME"
    echo "  Version: $VERSION"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Aborted by user"
        exit 0
    fi
    
    # Execute steps
    docker_login
    build_backend
    build_frontend
    
    echo ""
    read -p "Test images locally before publishing? (recommended) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_images
    fi
    
    echo ""
    read -p "Publish images to Docker Hub? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        push_images
        generate_deployment_guide
        
        print_header "🎉 Success!"
        echo ""
        print_success "Images successfully published to Docker Hub!"
        echo ""
        print_info "Published images:"
        echo "  • ${DOCKER_USERNAME}/databaseai-backend:${VERSION}"
        echo "  • ${DOCKER_USERNAME}/databaseai-backend:latest"
        echo "  • ${DOCKER_USERNAME}/databaseai-frontend:${VERSION}"
        echo "  • ${DOCKER_USERNAME}/databaseai-frontend:latest"
        echo ""
        print_info "View on Docker Hub:"
        echo "  https://hub.docker.com/r/${DOCKER_USERNAME}/databaseai-backend"
        echo "  https://hub.docker.com/r/${DOCKER_USERNAME}/databaseai-frontend"
        echo ""
        print_info "Deployment guide: DOCKER_DEPLOYMENT.md"
        echo ""
    else
        print_warning "Skipped publishing to Docker Hub"
        echo ""
        print_info "Local images are ready. You can publish later with:"
        echo "  docker push ${DOCKER_USERNAME}/databaseai-backend:${VERSION}"
        echo "  docker push ${DOCKER_USERNAME}/databaseai-frontend:${VERSION}"
    fi
}

# Run main function
main
