# PGAIView License Server

A standalone Flask-based license generation and validation server for PGAIView.

## Features

- **Time-based License Generation**: Creates encrypted license keys with configurable expiration
- **Three License Types**:
  - **Trial**: 10 days validity
  - **Standard**: 60 days (2 months) validity
  - **Enterprise**: 365 days (1 year) validity
- **Secure Encryption**: Uses Fernet symmetric encryption for license keys
- **License Validation**: Validates and decrypts license keys to check validity
- **License Renewal**: Extends existing licenses with new expiration dates
- **REST API**: Simple HTTP endpoints for integration

## Installation

### Option 1: Local Installation

```bash
# Install dependencies
pip install -r license_requirements.txt

# Set environment variables (optional)
export LICENSE_SECRET_KEY="your-secret-key-here"
export ADMIN_KEY="your-admin-password"
export PORT=5000

# Run the server
python license_server.py
```

### Option 2: Docker Installation

```bash
# Build Docker image
docker build -t pgaiview-license-server -f Dockerfile.license .

# Run container
docker run -d \
  -p 5000:5000 \
  -e LICENSE_SECRET_KEY="your-secret-key" \
  -e ADMIN_KEY="your-admin-password" \
  --name license-server \
  pgaiview-license-server
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LICENSE_SECRET_KEY` | Secret key for encryption (keep secure!) | Auto-generated |
| `ADMIN_KEY` | Password for generating licenses | `pgaiview-admin-2024` |
| `PORT` | Server port | `5000` |

## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "PGAIView License Server"
}
```

### 2. Generate License

**POST** `/license/generate`

Generate a new license key.

**Request:**
```json
{
  "deployment_id": "customer-deployment-001",
  "license_type": "standard",
  "admin_key": "pgaiview-admin-2024"
}
```

**Response:**
```json
{
  "license_key": "gAAAAABl...",
  "deployment_id": "customer-deployment-001",
  "license_type": "standard",
  "issue_date": "2024-01-15T10:30:00",
  "expiry_date": "2024-03-15T10:30:00",
  "days_valid": 60
}
```

**License Types:**
- `trial` - 10 days
- `standard` - 60 days (2 months)
- `enterprise` - 365 days (1 year)

### 3. Validate License

**POST** `/license/validate`

Validate a license key and check expiration.

**Request:**
```json
{
  "license_key": "gAAAAABl..."
}
```

**Response (Valid):**
```json
{
  "valid": true,
  "deployment_id": "customer-deployment-001",
  "license_type": "standard",
  "issue_date": "2024-01-15T10:30:00",
  "expiry_date": "2024-03-15T10:30:00",
  "days_remaining": 45,
  "expired": false
}
```

**Response (Expired):**
```json
{
  "valid": false,
  "deployment_id": "customer-deployment-001",
  "license_type": "standard",
  "issue_date": "2024-01-15T10:30:00",
  "expiry_date": "2024-03-15T10:30:00",
  "days_remaining": 0,
  "expired": true
}
```

### 4. Renew License

**POST** `/license/renew`

Renew an existing license (generates new key with fresh expiration).

**Request:**
```json
{
  "current_license_key": "gAAAAABl...",
  "admin_key": "pgaiview-admin-2024"
}
```

**Response:**
```json
{
  "license_key": "gAAAAABm...",
  "deployment_id": "customer-deployment-001",
  "license_type": "standard",
  "issue_date": "2024-03-10T14:20:00",
  "expiry_date": "2024-05-09T14:20:00",
  "days_valid": 60
}
```

### 5. Get License Types

**GET** `/license/types`

Get available license types and configurations.

**Response:**
```json
{
  "trial": {
    "days": 10,
    "description": "Trial License"
  },
  "standard": {
    "days": 60,
    "description": "Standard 2-Month License"
  },
  "enterprise": {
    "days": 365,
    "description": "Enterprise Annual License"
  }
}
```

## Usage Examples

### Generate a Trial License

```bash
curl -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "demo-deployment",
    "license_type": "trial",
    "admin_key": "pgaiview-admin-2024"
  }'
