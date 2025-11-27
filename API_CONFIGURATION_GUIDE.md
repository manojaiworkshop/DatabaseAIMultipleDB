# API Configuration Guide

## Problem
When running the frontend in Docker, it needs to connect to the backend API. The API URL must be accessible from both:
1. The user's browser (client-side)
2. The Docker container network

## Solution
We use **runtime environment variables** that are injected when the container starts, not during the build process.

---

## How It Works

### 1. Runtime Config Generation
The `docker-entrypoint.sh` script generates `/usr/share/nginx/html/config.js` at container startup:

```javascript
window.ENV = {
  REACT_APP_API_URL: 'http://localhost:8088/api/v1'
};
```

### 2. Frontend Loads Config
The React app loads this config before starting (`index.html`):
```html
<script src="/config.js"></script>
```

### 3. API Service Uses Config
`frontend/src/services/api.js` reads the config:
```javascript
const API_BASE_URL = window.ENV?.REACT_APP_API_URL || 
                     process.env.REACT_APP_API_URL || 
                     'http://localhost:8088/api/v1';
```

---

## Configuration Options

### Option 1: Using docker-compose.yml (Recommended)

Edit `docker-compose.yml`:
```yaml
services:
  frontend:
    environment:
      - REACT_APP_API_URL=http://localhost:8088/api/v1
```

### Option 2: Using .env File

Create `.env` file:
```bash
REACT_APP_API_URL=http://localhost:8088/api/v1
```

Then run:
```bash
docker compose up -d
```

### Option 3: Command Line

```bash
docker compose up -d -e REACT_APP_API_URL=http://192.168.1.100:8088/api/v1
```

Or for standalone container:
```bash
docker run -d \
  -p 3000:80 \
  -e REACT_APP_API_URL=http://localhost:8088/api/v1 \
  yourusername/databaseai-frontend:latest
```

---

## Different Deployment Scenarios

### Scenario 1: Local Development (Same Machine)
**URL:** `http://localhost:8088/api/v1`
```yaml
environment:
  - REACT_APP_API_URL=http://localhost:8088/api/v1
```

### Scenario 2: Docker Desktop (Windows/Mac)
**URL:** `http://host.docker.internal:8088/api/v1`
```yaml
environment:
  - REACT_APP_API_URL=http://host.docker.internal:8088/api/v1
```

### Scenario 3: Docker on Linux
**URL:** `http://172.17.0.1:8088/api/v1` (Docker bridge IP)
```yaml
environment:
  - REACT_APP_API_URL=http://172.17.0.1:8088/api/v1
```

Or use host machine's IP:
```yaml
environment:
  - REACT_APP_API_URL=http://192.168.1.100:8088/api/v1
```

### Scenario 4: Production (Same Domain)
**URL:** `/api/v1` (relative URL, nginx proxy handles routing)
```yaml
environment:
  - REACT_APP_API_URL=/api/v1
```

### Scenario 5: Production (Different Domains)
**URL:** `https://api.yourdomain.com/v1`
```yaml
environment:
  - REACT_APP_API_URL=https://api.yourdomain.com/v1
```

---

## Verification

### 1. Check Generated Config
```bash
# View config.js in container
docker exec databaseai-frontend cat /usr/share/nginx/html/config.js
```

### 2. Check Container Logs
```bash
# Check if config was generated
docker logs databaseai-frontend | grep "Generated config"
```

### 3. Browser Console
Open browser console at `http://localhost:3000`:
```javascript
console.log(window.ENV);
// Output: { REACT_APP_API_URL: "http://localhost:8088/api/v1" }
```

### 4. Network Tab
Open DevTools → Network tab and check API requests:
- Should see requests to the configured API URL
- Check if CORS errors are present

---

## Troubleshooting

### Issue: Frontend can't reach backend

**Symptom:**
```
Network Error
Failed to fetch
```

**Solution:**
1. Check if backend is accessible from your browser:
   ```bash
   curl http://localhost:8088/api/v1/health
   ```

2. If backend works, update frontend API URL:
   ```bash
   # Get your machine's IP
   ip addr show | grep "inet "
   
   # Update docker-compose.yml
   REACT_APP_API_URL=http://192.168.1.100:8088/api/v1
   
   # Restart frontend
   docker compose restart frontend
   ```

### Issue: CORS errors

**Symptom:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
Check `backend/app/main.py` CORS settings:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Config not updating

**Symptom:**
Changed environment variable but frontend still uses old URL

**Solution:**
```bash
# Rebuild and restart frontend
docker compose build frontend
docker compose up -d frontend

# Or restart existing container
docker compose restart frontend
```

---

## Best Practices

1. **Use Environment Variables**: Never hardcode API URLs
2. **Use Relative URLs in Production**: Let nginx proxy handle routing
3. **Use HTTPS in Production**: Always use secure connections
4. **Validate Config**: Check browser console for loaded config
5. **Document Your Setup**: Update `.env.example` with your configuration

---

## Example: Multi-Environment Setup

### Development
```bash
# .env.development
REACT_APP_API_URL=http://localhost:8088/api/v1
```

### Staging
```bash
# .env.staging
REACT_APP_API_URL=https://staging-api.yourdomain.com/v1
```

### Production
```bash
# .env.production
REACT_APP_API_URL=https://api.yourdomain.com/v1
```

Then run:
```bash
# Development
docker compose --env-file .env.development up -d

# Staging
docker compose --env-file .env.staging up -d

# Production
docker compose --env-file .env.production up -d
```

---

## Summary

✅ **Runtime Configuration**: Config generated at container startup, not build time
✅ **Flexible**: Change API URL without rebuilding images
✅ **Environment-Specific**: Different URLs for dev, staging, production
✅ **Easy to Debug**: Check config.js file and browser console
✅ **No Rebuild Required**: Just restart container with new environment variable

**Default Configuration:**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8088`
- API URL: `http://localhost:8088/api/v1`

This setup works perfectly for local development and can be easily adapted for production!
