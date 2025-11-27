# PGAIView - Combined Docker Image

## 🎯 Overview

**PGAIView** is a single Docker image that bundles both the backend FastAPI server and frontend React application into one container, making deployment simple and efficient.

### Key Features
- ✅ **Single Container**: Backend + Frontend in one image
- ✅ **Nginx Reverse Proxy**: Frontend on port 80, API proxied to `/api/`
- ✅ **Supervisor**: Manages both services automatically
- ✅ **Small Size**: Optimized multi-stage build (~150-200MB)
- ✅ **Production Ready**: Health checks, auto-restart, proper logging
- ✅ **Easy Deployment**: Just expose port 80

---

## 📦 What's Inside

```
┌─────────────────────────────────────┐
│         PGAIView Container          │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   Frontend   │  │   Backend   │ │
│  │  (React App) │  │  (FastAPI)  │ │
│  │              │  │             │ │
│  │  Port: 80    │  │ Port: 8088  │ │
│  └──────────────┘  └─────────────┘ │
│         │                  │        │
│         └─── Nginx ────────┘        │
│            (Reverse Proxy)          │
│                                     │
│       Managed by Supervisord        │
└─────────────────────────────────────┘
```

### Services Included
1. **Backend**: FastAPI executable (PyInstaller)
2. **Frontend**: React build served by Nginx
3. **Nginx**: Reverse proxy and web server
4. **Supervisord**: Process manager for both services

---

## 🚀 Quick Start

### 1. Build Locally
```bash
docker build -f Dockerfile.combined -t opendockerai/pgaiview:1.0.0 .
```

### 2. Test Locally
```bash
# Using test script (recommended)
./test_pgaiview.sh

# Or manually
docker run -d \
  --name pgaiview \
  -p 8080:80 \
  -v $(pwd)/app_config.yml:/app/app_config.yml:ro \
  opendockerai/pgaiview:1.0.0
```

Access at: **http://localhost:8080**

### 3. Build and Publish
```bash
# Complete build, test, and publish pipeline
./build_pgaiview.sh

# Or manually
docker build -f Dockerfile.combined -t opendockerai/pgaiview:1.0.0 .
docker tag opendockerai/pgaiview:1.0.0 opendockerai/pgaiview:latest
docker push opendockerai/pgaiview:1.0.0
docker push opendockerai/pgaiview:latest
```

---

## 📋 Using Docker Compose

```bash
# Start
docker compose -f docker-compose.pgaiview.yml up -d

# View logs
docker compose -f docker-compose.pgaiview.yml logs -f

# Stop
docker compose -f docker-compose.pgaiview.yml down
```

Access at: **http://localhost** (port 80)

---

## 🌐 Deployment

### Pull from Docker Hub
```bash
docker pull opendockerai/pgaiview:latest
```

### Run in Production
```bash
docker run -d \
  --name pgaiview \
  --restart unless-stopped \
  -p 80:80 \
  -v /path/to/app_config.yml:/app/app_config.yml:ro \
  opendockerai/pgaiview:latest
```

### Environment Variables
- `PYTHONUNBUFFERED=1` - Python logging (already set)
- Configure LLM settings in `app_config.yml`

---

## 🔧 Architecture Details

### Multi-Stage Build

#### Stage 1: Backend Builder
- Base: `python:3.11-slim`
- Installs dependencies
- Builds backend executable with PyInstaller
- Output: `/build/dist/backend` (~50-100MB)

#### Stage 2: Frontend Builder
- Base: `node:18-alpine`
- npm install and build
- Output: `/build/build` (optimized React bundle)

#### Stage 3: Final Image
- Base: `nginx:alpine` (~7MB)
- Copies backend executable
- Copies frontend build
- Installs Python runtime + libpq
- Configures Nginx reverse proxy
- Sets up Supervisord
- Final size: ~150-200MB

### Port Mapping
- **Port 80**: Main access point
  - `/` → Frontend (React app)
  - `/api/` → Backend API (proxied to localhost:8088)
  - `/health` → Health check endpoint

### Internal Services
- **Backend**: Runs on localhost:8088 (internal only)
- **Frontend**: Served by Nginx on port 80
- **Nginx**: Routes requests to appropriate service

---

## 🏥 Health Checks

### Container Health
```bash
docker inspect --format='{{.State.Health.Status}}' pgaiview
```

### Manual Checks
```bash
# Overall health
curl http://localhost/health

# Backend API
curl http://localhost/api/v1/health

# Frontend
curl http://localhost/
```

---

## 📊 Monitoring

### View Logs
```bash
# All logs
docker logs -f pgaiview

# Backend only
docker exec pgaiview supervisorctl tail -f backend

# Nginx only
docker exec pgaiview supervisorctl tail -f nginx
```

### Service Status
```bash
docker exec pgaiview supervisorctl status
```