```

### Validate a License

```bash
curl -X POST http://localhost:5000/license/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "gAAAAABl..."
  }'
```

### Renew a License

```bash
curl -X POST http://localhost:5000/license/renew \
  -H "Content-Type: application/json" \
  -d '{
    "current_license_key": "gAAAAABl...",
    "admin_key": "pgaiview-admin-2024"
  }'
```

## Integration with PGAIView

### Backend Configuration

Update your PGAIView backend to validate licenses on startup and for protected routes:

```python
import requests

LICENSE_SERVER_URL = "http://license-server:5000"

def validate_license(license_key):
    response = requests.post(
        f"{LICENSE_SERVER_URL}/license/validate",
        json={"license_key": license_key}
    )
    return response.json()

# Middleware to check license
@app.middleware("http")
async def license_check_middleware(request: Request, call_next):
    # Skip health/license endpoints
    if request.url.path in ["/health", "/license/activate"]:
        return await call_next(request)
    
    # Check license from config/database
    license_key = get_stored_license()
    if not license_key:
        return JSONResponse(
            status_code=403,
            content={"error": "No license activated"}
        )
    
    validation = validate_license(license_key)
    if not validation.get("valid"):
        return JSONResponse(
            status_code=403,
            content={"error": "License expired or invalid"}
        )
    
    return await call_next(request)
```

### Frontend Integration

The SettingsDrawer already includes license activation UI:

1. User enters license key in Settings → License tab
2. Frontend calls `/license/activate` on PGAIView backend
3. Backend validates with license server and stores key
4. All subsequent requests are validated by middleware

## Security Considerations

1. **SECRET_KEY**: Keep the `LICENSE_SECRET_KEY` secure and never share it. Use a strong random key in production.

2. **ADMIN_KEY**: Change the default `ADMIN_KEY` immediately. Use a strong password and rotate regularly.

3. **HTTPS**: Always use HTTPS in production to prevent key interception.

4. **Key Storage**: Store the license server's secret key in a secure vault (AWS Secrets Manager, Azure Key Vault, etc.).

5. **Access Control**: Restrict access to the license server to only authorized systems/networks.

6. **Audit Logging**: Add logging for all license generation and validation requests.

## Deployment Strategies

### Strategy 1: Centralized License Server

- Single license server for all customer deployments
- Each customer deployment validates against central server
- Pros: Easy updates, centralized tracking
- Cons: Requires network connectivity

### Strategy 2: License File Distribution

- Generate licenses offline and distribute as files
- Each deployment validates locally (no network needed)
- Pros: Works offline, more secure
- Cons: Manual distribution

### Strategy 3: Hybrid Approach

- License server for generation only
- Deployments validate locally with cached results
- Periodic online validation (daily/weekly)
- Pros: Best of both worlds

## Monitoring

Monitor these metrics:

- License generation requests
- Validation failures (expired/invalid)
- Deployment ID uniqueness
- License renewal patterns

## Troubleshooting

### License Key Invalid

- Check if SECRET_KEY matches between generation and validation
- Verify license key wasn't truncated or corrupted
- Check for expiration

### Server Won't Start

- Verify all dependencies installed: `pip install -r license_requirements.txt`
- Check port 5000 is available: `lsof -i :5000`
- Verify Python version (3.8+)

### License Expired

- Generate new license with same deployment_id
- Or renew existing license via `/license/renew`

## Development

Run in development mode:

```bash
export FLASK_ENV=development
python license_server.py
```

Run tests:

```bash
# Test health
curl http://localhost:5000/health

# Test license generation
curl -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{"deployment_id": "test", "license_type": "trial", "admin_key": "pgaiview-admin-2024"}'
```

## License

Copyright © 2024 PGAIView. All rights reserved.
