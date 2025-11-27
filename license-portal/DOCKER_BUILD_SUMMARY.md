# License Portal Docker Deployment - Summary

## ✅ Files Created

### 1. `Dockerfile.combined`
**Multi-stage Dockerfile for combined backend + frontend**
- Stage 1: Build Backend (Python 3.11)
- Stage 2: Build Frontend (Node 18)
- Stage 3: Final image with Nginx + Supervisord

**Features:**
- ✅ Optimized multi-stage build
- ✅ Small final image size
- ✅ Both services managed by supervisord
- ✅ Nginx reverse proxy for API
- ✅ Health checks included
- ✅ Production-ready configuration

### 2. `.dockerignore`
**Optimized Docker build context**
- Excludes unnecessary files
- Reduces build time
- Smaller build context

### 3. `build_docker.sh`
**Automated build and deployment script**

**Features:**
- ✅ Builds frontend automatically
- ✅ Creates Docker image
- ✅ Tags versions (latest + 2.0.0)
- ✅ Optionally pushes to registry
- ✅ Starts container with health checks
- ✅ Colorful output with progress

**Usage:**
```bash
# Build and run
./build_docker.sh

# Build only
./build_docker.sh --build-only

# Build, push, and run
./build_docker.sh --push

# Custom port
./build_docker.sh --port 9000
```

### 4. `DOCKER_DEPLOYMENT.md`
**Complete Docker deployment guide**

**Contents:**
- Quick start commands
- Build options
- Manual Docker commands
- Configuration examples
- Docker Compose setup
- Integration with DatabaseAI
- Troubleshooting guide
- Production deployment
- Monitoring and backup

## 🚀 Quick Usage

### Build and Run
```bash
cd license-portal
./build_docker.sh
```

**Access:**
- 🌐 Web UI: http://localhost:8080
- 📚 API: http://localhost:8080/api/docs
- 💚 Health: http://localhost:8080/health

### Manual Build
```bash
# Build image
docker build -f Dockerfile.combined \
  -t opendockerai/pgaiview-license:latest .

# Run container
docker run -d --name pgaiview-license \
  -p 8080:80 \
  opendockerai/pgaiview-license:latest
```

### With Custom Config
```bash
docker run -d --name pgaiview-license \
  -p 8080:80 \
  -v $(pwd)/config.yml:/app/config.yml \
  opendockerai/pgaiview-license:latest
```

## 📊 Architecture

```
                    ┌─────────────────────┐
                    │   Docker Container  │
                    │  Port 80 (Internal) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Supervisord      │
                    │  (Process Manager)  │
                    └──────┬──────┬───────┘
                           │      │
              ┌────────────┘      └────────────┐
              │                                 │
    ┌─────────▼────────┐            ┌─────────▼────────┐
    │      Nginx       │            │   FastAPI        │
    │   Port 80        │◄───────────┤   Port 8000      │
    │   (Frontend)     │   Proxy    │   (Backend API)  │
    └──────────────────┘            └──────────────────┘
              │                                 │
    ┌─────────▼────────┐            ┌─────────▼────────┐
    │  React Build     │            │  License Logic   │
    │  (Static Files)  │            │  Email Service   │
    └──────────────────┘            └──────────────────┘
```

## 🔄 Integration with DatabaseAI

### Same Server
```bash
# License Portal on port 8080
docker run -d --name pgaiview-license -p 8080:80 \
  opendockerai/pgaiview-license:latest

# DatabaseAI on port 80
docker run -d --name pgaiview -p 80:80 \
  -e LICENSE_SERVER_URL=http://localhost:8080 \
  opendockerai/pgaiview:latest
```

### Different Servers
```bash
# License Server (192.168.1.7)
docker run -d --name pgaiview-license -p 8080:80 \
  opendockerai/pgaiview-license:latest

# DatabaseAI Server (192.168.1.10)
docker run -d --name pgaiview -p 80:80 \
  -e LICENSE_SERVER_URL=http://192.168.1.7:8080 \
  opendockerai/pgaiview:latest
```

