# PGAIView License System - Complete Guide 🔐

## Overview
Your application implements a **license-based authentication system** that validates against a license server before allowing access to protected features.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LICENSE VALIDATION FLOW                       │
└─────────────────────────────────────────────────────────────────┘

1. Frontend Request
   ↓
2. FastAPI Endpoint (with Depends(require_valid_license))
   ↓
3. License Middleware Check
   ↓
4. License Server Validation (HTTP API)
   ↓
5. Config Storage (app_config.yml)
   ↓
6. Access Granted/Denied
```

## Components

### 1. License Server (External Service)
**Location**: Separate service (default: `http://localhost:5000`)
**Purpose**: Central license validation authority

**Endpoints**:
- `POST /license/validate` - Validates license keys
- Returns:
  ```json
  {
    "valid": true,
    "license_type": "trial|professional|enterprise",
    "deployment_id": "deploy-20251027-ULBAA1A7",
    "expiry_date": "2025-11-06T10:30:59.606783",
    "features": ["basic", "advanced", "enterprise"]
  }
  ```

### 2. License Middleware
**File**: `backend/app/middleware/license.py`

#### Key Functions:

**`check_license_valid()`**
```python
def check_license_valid() -> tuple[bool, str, Dict[str, Any]]:
    """
    Check if license is valid
    Returns: (is_valid, message, license_info)
    """
    license_config = load_license_config()
    
    # Check 1: License activated?
    if not license_config.get("activated"):
        return False, "No license activated", {}
    
    # Check 2: License key exists?
    if not license_config.get("license_key"):
        return False, "No license key", {}
    
    # Check 3: Not expired?
    expiration = license_info["expiration_date"]
    if datetime.now() > expiration:
        return False, "License expired", license_info
    
    return True, "Valid", license_info
```

**`require_valid_license()`**
```python
async def require_valid_license(request: Request):
    """
    FastAPI dependency for protected endpoints
    Raises HTTPException 403 if license invalid
    """
    is_valid, message, license_info = check_license_valid()
    
    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "License Required",
                "message": message
            }
        )
    
    return license_info
```

### 3. License Routes
**File**: `backend/app/routes/license.py`

#### Endpoints:

**`POST /api/v1/license/activate`**
- Activates a new license key
- Validates with license server
- Stores in `app_config.yml`

**Request**:
```json
{
  "license_key": "PGAI-XXXX-XXXX-XXXX-XXXX"
}
```

**Response**:
```json
{
  "success": true,
  "message": "License activated successfully",
  "license_info": {
    "license_type": "trial",
    "deployment_id": "deploy-20251027-ULBAA1A7",
    "expiry_date": "2025-11-06T10:30:59.606783",
    "activated_at": "2025-10-27T10:31:13.388449"
  }
}
```

**`POST /api/v1/license/validate`**
- Validates current license
- Checks expiration
- Returns license details

**`GET /api/v1/license/check`**
- Quick check if license is valid
- Returns boolean status

**`POST /api/v1/license/deactivate`**
- Removes license from config
- Clears activation status

### 4. Protected Endpoints
**Example**: `POST /api/v1/query`

```python
@router.post("/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest, 
    agent: SQLAgent = Depends(get_sql_agent),
    license_info: dict = Depends(require_valid_license)  # ← License check
):
    """
    Protected endpoint - requires valid license
    """
    logger.info(f"License type: {license_info.get('license_type')}")
    
    # Process query...
    result = agent.run(question=request.question)
    return result
```

### 5. Configuration Storage
**File**: `app_config.yml`

```yaml
license:
  key: "PGAI-TRIAL-2025-XXXX-XXXX"  # Encrypted/hashed in production
  activated_at: "2025-10-27T10:31:13.388449"
  deployment_id: "deploy-20251027-ULBAA1A7"
  expiry_date: "2025-11-06T10:30:59.606783"
  license_type: "trial"  # trial | professional | enterprise
```

## License Types

### Trial License
- **Duration**: 7-30 days
- **Features**: All basic features
- **Limitations**: Query limit, time-bound
- **Purpose**: Evaluation

