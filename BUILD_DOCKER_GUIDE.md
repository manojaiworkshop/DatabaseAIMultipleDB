# Build Executables & Docker Images - Complete Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Building Standalone Executables](#building-standalone-executables)
3. [Building Docker Images](#building-docker-images)
4. [Publishing to Docker Hub](#publishing-to-docker-hub)
5. [Running with Docker](#running-with-docker)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.11+** (for executable building)
- **Node.js 18+** (for frontend building)
- **Docker 20.10+** (for containerization)
- **Docker Compose 2.0+** (for orchestration)

### Installation Check
```bash
python --version      # Python 3.11.x
node --version        # v18.x.x or higher
docker --version      # Docker version 20.10+
docker-compose --version  # v2.x.x
```

---

## Building Standalone Executables

### Option 1: Build Backend Executable Only

```bash
# Make script executable
chmod +x build_backend_exe.sh

# Build backend
./build_backend_exe.sh
```

**Output:**
- `dist/databaseai-backend` - Standalone executable
- Size: ~50-100 MB (includes all dependencies)

**Run:**
```bash
cd dist
./databaseai-backend
```

### Option 2: Build Both Backend & Frontend

```bash
# Make script executable
chmod +x build_all_executables.sh

# Build everything
./build_all_executables.sh
```

**Output:**
- `dist/databaseai-backend` - Backend executable
- `frontend/build/` - Frontend static files

**Run Backend:**
```bash
cd dist
./databaseai-backend
```

**Serve Frontend:**
```bash
cd frontend/build
python -m http.server 3000
# OR
npx serve -s . -l 3000
```

---

## Building Docker Images

### Quick Build (No Publishing)

```bash
# Build backend image
docker build -f Dockerfile.backend -t databaseai-backend:latest .

# Build frontend image
docker build -f Dockerfile.frontend -t databaseai-frontend:latest .
```

### Build with Docker Compose

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

---

## Publishing to Docker Hub

### Step 1: Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password
```

### Step 2: Run Publish Script

```bash
# Make script executable
chmod +x docker_build_publish.sh

# Run with default version (1.0.0)
./docker_build_publish.sh

# OR specify custom version
./docker_build_publish.sh v1.2.3
```

### Step 3: Follow Interactive Prompts

The script will:
1. ✅ Ask for your Docker Hub username
2. ✅ Build backend image
3. ✅ Build frontend image
4. ✅ Test images locally (optional)
5. ✅ Push to Docker Hub
6. ✅ Tag as `latest` and version-specific tags

### Manual Publishing (Alternative)

```bash
# Set your Docker Hub username
export DOCKER_USERNAME="yourusername"
export VERSION="1.0.0"

# Build images
docker build -f Dockerfile.backend \
  -t ${DOCKER_USERNAME}/databaseai-backend:${VERSION} \
  -t ${DOCKER_USERNAME}/databaseai-backend:latest .

docker build -f Dockerfile.frontend \
  -t ${DOCKER_USERNAME}/databaseai-frontend:${VERSION} \
  -t ${DOCKER_USERNAME}/databaseai-frontend:latest .

# Push to Docker Hub
docker push ${DOCKER_USERNAME}/databaseai-backend:${VERSION}
docker push ${DOCKER_USERNAME}/databaseai-backend:latest
docker push ${DOCKER_USERNAME}/databaseai-frontend:${VERSION}
docker push ${DOCKER_USERNAME}/databaseai-frontend:latest
```

---

## Running with Docker

### Option 1: Docker Compose (Recommended)

**Local Testing:**
```bash
# Start all services (including PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Production (Using Published Images):**
```bash
# Create .env file
cat > .env << EOF
DOCKER_USERNAME=yourusername
VERSION=latest
EOF

# Pull and run
docker-compose pull
docker-compose up -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8088
- API Docs: http://localhost:8088/docs
- PostgreSQL: localhost:5432

### Option 2: Docker Run (Individual Containers)

**Run Backend:**
```bash
docker run -d \
  --name databaseai-backend \
  -p 8088:8088 \
  -v $(pwd)/app_config.yml:/app/app_config.yml:ro \
  yourusername/databaseai-backend:latest
```

**Run Frontend:**
```bash
docker run -d \
  --name databaseai-frontend \
  -p 3000:80 \
  --link databaseai-backend:backend \
  yourusername/databaseai-frontend:latest
```

### Option 3: Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: databaseai-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: databaseai-backend
  template:
    metadata:
      labels:
        app: databaseai-backend
    spec:
      containers:
      - name: backend
        image: yourusername/databaseai-backend:latest
        ports:
        - containerPort: 8088
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: databaseai-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: databaseai-frontend
  template:
    metadata:
      labels:
        app: databaseai-frontend
    spec:
      containers:
      - name: frontend
        image: yourusername/databaseai-frontend:latest
        ports:
        - containerPort: 80
```

---

## Image Details

### Backend Image
- **Base:** `python:3.11-slim` (builder), `debian:bookworm-slim` (runtime)
- **Size:** ~200-300 MB
- **Includes:**
  - Python executable
  - All Python dependencies
  - FastAPI application
  - Configuration files
- **Exposed Port:** 8088
- **Health Check:** `/api/v1/health`

### Frontend Image
- **Base:** `node:18-alpine` (builder), `nginx:alpine` (runtime)
- **Size:** ~50-80 MB
- **Includes:**
  - React production build
  - Nginx web server
  - Optimized static assets
  - API proxy configuration
- **Exposed Port:** 80
- **Health Check:** HTTP GET `/`

---

## Environment Variables

### Backend (`app_config.yml`)
```yaml
server:
  port: 8088
  host: "0.0.0.0"

llm:
  provider: "vllm"
  max_tokens: 4000

vllm:
  api_url: "http://localhost:8000/v1/chat/completions"
```

### Frontend (Build-time)
Create `frontend/.env.production`:
```bash
REACT_APP_API_URL=http://localhost:8088/api/v1
```

### Docker Compose
```bash
DOCKER_USERNAME=yourusername
VERSION=latest
```

---

## Troubleshooting

### Build Issues

**Issue: PyInstaller fails**
```bash
# Solution: Install build dependencies
sudo apt-get install -y gcc g++ make libpq-dev python3-dev

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

**Issue: Frontend build fails**
```bash
# Solution: Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Issue: Docker build fails - out of space**
```bash
# Clean Docker
docker system prune -a --volumes
df -h  # Check disk space
```

### Runtime Issues

**Issue: Backend can't connect to database**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Verify connection in app_config.yml
# Update host to 'postgres' (service name in docker-compose)
```

**Issue: Frontend can't reach backend**
```bash
# Check if backend is running
curl http://localhost:8088/api/v1/health

# Check nginx config in frontend container
docker exec databaseai-frontend cat /etc/nginx/conf.d/default.conf

# Verify network
docker network inspect databaseai_databaseai-network
```

**Issue: Permission denied on executable**
```bash
chmod +x dist/databaseai-backend
```

### Docker Hub Issues

**Issue: Push denied**
```bash
# Re-login
docker logout
docker login

# Verify username
docker info | grep Username
```

**Issue: Image too large**
```bash
# Use multi-stage builds (already implemented)
# Remove unnecessary files in .dockerignore
# Use alpine base images where possible
```

---

## Deployment Checklist

### Before Building
- [ ] Update version in `package.json`
- [ ] Update version in build scripts
- [ ] Test locally
- [ ] Update `app_config.yml`
- [ ] Update `README.md`

### Before Publishing
- [ ] Login to Docker Hub
- [ ] Set DOCKER_USERNAME
- [ ] Set VERSION tag
- [ ] Test images locally
- [ ] Check image sizes

### After Publishing
- [ ] Verify images on Docker Hub
- [ ] Test pulling images
- [ ] Update documentation
- [ ] Tag GitHub release
- [ ] Notify users

---

## Quick Commands Reference

```bash
# Build standalone executables
./build_all_executables.sh

# Build Docker images
docker-compose build

# Publish to Docker Hub
./docker_build_publish.sh v1.0.0

# Run locally
docker-compose up -d

# Stop and remove
docker-compose down -v

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Pull published images
docker pull yourusername/databaseai-backend:latest
docker pull yourusername/databaseai-frontend:latest

# Clean everything
docker-compose down -v
docker system prune -a
rm -rf dist build frontend/build
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/docker-publish.yml
name: Docker Build & Publish

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        run: |
          export VERSION=${GITHUB_REF#refs/tags/}
          ./docker_build_publish.sh $VERSION
```

---

## Support

For issues or questions:
- GitHub Issues: [Your Repository]
- Docker Hub: [Your Docker Hub Profile]
- Email: [Your Email]

---

**Last Updated:** October 26, 2025
