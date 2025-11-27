# License Portal Integration Guide

## Overview
This guide explains how to integrate the new PGAIView License Portal with your DatabaseAI backend and frontend.

## What Changed

### 🔄 Migration Summary
- **Old License Server**: Flask-based server on port 5000
- **New License Portal**: FastAPI backend (port 8000) + React frontend (port 3000)
- **API Endpoint Change**: `/license/validate` → `/api/license/validate`

### ✨ New Features
- 🌐 Beautiful web portal for license management
- 📧 Automatic email delivery of license keys
- 🎨 Modern React + Tailwind CSS UI
- ⚡ FastAPI backend with automatic API docs
- 🔐 No admin key required for users (handled internally)

## Backend Changes

### 1. Updated Files

#### `backend/app/routes/license.py`
**Changes:**
- Default license server URL changed from `http://localhost:5000` → `http://localhost:8000`
- API endpoint updated to use `/api/license/validate`
- Response mapping added to handle new portal's response format

**Key Changes:**
```python
# Old
LICENSE_SERVER_URL = 'http://localhost:5000'
response = requests.post(f"{url}/license/validate", ...)

# New  
LICENSE_SERVER_URL = 'http://localhost:8000'
response = requests.post(f"{url}/api/license/validate", ...)
```

#### `app_config.yml`
**Changes:**
```yaml
license:
  server_url: http://localhost:8000  # Changed from port 5000
```

### 2. API Response Mapping

The new portal returns a different response format:

**New Portal Response:**
```json
{
  "valid": true,
  "deployment_id": "deploy-20251102-ABC123",
  "license_type": "standard",
  "issue_date": "2025-11-02T10:00:00",
  "expiry_date": "2026-01-01T10:00:00",
  "days_remaining": 60,
  "expired": false,
  "error": null
}
```

The backend automatically maps this to the format your application expects.

## Frontend Changes

### 1. Updated Components

#### `frontend/src/components/LicenseModal.js`
**Changes:**
- Default license server URL: `http://localhost:3000` (React portal frontend)
- Opens license portal web UI instead of old Flask server

#### `frontend/src/components/LicenseSettings.js`
**Changes:**
- Default API server URL: `http://localhost:8000` (FastAPI backend)
- Placeholder updated to reflect new port

### 2. User Experience Flow

**Before:**
1. User gets license key from old Flask server
2. Manually enters key in DatabaseAI
3. Backend validates with Flask server (port 5000)