### Professional License
- **Duration**: 1 year
- **Features**: All features + advanced analytics
- **Limitations**: Single deployment
- **Support**: Email support

### Enterprise License
- **Duration**: 1-3 years
- **Features**: All features + custom integrations
- **Limitations**: Multiple deployments
- **Support**: Priority support + SLA

## How It Works

### Step 1: License Activation
```bash
# User enters license key in UI
POST /api/v1/license/activate
{
  "license_key": "PGAI-TRIAL-2025-1234-5678"
}

# Backend validates with license server
→ License Server: POST /license/validate

# If valid, store in config
→ app_config.yml: license.key = "PGAI-..."
```

### Step 2: Request Validation
```bash
# User makes query request
POST /api/v1/query
{
  "question": "show all tables"
}

# Middleware checks license
→ require_valid_license() dependency

# Load from config
→ app_config.yml: license.*

# Check expiration
→ Compare license.expiry_date with now()

# If valid: continue
# If invalid: HTTP 403 Forbidden
```

### Step 3: License Expiry
```python
# Automatic check on every request
if datetime.now() > license_info['expiry_date']:
    raise HTTPException(403, "License expired")

# User must renew or reactivate
```

## API Request Flow

```
User Query: "find all network devices"
    ↓
Frontend: POST /api/v1/query
    ↓
FastAPI Router
    ↓
require_valid_license() ← License Dependency
    ↓
check_license_valid()
    ├─ Load app_config.yml
    ├─ Check activated = true
    ├─ Check license_key exists
    ├─ Check expiry_date > now()
    └─ Return (valid, message, license_info)
    ↓
If Valid: Continue to query_database()
    ↓
SQL Agent processes query
    ↓
Return results
    
If Invalid: Raise HTTPException(403)
    ↓
Frontend shows "License Required" error
```

## Configuration

### Environment Variables
```bash
# License server URL
export LICENSE_SERVER_URL="http://license-server:5000"

# Config file location
export CONFIG_FILE="app_config.yml"
```

### app_config.yml Structure
```yaml
license:
  key: "PGAI-XXXX-XXXX-XXXX-XXXX"
  activated_at: "2025-10-27T10:31:13.388449"
  deployment_id: "deploy-20251027-ULBAA1A7"
  expiry_date: "2025-11-06T10:30:59.606783"
  license_type: "trial"

# Other config...
llm:
  provider: ollama
neo4j:
  enabled: true
ontology:
  enabled: true
```

## License Server Integration

### Required License Server Endpoints

**1. Validate License**
```
POST /license/validate
Content-Type: application/json

{
  "license_key": "PGAI-XXXX-XXXX-XXXX-XXXX"
}

Response:
{
  "valid": true,
  "license_type": "trial",
  "deployment_id": "deploy-20251027-ULBAA1A7",
  "expiry_date": "2025-11-06T10:30:59.606783",
  "features": ["query", "ontology", "knowledge_graph"]
}
```

**2. Activate License**
```
POST /license/activate
Content-Type: application/json

{
  "license_key": "PGAI-XXXX-XXXX-XXXX-XXXX",
  "deployment_id": "deploy-20251027-ULBAA1A7"
}

Response:
{
  "success": true,
  "message": "License activated",
  "expiry_date": "2025-11-06T10:30:59.606783"
}
```

## Error Handling

### No License Activated
```json
HTTP 403 Forbidden
{
  "error": "License Required",
  "message": "No license activated. Please activate a valid license."
}
```

### License Expired
```json
HTTP 403 Forbidden
{
  "error": "License Required",
  "message": "License has expired. Please renew your license.",
  "license_info": {
    "license_type": "trial",
    "expiry_date": "2025-11-06T10:30:59.606783"
  }
}
```

### Invalid License Key
```json
HTTP 400 Bad Request
{
  "detail": "Invalid license key"
}
```

## Security Considerations

### Current Implementation
1. ✅ License key stored in config file
2. ✅ Expiration date validation
3. ✅ License server validation
4. ✅ Deployment ID tracking

