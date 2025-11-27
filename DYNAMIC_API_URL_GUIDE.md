# Dynamic API URL Configuration

## Overview
The frontend now automatically detects the server's hostname and constructs the API URL dynamically. This eliminates the need to hardcode `localhost` and makes the application portable across different servers and IP addresses.

## How It Works

### 1. **Automatic Detection (Default)**
The application uses `window.location` to automatically detect:
- **Protocol**: `http://` or `https://`
- **Hostname**: IP address or domain name
- **Port**: Hardcoded to `8088` (backend port)

**Example:**
- If you access: `http://192.168.1.100:3000`
- API URL becomes: `http://192.168.1.100:8088/api/v1`

- If you access: `https://myapp.com`
- API URL becomes: `https://myapp.com:8088/api/v1`

### 2. **Manual Override (Optional)**
You can override the automatic detection by editing `frontend/public/config.js`:

```javascript
window.ENV = {
  REACT_APP_API_URL: 'http://your-server-ip:8088/api/v1'
};
```

## Configuration Priority

The API URL is determined in this order:
1. **Runtime Config** (`window.ENV.REACT_APP_API_URL` in `config.js`)
2. **Build-time Environment** (`process.env.REACT_APP_API_URL`)
3. **Auto-detection** (from `window.location`)

## File Locations

### Frontend API Service
**File**: `frontend/src/services/api.js`

```javascript
const getApiBaseUrl = () => {
  // 1. Check runtime config
  if (window.ENV?.REACT_APP_API_URL) {
    return window.ENV.REACT_APP_API_URL;
  }
  
  // 2. Check build-time env
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // 3. Auto-detect from window.location
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = '8088';
  
  return `${protocol}//${hostname}:${port}/api/v1`;
};
```

### Runtime Configuration
**File**: `frontend/public/config.js`

This file is loaded before React and can be modified at deployment time without rebuilding.

## Deployment Scenarios

### Scenario 1: Local Development
```
Access: http://localhost:3000
API URL: http://localhost:8088/api/v1 (auto-detected)
```

### Scenario 2: Remote Server with IP
```
Access: http://192.168.1.100:3000
API URL: http://192.168.1.100:8088/api/v1 (auto-detected)
```

### Scenario 3: Domain with HTTPS
```
Access: https://myapp.com
API URL: https://myapp.com:8088/api/v1 (auto-detected)
```

### Scenario 4: Custom Backend Location
Edit `config.js`:
```javascript
window.ENV = {
  REACT_APP_API_URL: 'https://api.backend-server.com/api/v1'
};
```

## Docker Deployment

### Method 1: Auto-detection (Recommended)
No changes needed! Access via server IP/domain, and it works automatically.

```bash
# Access frontend
http://YOUR_SERVER_IP:3000

# Backend API automatically detected at
http://YOUR_SERVER_IP:8088/api/v1
```

### Method 2: Custom config.js in Docker
Mount a custom `config.js` file:

```yaml
# docker-compose.yml
services:
  frontend:
    volumes:
      - ./custom-config.js:/usr/share/nginx/html/config.js:ro
```

**custom-config.js:**
```javascript
window.ENV = {
  REACT_APP_API_URL: 'https://api.mycompany.com/api/v1'
};
```

### Method 3: Environment Variables at Build Time
```bash
# Build with custom API URL
REACT_APP_API_URL=https://api.myserver.com/api/v1 npm run build

# Or in Dockerfile
ENV REACT_APP_API_URL=https://api.myserver.com/api/v1
RUN npm run build
```

## Nginx Configuration

The Dockerfile already includes a proxy configuration for `/api/`:

```nginx
location /api/ {
    proxy_pass http://backend:8088;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

This allows both:
1. **Direct Backend Access**: `http://hostname:8088/api/v1/...`
2. **Proxied Access**: `http://hostname:3000/api/...` → backend

## Testing

### Test Auto-detection
1. Build and start containers:
```bash
docker compose build
docker compose up -d
```

2. Access from different machines:
```bash
# From local machine
http://localhost:3000

# From another machine on network
http://192.168.1.100:3000

# From internet (if public IP)
http://203.0.113.45:3000
```

3. Check browser console:
```
DatabaseAI Runtime Config:
  Current Host: 192.168.1.100
  Current Protocol: http:
  Configured API URL: Auto-detect
API Base URL: http://192.168.1.100:8088/api/v1
```

### Test Custom Override
1. Edit `frontend/public/config.js`:
```javascript
window.ENV = {
  REACT_APP_API_URL: 'http://test-server:8088/api/v1'
};
```

2. Rebuild and check console:
```
API Base URL: http://test-server:8088/api/v1
```

## Troubleshooting

### Issue: API calls fail with CORS error
**Cause**: Backend not accessible at detected URL

**Solutions:**
1. Check if backend is running: `curl http://YOUR_IP:8088/api/v1/health`
2. Check firewall allows port 8088
3. Manually set API URL in `config.js`

### Issue: Wrong IP detected
**Cause**: Accessing through proxy or load balancer

**Solution:**
Set explicit URL in `config.js`:
```javascript
window.ENV = {
  REACT_APP_API_URL: 'http://actual-backend-ip:8088/api/v1'
};
```

### Issue: HTTPS frontend, HTTP backend
**Cause**: Mixed content blocked by browser

**Solution:**
1. Enable HTTPS on backend
2. OR use same protocol:
```javascript
window.ENV = {
  REACT_APP_API_URL: 'https://your-backend:8088/api/v1'
};
```

## Benefits

✅ **No hardcoded IPs**: Works on any server automatically
✅ **Development → Production**: Same build works everywhere
✅ **Easy deployment**: No rebuild needed for different environments
✅ **Flexible**: Can override when needed
✅ **Docker-friendly**: Works in containers without modification
✅ **Network portable**: Works on LAN, VPN, or public internet

## Examples

### Example 1: Home Lab
```
Server IP: 192.168.1.50
Access: http://192.168.1.50:3000
API URL: http://192.168.1.50:8088/api/v1 ✓ Auto-detected
```

### Example 2: Cloud Server
```
Server IP: 203.0.113.100
Domain: api.myapp.com → 203.0.113.100
Access: http://api.myapp.com:3000
API URL: http://api.myapp.com:8088/api/v1 ✓ Auto-detected
```

### Example 3: Corporate Network
```
Server: corp-db-server.local
Access: http://corp-db-server.local:3000
API URL: http://corp-db-server.local:8088/api/v1 ✓ Auto-detected
```

### Example 4: Kubernetes
```
Service: databaseai-frontend.default.svc.cluster.local
Access via Ingress: https://databaseai.company.com
API URL: https://databaseai.company.com:8088/api/v1 ✓ Auto-detected
```

## Summary

The dynamic API URL configuration makes DatabaseAI truly portable:
- **No configuration**: Works out-of-the-box on any server
- **No rebuilds**: Same Docker image works everywhere
- **Flexible**: Can override when needed
- **User-friendly**: Just access via IP/domain, everything works!

**Key Files:**
- `frontend/src/services/api.js` - API client with auto-detection
- `frontend/public/config.js` - Runtime configuration (optional override)
- `frontend/public/index.html` - Loads config.js before React

**Default Behavior:**
Access frontend at `http://YOUR_IP:3000` → API automatically uses `http://YOUR_IP:8088/api/v1`

**That's it!** 🎉
