# 🐳 DatabaseAI - Docker Deployment Guide

Complete guide to building, publishing, and deploying DatabaseAI using Docker and standalone executables.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Build Options](#build-options)
3. [Deployment Methods](#deployment-methods)
4. [Publishing to Docker Hub](#publishing-to-docker-hub)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Fastest Way (Docker Compose)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/DatabaseAI.git
cd DatabaseAI

# 2. Run interactive deployment
./quick_deploy.sh
# Select option 1 (Docker Compose)

# 3. Access application
# Frontend: http://localhost:3000
# Backend:  http://localhost:8088
# API Docs: http://localhost:8088/docs
```

That's it! The application is running with all dependencies.

---

## 🏗️ Build Options

### Option 1: Standalone Executables

**Best for:** Offline deployment, no Docker available

```bash
# Build backend executable
./build_backend_exe.sh

# Build frontend static files
cd frontend
npm install
npm run build
cd ..

# Output:
#   dist/databaseai-backend     (~50-100 MB)
#   frontend/build/             (~5-10 MB)
```

**Run:**
```bash
# Backend
cd dist && ./databaseai-backend

# Frontend (separate terminal)
cd frontend/build && python -m http.server 3000
```

### Option 2: Docker Images (Local)

**Best for:** Development, local testing

```bash
# Build all images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 3: Pull from Docker Hub

**Best for:** Production deployment

```bash
# Create .env file
echo "DOCKER_USERNAME=yourusername" > .env
echo "VERSION=latest" >> .env

# Pull and run
docker-compose pull
docker-compose up -d
```

---

## 🌐 Deployment Methods

### Method 1: Docker Compose (Recommended)

**Architecture:**
```
├── PostgreSQL (port 5432)
├── Backend (port 8088)
└── Frontend (port 3000)
```

**Commands:**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8088/api/v1
- API Documentation: http://localhost:8088/docs
- PostgreSQL: localhost:5432 (user: postgres, password: postgres)

### Method 2: Standalone Containers

**Backend:**
```bash
docker run -d \
  --name databaseai-backend \
  -p 8088:8088 \
  -v $(pwd)/app_config.yml:/app/app_config.yml:ro \
  --restart unless-stopped \
  yourusername/databaseai-backend:latest
```

**Frontend:**
```bash
docker run -d \
  --name databaseai-frontend \
  -p 3000:80 \
  --link databaseai-backend:backend \
  --restart unless-stopped \
  yourusername/databaseai-frontend:latest
```

### Method 3: Kubernetes

```bash
# Apply deployment
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services

# Access via LoadBalancer or NodePort
kubectl get svc databaseai-frontend
```

**Example deployment:** See `DEPLOYMENT_ARCHITECTURE.md`

---

## 📤 Publishing to Docker Hub

### Step 1: Prepare

```bash
# Login to Docker Hub
docker login
# Enter username and password

# Verify login
docker info | grep Username
```

### Step 2: Build & Publish

```bash
# Automatic (Recommended)
./docker_build_publish.sh v1.0.0

# Manual
export DOCKER_USERNAME=yourusername
export VERSION=v1.0.0

docker build -f Dockerfile.backend \
  -t ${DOCKER_USERNAME}/databaseai-backend:${VERSION} .
docker build -f Dockerfile.frontend \
  -t ${DOCKER_USERNAME}/databaseai-frontend:${VERSION} .

docker push ${DOCKER_USERNAME}/databaseai-backend:${VERSION}
docker push ${DOCKER_USERNAME}/databaseai-frontend:${VERSION}
```

### Step 3: Verify

```bash
# Check on Docker Hub
open https://hub.docker.com/u/yourusername

# Test pull
docker pull yourusername/databaseai-backend:v1.0.0
docker pull yourusername/databaseai-frontend:v1.0.0
```

---

## ⚙️ Configuration

### Environment Variables

**Docker Compose (`.env`):**
```bash
DOCKER_USERNAME=yourusername
VERSION=latest
```

**Backend (`app_config.yml`):**
```yaml
server:
  port: 8088
  host: "0.0.0.0"
  workers: 1

llm:
  provider: "vllm"
  max_tokens: 4000

vllm:
  api_url: "http://localhost:8000/v1/chat/completions"
  model: "/models"

# Database connection (for user connections)
# Users will provide these in the UI
```

**Frontend (`frontend/.env.production`):**
```bash
REACT_APP_API_URL=http://localhost:8088/api/v1
```

### Volume Mounts

**Persistent data:**
```yaml
volumes:
  postgres_data:  # Database data
    driver: local
```

**Configuration files:**
```yaml
services:
  backend:
    volumes:
      - ./app_config.yml:/app/app_config.yml:ro
```

---

## 📊 Monitoring

### Health Checks

**Backend:**
```bash
curl http://localhost:8088/api/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "llm_provider": "vllm",
#   "database_connected": false
# }
```

**Frontend:**
```bash
curl http://localhost:3000

# Expected: HTML response with 200 status
```

**Docker Health:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected:
# NAMES                    STATUS
# databaseai-frontend      Up 5 minutes (healthy)
# databaseai-backend       Up 5 minutes (healthy)
# databaseai-postgres      Up 5 minutes (healthy)
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last N lines
docker-compose logs --tail=100 backend

# Since timestamp
docker-compose logs --since 2023-10-01T00:00:00 backend
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Specific container
docker stats databaseai-backend
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: Port Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using port
sudo lsof -i :3000
sudo lsof -i :8088

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

#### Issue 2: Build Fails - Out of Space

**Symptom:**
```
no space left on device
```

**Solution:**
```bash
# Clean Docker
docker system prune -a --volumes

# Check disk space
df -h

# Remove old images
docker images | grep databaseai
docker rmi <image-id>
```

#### Issue 3: Frontend Can't Reach Backend

**Symptom:**
```
Network error when querying database
```

**Solution:**
```bash
# Check if backend is running
docker ps | grep backend

# Check backend logs
docker logs databaseai-backend

# Test backend directly
curl http://localhost:8088/api/v1/health

# Check nginx config
docker exec databaseai-frontend cat /etc/nginx/conf.d/default.conf
```

#### Issue 4: Database Connection Fails

**Symptom:**
```
Could not connect to database
```

**Solution:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs databaseai-postgres

# Test connection
docker exec -it databaseai-postgres psql -U postgres -c "SELECT 1;"

# Restart PostgreSQL
docker-compose restart postgres
```

#### Issue 5: Executable Fails to Run

**Symptom:**
```
./databaseai-backend: error while loading shared libraries
```

**Solution:**
```bash
# Install missing libraries
sudo apt-get install libpq5

# Check dependencies
ldd dist/databaseai-backend

# Rebuild with static linking
./build_backend_exe.sh
```

### Debug Mode

**Enable verbose logging:**
```bash
# Backend
docker-compose up backend  # without -d flag

# Frontend
docker-compose up frontend
```

**Check environment:**
```bash
# Inside container
docker exec -it databaseai-backend env
docker exec -it databaseai-backend ls -la /app
```

---

## 📈 Performance Tuning

### Backend Optimization

**Increase workers (production):**
```yaml
# app_config.yml
server:
  workers: 4  # Number of CPU cores
```

**Resource limits (docker-compose.yml):**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Frontend Optimization

**Enable compression (already configured):**
- Gzip enabled in nginx
- Static assets cached for 1 year
- Minified production build

### Database Optimization

**PostgreSQL tuning:**
```yaml
services:
  postgres:
    command: postgres -c shared_buffers=256MB -c max_connections=200
    shm_size: 256mb
```

---

## 🔒 Security Best Practices

### Production Checklist

- [ ] Change default PostgreSQL password
- [ ] Use secrets management (Docker secrets/Kubernetes secrets)
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up firewall rules
- [ ] Use non-root user (already configured)
- [ ] Scan images for vulnerabilities
- [ ] Keep dependencies updated
- [ ] Enable audit logging
- [ ] Set resource limits
- [ ] Use private Docker registry (optional)

### SSL/TLS Setup

**Add reverse proxy (nginx):**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

---

## 📚 Additional Resources

- **Complete Build Guide:** `BUILD_DOCKER_GUIDE.md`
- **Architecture Diagrams:** `DEPLOYMENT_ARCHITECTURE.md`
- **Quick Summary:** `DOCKER_BUILD_SUMMARY.md`
- **Application README:** `README_APP.md`
- **Logout Implementation:** `SESSION_LOGOUT_IMPLEMENTATION.md`

---

## 🎯 Production Deployment Checklist

Before deploying to production:

- [ ] Test locally with docker-compose
- [ ] Build and tag version (e.g., v1.0.0)
- [ ] Scan images for vulnerabilities
- [ ] Push to Docker Hub/Registry
- [ ] Update environment variables
- [ ] Set resource limits
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Configure SSL/TLS
- [ ] Test health endpoints
- [ ] Load test application
- [ ] Document deployment
- [ ] Train operations team

---

## 📞 Support

For issues or questions:
- **GitHub Issues:** [Your Repository URL]
- **Docker Hub:** [Your Docker Hub Profile]
- **Documentation:** See `.md` files in repository

---

**Version:** 1.0.0  
**Last Updated:** October 26, 2025  
**License:** MIT (or your license)