### Recommended Improvements
1. 🔒 **Encrypt license keys** in config file
2. 🔒 **Add signature verification** (JWT/RSA)
3. 🔒 **Implement license caching** (reduce server calls)
4. 🔒 **Add hardware fingerprinting** (prevent sharing)
5. 🔒 **Use HTTPS** for license server communication
6. 🔒 **Add rate limiting** on license endpoints
7. 🔒 **Implement audit logging** for license events

## Debugging License Issues

### Check Current License Status
```bash
# View config
cat app_config.yml | grep -A 10 license

# Check license endpoint
curl http://localhost:8088/api/v1/license/check

# View logs
grep "License" backend_debug.log
```

### Common Issues

**1. "No license activated"**
- Solution: Activate license via UI or API
- Command: `POST /api/v1/license/activate`

**2. "License has expired"**
- Solution: Renew license or get new trial
- Check: `app_config.yml` → `license.expiry_date`

**3. "License server error"**
- Solution: Check license server is running
- Check: `LICENSE_SERVER_URL` environment variable
- Test: `curl http://localhost:5000/health`

**4. "Invalid license key"**
- Solution: Contact support for valid key
- Verify: License key format `PGAI-XXXX-XXXX-XXXX-XXXX`

## Testing License System

### Manual Testing
```bash
# 1. Activate license
curl -X POST http://localhost:8088/api/v1/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "PGAI-TRIAL-2025-TEST-KEY"}'

# 2. Check status
curl http://localhost:8088/api/v1/license/check

# 3. Make protected query
curl -X POST http://localhost:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "show all tables"}'

# 4. Deactivate
curl -X POST http://localhost:8088/api/v1/license/deactivate
```

### Automated Testing
```python
import requests

# Test license activation
response = requests.post(
    "http://localhost:8088/api/v1/license/activate",
    json={"license_key": "TEST-KEY"}
)
assert response.status_code == 200

# Test protected endpoint
response = requests.post(
    "http://localhost:8088/api/v1/query",
    json={"question": "show tables"}
)
assert response.status_code == 200  # Should work with valid license

# Deactivate
requests.post("http://localhost:8088/api/v1/license/deactivate")

# Should fail now
response = requests.post(
    "http://localhost:8088/api/v1/query",
    json={"question": "show tables"}
)
assert response.status_code == 403  # Forbidden
```

## License Flow Diagram

```
┌──────────────┐
│ User Enters  │
│ License Key  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ POST /license/activate   │
│ {license_key: "..."}     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ License Server           │
│ POST /license/validate   │
└──────┬───────────────────┘
       │
       ├─ Valid ──────────────┐
       │                      ▼
       │              ┌───────────────┐
       │              │ Save to       │
       │              │ app_config.yml│
       │              └───────┬───────┘
       │                      │
       │                      ▼
       │              ┌───────────────┐
       │              │ Return Success│
       │              └───────────────┘
       │
       └─ Invalid ────────────┐
                              ▼
                      ┌───────────────┐
                      │ Return Error  │
                      │ HTTP 400      │
                      └───────────────┘

Later...

┌──────────────┐
│ User Query   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ POST /query              │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ require_valid_license()  │
│ (Dependency)             │
└──────┬───────────────────┘
       │
       ├─ Check activated ───┐
       ├─ Check expiry ──────┤
       └─ Check key ─────────┤
                             │
                             ├─ Valid ────────────┐
                             │                    ▼
                             │            ┌───────────────┐
                             │            │ Process Query │
                             │            │ Return Results│
                             │            └───────────────┘
                             │
                             └─ Invalid ──────────┐
                                                   ▼
                                           ┌───────────────┐
                                           │ HTTP 403      │
                                           │ License Error │
                                           └───────────────┘
```

## Summary

Your licensing system provides:
1. ✅ **License activation** via API
2. ✅ **Expiration checking** on every request
3. ✅ **License server validation** (external authority)
4. ✅ **Protected endpoints** using FastAPI dependencies
5. ✅ **Configuration storage** in YAML
6. ✅ **Multiple license types** (trial, professional, enterprise)

The system ensures that only users with valid, non-expired licenses can access protected features like querying the database.
