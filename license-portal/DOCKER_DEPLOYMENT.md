# License Portal - Docker Deployment

## Quick Start

### Build and Run (Single Command)
```bash
cd license-portal
./build_docker.sh
```

This will:
- Build the frontend
- Create Docker image `opendockerai/pgaiview-license:latest`
- Start container on port 8080

**Access:**
- Web UI: http://localhost:8080
- API Docs: http://localhost:8080/api/docs
- Health: http://localhost:8080/health

## Build Options

### Build Only (Don't Run)
```bash
./build_docker.sh --build-only
```

### Build and Push to Registry
```bash
./build_docker.sh --push
```

### Custom Port
```bash
./build_docker.sh --port 9000
```

## Manual Docker Commands

### Build Image
```bash
docker build -f Dockerfile.combined \
  -t opendockerai/pgaiview-license:latest .
```

### Run Container
```bash
# Port 8080
docker run -d --name pgaiview-license -p 8080:80 \
  opendockerai/pgaiview-license:latest

# Port 80 (default HTTP)
docker run -d --name pgaiview-license -p 80:80 \
  opendockerai/pgaiview-license:latest
```

### Stop/Start Container
```bash
# Stop
docker stop pgaiview-license

# Start
docker start pgaiview-license

# Restart
docker restart pgaiview-license

# Remove
docker rm -f pgaiview-license
```

### View Logs
```bash
# Follow logs
docker logs pgaiview-license -f

# Last 100 lines
docker logs pgaiview-license --tail 100

# Backend only
docker exec pgaiview-license supervisorctl tail backend

# Nginx only
docker exec pgaiview-license supervisorctl tail nginx
```

## Configuration

### Environment Variables
```bash
docker run -d --name pgaiview-license \
  -p 8080:80 \
  -e TZ=America/New_York \
  opendockerai/pgaiview-license:latest
```

### Volume Mounts (Persistent Config)
```bash
docker run -d --name pgaiview-license \
  -p 8080:80 \
  -v $(pwd)/config.yml:/app/config.yml \
  -v $(pwd)/logs:/app/logs \
  opendockerai/pgaiview-license:latest
```

### Custom Email Configuration
```bash
# Create config file
cat > custom_config.yml <<EOF
email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"
EOF

# Run with custom config
docker run -d --name pgaiview-license \
  -p 8080:80 \
  -v $(pwd)/custom_config.yml:/app/config.yml \
  opendockerai/pgaiview-license:latest
```

## Docker Compose (Alternative)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  license-portal:
    image: opendockerai/pgaiview-license:latest
    container_name: pgaiview-license
    ports:
      - "8080:80"
    environment:
      - TZ=UTC
    volumes:
      - ./config.yml:/app/config.yml
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
```

**Usage:**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and restart
docker-compose up -d --build
```

## Integration with DatabaseAI

### Same Host (Docker Network)
```bash
# Create network
docker network create pgaiview-net

# Run license portal
docker run -d --name pgaiview-license \
  --network pgaiview-net \
  -p 8080:80 \
  opendockerai/pgaiview-license:latest

# Run DatabaseAI (configure to use http://pgaiview-license)
docker run -d --name pgaiview \
  --network pgaiview-net \
  -p 80:80 \
  -e LICENSE_SERVER_URL=http://pgaiview-license \
  opendockerai/pgaiview:latest
```

### Separate Hosts
```bash
# On License Server (192.168.1.7)
docker run -d --name pgaiview-license \
  -p 8080:80 \
  opendockerai/pgaiview-license:latest

# On DatabaseAI Server
docker run -d --name pgaiview \
  -p 80:80 \
  -e LICENSE_SERVER_URL=http://192.168.1.7:8080 \
  opendockerai/pgaiview:latest
```

## Health Checks

### Check Container Health
```bash
docker ps --filter "name=pgaiview-license"
docker inspect pgaiview-license --format='{{.State.Health.Status}}'
```

### Manual Health Check
```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/health
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs pgaiview-license

# Check container status
docker ps -a --filter "name=pgaiview-license"

# Inspect container
docker inspect pgaiview-license
```

### Port Already in Use
```bash
# Check what's using the port
lsof -i:8080

# Kill process
kill -9 $(lsof -ti:8080)

# Or use a different port
docker run -d --name pgaiview-license -p 9000:80 \
  opendockerai/pgaiview-license:latest
```

### API Not Responding
```bash
# Check backend logs
docker exec pgaiview-license supervisorctl status backend
docker exec pgaiview-license supervisorctl tail backend

# Restart backend only
docker exec pgaiview-license supervisorctl restart backend
```

### Frontend Not Loading
```bash
# Check nginx logs
docker exec pgaiview-license supervisorctl status nginx
docker exec pgaiview-license supervisorctl tail nginx

# Restart nginx only
docker exec pgaiview-license supervisorctl restart nginx
```

### Email Not Sending
```bash
# Check config inside container
docker exec pgaiview-license cat /app/config.yml

# Test SMTP connection
docker exec -it pgaiview-license python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('SMTP connection successful!')
server.quit()
"
```

## Image Management

### View Images
```bash
docker images opendockerai/pgaiview-license
```

### Remove Old Images
```bash
docker rmi opendockerai/pgaiview-license:old-tag
```

### Clean Up
```bash
# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a

# Complete cleanup
docker system prune -a --volumes
```

## Production Deployment

### Recommended Settings
```bash
docker run -d \
  --name pgaiview-license \
  --restart always \
  -p 8080:80 \
  --memory="512m" \
  --cpus="1.0" \
  -v /opt/pgaiview/config.yml:/app/config.yml \
  -v /opt/pgaiview/logs:/app/logs \
  -e TZ=UTC \
  opendockerai/pgaiview-license:latest
```

### Behind Reverse Proxy (Nginx/Apache)

**Nginx Config:**
```nginx
server {
    listen 80;
    server_name license.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### With SSL/TLS
```bash
docker run -d \
  --name pgaiview-license \
  -p 8080:80 \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  opendockerai/pgaiview-license:latest
```

## Backup & Restore

### Backup Configuration
```bash
docker exec pgaiview-license cat /app/config.yml > backup_config.yml
```

### Restore Configuration
```bash
docker cp backup_config.yml pgaiview-license:/app/config.yml
docker restart pgaiview-license
```

## Monitoring

### Check Resource Usage
```bash
docker stats pgaiview-license
```

### Export Container
```bash
docker export pgaiview-license > license-portal.tar
```

### Save Image
```bash
docker save opendockerai/pgaiview-license:latest | gzip > license-portal-image.tar.gz
```

## Support

For issues or questions:
- View logs: `docker logs pgaiview-license -f`
- Check health: `curl http://localhost:8080/health`
- API docs: http://localhost:8080/api/docs
- GitHub: https://github.com/manojaiworkshop/DatabaseAI

---

**Version:** 2.0.0  
**Last Updated:** 2025-11-02