**After:**
1. User visits beautiful web portal at `http://localhost:3000`
2. Enters email and deployment ID
3. Gets license key instantly + receives email
4. Enters key in DatabaseAI (or it's already configured)
5. Backend validates with FastAPI server (port 8000)

## Configuration

### Backend Configuration

**Option 1: Using app_config.yml** (Recommended for persistent storage)
```yaml
license:
  server_url: http://localhost:8000
  key: your-license-key-here
  activated_at: '2025-11-02T10:00:00'
  deployment_id: deploy-20251102-ABC123
  license_type: standard
  expiry_date: '2026-01-01T10:00:00'
```

**Option 2: Using Environment Variable**
```bash
export LICENSE_SERVER_URL=http://localhost:8000
```

**Option 3: Using API**
```bash
# Update license server URL via API
curl -X PUT http://localhost:8000/license/server-config \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://localhost:8000"}'
```

### Frontend Configuration

The frontend automatically loads the license server URL from the backend API, but you can configure defaults:

**LicenseModal.js:**
```javascript
const [licenseServerUrl, setLicenseServerUrl] = useState('http://localhost:3000');
```

**LicenseSettings.js:**
```javascript
const [serverUrl, setServerUrl] = useState('http://localhost:8000');
```

## Testing the Integration

### 1. Start the License Portal

```bash
cd license-portal
./start.sh
```

**Verify:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### 2. Generate a Test License

**Option A: Using Web Portal (Recommended)**
1. Open http://localhost:3000
2. Go to "Generate License" tab
3. Enter email: `test@example.com`
4. Click "Generate" button for deployment ID
5. Select license type (Trial/Standard/Enterprise)
6. Click "Generate License"
7. Copy the license key

**Option B: Using API Directly**
```bash
curl -X POST http://localhost:8000/api/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "deployment_id": "deploy-20251102-TEST123",
    "license_type": "trial"
  }'
```

### 3. Activate License in DatabaseAI

**Option A: Using Frontend UI**
1. Open DatabaseAI at http://localhost:3000 (your main app)
2. Click on Settings → License
3. Paste the license key
4. Click "Activate"

**Option B: Using API**
```bash
curl -X POST http://localhost:8000/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "your-license-key-here"}'
```

### 4. Verify License Status

**Check via API:**
```bash
# Get license info
curl http://localhost:8000/license/info

# Quick validation check
curl http://localhost:8000/license/check
```

**Expected Response:**
```json
{
  "activated": true,
  "valid": true,
  "license_type": "trial",
  "deployment_id": "deploy-20251102-TEST123",
  "expiry_date": "2025-11-12T10:00:00",
  "days_remaining": 10,
  "expired": false
}
```

## Deployment Scenarios

### Local Development
```yaml
license:
  server_url: http://localhost:8000
```

### Docker Compose
```yaml
license:
  server_url: http://license-portal:8000
```

### Production (Separate Server)
```yaml
license:
  server_url: https://license.yourdomain.com
```

### Cloud Deployment
```yaml
license:
  server_url: https://license-api.yourdomain.com
```

## API Endpoints Reference

### License Portal (New)

**Base URL:** `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/license/generate` | POST | Generate new license |
| `/api/license/validate` | POST | Validate license key |
| `/api/license/renew` | POST | Renew existing license |
| `/api/docs` | GET | Interactive API documentation |

### DatabaseAI Backend

**Base URL:** `http://localhost:8000` (your backend)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/license/activate` | POST | Activate license in app |
| `/license/validate` | POST | Validate current license |
| `/license/info` | GET | Get license information |
| `/license/status` | GET | Get license status |
| `/license/check` | GET | Quick validity check |
| `/license/deactivate` | DELETE | Remove license |
| `/license/server-config` | GET | Get license server URL |
| `/license/server-config` | PUT | Update license server URL |

## Troubleshooting

### Issue: "Connection refused" when validating license

**Solution:**
1. Make sure license portal is running: `cd license-portal && ./start.sh`
2. Check port 8000 is not blocked: `netstat -tuln | grep 8000`
3. Verify server URL in config: `curl http://localhost:8000/license/server-config`

### Issue: "Invalid license key"

**Solution:**
1. Verify license was generated with correct deployment ID
2. Check license server URL is correct
3. Test validation directly: 
   ```bash
   curl -X POST http://localhost:8000/api/license/validate \
     -H "Content-Type: application/json" \
     -d '{"license_key": "your-key"}'
   ```

### Issue: Frontend shows wrong license server URL

**Solution:**
1. Update via Settings → License → Server URL
2. Or update via API:
   ```bash
   curl -X PUT http://localhost:8000/license/server-config \
     -d '{"server_url": "http://localhost:8000"}'
   ```

### Issue: Email not being received

**Solution:**
1. Check email is enabled in `license-portal/config.yml`:
   ```yaml
   email:
     enabled: true
   ```
2. Verify SMTP credentials are correct
3. Run email test: `cd license-portal && python3 test_email.py`
4. Check spam/junk folder

## Migration Checklist

- [x] Update backend default license server URL (port 5000 → 8000)
- [x] Update API endpoint path (`/license/validate` → `/api/license/validate`)
- [x] Update frontend default URLs
- [x] Update app_config.yml
- [x] Add response format mapping in backend
- [ ] Test license generation via new portal
- [ ] Test license activation in DatabaseAI
- [ ] Test license validation
- [ ] Update production configuration
- [ ] Update deployment scripts
- [ ] Update documentation

## Benefits of New Portal

### For End Users
✅ Beautiful, intuitive web interface  
✅ Automatic email delivery of licenses  
✅ No admin key required  
✅ Mobile-responsive design  
✅ Copy license key with one click  

### For Administrators
✅ Modern FastAPI backend with auto-docs  
✅ Better error handling and logging  
✅ Configurable SMTP for email  
✅ React frontend for easy customization  
✅ Professional, production-ready code  

### For Developers
✅ Well-documented API  
✅ Pydantic models for validation  
✅ TypeScript-ready React components  
✅ Tailwind CSS for styling  
✅ Easy to extend and maintain  

## Support

For issues or questions:
1. Check API docs: http://localhost:8000/api/docs
2. Review configuration: `app_config.yml` and `license-portal/config.yml`
3. Check logs: `license-portal/logs/`
4. Run test script: `license-portal/test_email.py`

## Related Documentation

- [License Portal README](../license-portal/README.md)
- [Email Setup Guide](../license-portal/EMAIL_SETUP_GUIDE.md)
- [License Portal Changelog](../license-portal/CHANGELOG.md)
- [License Portal Quick Start](../license-portal/QUICKSTART.md)

---

**Last Updated:** 2025-11-02  
**Version:** 2.0.0