Expected output:
```
backend    RUNNING   pid 12, uptime 0:05:23
nginx      RUNNING   pid 13, uptime 0:05:23
```

---

## 🛠️ Troubleshooting

### Issue: Container fails to start
```bash
# Check logs
docker logs pgaiview

# Check supervisor status
docker exec pgaiview supervisorctl status
```

### Issue: Backend not responding
```bash
# Restart backend only
docker exec pgaiview supervisorctl restart backend

# Check backend logs
docker exec pgaiview supervisorctl tail backend
```

### Issue: Frontend not loading
```bash
# Check nginx config
docker exec pgaiview cat /etc/nginx/conf.d/default.conf

# Restart nginx
docker exec pgaiview supervisorctl restart nginx
```

### Issue: Can't connect to database
- Ensure PostgreSQL is accessible from container
- Check `app_config.yml` configuration
- For localhost PostgreSQL, use host.docker.internal:
  ```yaml
  database:
    host: host.docker.internal
    port: 5432
  ```

---

## 📝 Configuration

### app_config.yml
Mount your configuration file:
```bash
-v /path/to/app_config.yml:/app/app_config.yml:ro
```

Example config:
```yaml
llm_providers:
  openai:
    api_key: "your-key"
    model: "gpt-4"
  
database:
  host: "host.docker.internal"
  port: 5432
```

---

## 🔄 Updates

### Update to New Version
```bash
# Pull latest
docker pull opendockerai/pgaiview:latest

# Stop old container
docker stop pgaiview
docker rm pgaiview

# Start new container
docker run -d \
  --name pgaiview \
  --restart unless-stopped \
  -p 80:80 \
  -v $(pwd)/app_config.yml:/app/app_config.yml:ro \
  opendockerai/pgaiview:latest
```

### Rebuild from Source
```bash
# Pull latest code
git pull

# Rebuild
docker build -f Dockerfile.combined -t opendockerai/pgaiview:latest .
```

---

## 📈 Performance

### Resource Usage
- **CPU**: Low (idle) to Medium (during queries)
- **RAM**: ~200-500MB
- **Disk**: ~150-200MB (image)

### Optimization Tips
1. Use environment-specific `app_config.yml`
2. Enable connection pooling for PostgreSQL
3. Configure nginx caching for static assets
4. Use Docker volume for config (faster than bind mount)

---

## 🎨 UI Changes

The application UI has been rebranded from "DatabaseAI" to "PGAIView":
- **Title**: PGAIView
- **Description**: Chat with your PostgreSQL database using natural language
- **All references updated** in frontend code

---

## 🔐 Security

### Best Practices
1. **Never expose secrets in image**: Use volume-mounted config
2. **Use read-only volumes**: `-v config.yml:/app/config.yml:ro`
3. **Run as non-root** (future improvement)
4. **Use specific versions**: `pgaiview:1.0.0` instead of `latest`
5. **Enable HTTPS**: Use reverse proxy (nginx/traefik) in front

### Network Isolation
```yaml
# In production, use custom networks
networks:
  frontend-network:
    driver: bridge
  backend-network:
    driver: bridge
    internal: true
```

---

## 📚 Scripts Reference

### test_pgaiview.sh
Quick local testing with automatic health checks:
```bash
./test_pgaiview.sh
```

### build_pgaiview.sh
Complete build and publish pipeline:
```bash
./build_pgaiview.sh
```
Includes:
1. Build image
2. Test locally (interactive)
3. Docker Hub login
4. Push to registry

---

## 🆚 Comparison: Single vs Separate Containers

| Feature | Combined (PGAIView) | Separate |
|---------|---------------------|----------|
| Containers | 1 | 2 |
| Ports | 80 only | 3000 + 8088 |
| Deployment | Simpler | More flexible |
| Scaling | Scale together | Scale independently |
| Size | ~200MB | ~170MB total |
| Management | Easier | More control |
| Best For | Simple deployments | Complex architectures |

---

## ✅ Checklist for Deployment

- [ ] Build image successfully
- [ ] Test locally on port 8080
- [ ] Verify health checks pass
- [ ] Configure app_config.yml
- [ ] Test database connection
- [ ] Push to Docker Hub
- [ ] Test pull from registry
- [ ] Deploy to production server
- [ ] Verify external access
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Document deployment

---

## 🎯 Next Steps

1. **Test locally**: Run `./test_pgaiview.sh`
2. **Publish**: Run `./build_pgaiview.sh`
3. **Deploy**: Pull and run on production server
4. **Monitor**: Check logs and health status
5. **Scale**: Add load balancer if needed

---

## 📞 Support

For issues or questions:
- Check logs: `docker logs pgaiview`
- View this guide: `PGAIVIEW_README.md`
- Check supervisor: `docker exec pgaiview supervisorctl status`

---

**Version**: 1.0.0  
**Image**: `opendockerai/pgaiview:latest`  
**Size**: ~150-200MB  
**Status**: ✅ Production Ready