### Docker Network
```bash
# Create network
docker network create pgaiview-net

# License Portal
docker run -d --name pgaiview-license \
  --network pgaiview-net \
  -p 8080:80 \
  opendockerai/pgaiview-license:latest

# DatabaseAI
docker run -d --name pgaiview \
  --network pgaiview-net \
  -p 80:80 \
  -e LICENSE_SERVER_URL=http://pgaiview-license \
  opendockerai/pgaiview:latest
```

## 📦 Image Details

**Base Image:** `python:3.11-slim`

**Installed Services:**
- Python 3.11 + FastAPI
- Nginx (web server)
- Supervisord (process manager)

**Exposed Ports:**
- Port 80 (HTTP - Frontend + API proxy)

**Image Size:** ~400-500 MB (optimized)

**Layers:**
1. Python base image
2. System dependencies (nginx, supervisor)
3. Python packages
4. Backend application
5. Frontend build
6. Configuration files

## 🎯 Key Features

### Backend (FastAPI)
- ✅ License generation with email
- ✅ License validation
- ✅ Automatic API documentation
- ✅ 2 Uvicorn workers for performance
- ✅ Environment variable support

### Frontend (React)
- ✅ Modern UI with Tailwind CSS
- ✅ Production build optimized
- ✅ Gzip compression enabled
- ✅ Static asset caching
- ✅ Mobile responsive

### Infrastructure
- ✅ Nginx reverse proxy
- ✅ Supervisord for process management
- ✅ Health checks (Docker + API)
- ✅ Graceful shutdown
- ✅ Auto-restart on failure
- ✅ Log streaming to stdout/stderr

## 🔧 Configuration

### Environment Variables
```bash
docker run -d --name pgaiview-license \
  -p 8080:80 \
  -e TZ=America/New_York \
  -e PYTHONUNBUFFERED=1 \
  opendockerai/pgaiview-license:latest
```

### Volume Mounts
```bash
docker run -d --name pgaiview-license \
  -p 8080:80 \
  -v /opt/config.yml:/app/config.yml \
  -v /opt/logs:/app/logs \
  opendockerai/pgaiview-license:latest
```

### Email Configuration
Mount custom `config.yml` with SMTP settings:
```yaml
email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"
```

## 🐛 Troubleshooting

### View Logs
```bash
# All logs
docker logs pgaiview-license -f

# Backend only
docker exec pgaiview-license supervisorctl tail backend

# Nginx only
docker exec pgaiview-license supervisorctl tail nginx
```

### Check Health
```bash
# Docker health
docker inspect pgaiview-license --format='{{.State.Health.Status}}'

# Manual check
curl http://localhost:8080/health
curl http://localhost:8080/api/health
```

### Restart Services
```bash
# Restart entire container
docker restart pgaiview-license

# Restart backend only
docker exec pgaiview-license supervisorctl restart backend

# Restart nginx only
docker exec pgaiview-license supervisorctl restart nginx
```

## 📝 Comparison with DatabaseAI Dockerfile

| Feature | License Portal | DatabaseAI |
|---------|---------------|------------|
| Backend | FastAPI (Python) | FastAPI (PyInstaller) |
| Backend Port | 8000 | 8088 |
| Frontend | React (Vite) | React (Create React App) |
| Process Manager | Supervisord | Supervisord |
| Web Server | Nginx | Nginx |
| Build Type | Source code | Executable |
| Image Size | ~400-500 MB | ~800-1000 MB |
| Workers | 2 Uvicorn workers | 1 executable |

## 🎉 Ready to Deploy!

The license portal is now ready for Docker deployment. You can:

1. **Build locally**: `./build_docker.sh`
2. **Run locally**: `docker run -d -p 8080:80 opendockerai/pgaiview-license:latest`
3. **Push to registry**: `docker push opendockerai/pgaiview-license:latest`
4. **Deploy to production**: Use Docker Compose or Kubernetes

---

**Status:** ✅ Complete  
**Version:** 2.0.0  
**Date:** 2025-11-02  
**Image:** `opendockerai/pgaiview-license:latest`
