# PGAIView License System - Quick Reference

## 🚀 Quick Start

### Start License Server
```bash
./start_license_server.sh
# Or manually:
python3 license_server.py
# Or Docker:
docker run -d -p 5000:5000 pgaiview-license-server
```

### Test License Server
```bash
./test_license_server.sh
```

---

## 🔑 Generate Licenses

### Trial License (10 days)
```bash
curl -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "demo-001",
    "license_type": "trial",
    "admin_key": "pgaiview-admin-2024"
  }'
```

### Standard License (2 months)
```bash
curl -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "customer-001",
    "license_type": "standard",
    "admin_key": "pgaiview-admin-2024"
  }'
```

### Enterprise License (1 year)
```bash
curl -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "enterprise-001",
    "license_type": "enterprise",
    "admin_key": "pgaiview-admin-2024"
  }'
```

---

## ✅ Validate License

```bash
curl -X POST http://localhost:5000/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "gAAAAABl..."}'
```

**Response (Valid)**:
```json
{
  "valid": true,
  "days_remaining": 45,
  "expiry_date": "2024-03-15T10:30:00"
}
```

---

## 🔄 Renew License

```bash
curl -X POST http://localhost:5000/license/renew \
  -H "Content-Type: application/json" \
  -d '{
    "current_license_key": "gAAAAABl...",
    "admin_key": "pgaiview-admin-2024"
  }'
```

---

## 📋 License Types

| Type | Duration | Use Case |
|------|----------|----------|
| `trial` | 10 days | Demo/Evaluation |
| `standard` | 60 days | Regular customers |
| `enterprise` | 365 days | Long-term contracts |

---

## 🌐 Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/license/types` | Get license types |
| POST | `/license/generate` | Generate license |
| POST | `/license/validate` | Validate license |
| POST | `/license/renew` | Renew license |

---

## 🔐 Environment Variables

```bash
# Required for production
export ADMIN_KEY="your-strong-password"
export LICENSE_SECRET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

# Optional
export PORT=5000
```

---

## 🐳 Docker Commands

### Build
```bash
docker build -f Dockerfile.license -t pgaiview-license-server .
```

### Run
```bash
docker run -d \
  --name license-server \
  -p 5000:5000 \
  -e ADMIN_KEY="your-admin-key" \
  -e LICENSE_SECRET_KEY="your-secret-key" \
  pgaiview-license-server
```

### Check Logs
```bash
docker logs license-server
```

### Stop/Remove
```bash
docker stop license-server
docker rm license-server
```

---

## 🎯 Common Tasks

### Generate Key for New Customer
```bash
# 1. Generate license
RESPONSE=$(curl -s -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "customer-name-prod",
    "license_type": "standard",
    "admin_key": "pgaiview-admin-2024"
  }')

# 2. Extract license key
echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['license_key'])"

# 3. Send key to customer via secure channel
```

### Check License Expiration
```bash
curl -X POST http://localhost:5000/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "customer-key"}' | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Valid: {data['valid']}, Days: {data['days_remaining']}\")"
```

### Renew Before Expiration
```bash
# Get current key from customer
# Generate new key with same deployment_id
curl -X POST http://localhost:5000/license/renew \
  -H "Content-Type: application/json" \
  -d '{
    "current_license_key": "old-key",
    "admin_key": "pgaiview-admin-2024"
  }'
```

---

## 🛠️ Troubleshooting

### Server Won't Start
```bash
# Check dependencies
pip install -r license_requirements.txt

# Check port
lsof -i :5000

# Check logs
python3 license_server.py
```

### Invalid License Key
```bash
# Verify key not truncated
echo "key" | wc -c

# Check server connectivity
curl http://localhost:5000/health

# Regenerate if needed
```

### License Expired
```bash
# Generate new license with same deployment_id
# Or renew existing license
```

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:5000/health
```

### License Types
```bash
curl http://localhost:5000/license/types
```

### Check Logs
```bash
# If running directly
tail -f license_server.log

# If running in Docker
docker logs -f license-server
```

---

## 🔒 Security Checklist

- [ ] Change default `ADMIN_KEY`
- [ ] Generate unique `LICENSE_SECRET_KEY`
- [ ] Store keys in secure vault
- [ ] Use HTTPS in production
- [ ] Restrict network access to license server
- [ ] Enable rate limiting
- [ ] Set up audit logging
- [ ] Regular key rotation (yearly)
- [ ] Backup license database
- [ ] Monitor failed validation attempts

---

## 📞 Support

For issues or questions:
1. Check logs: `docker logs license-server`
2. Run tests: `./test_license_server.sh`
3. Verify connectivity: `curl http://localhost:5000/health`
4. Check documentation: `LICENSE_SERVER_README.md`

---

## 📚 Related Files

- `license_server.py` - Main server code
- `LICENSE_SERVER_README.md` - Complete documentation
- `LICENSE_SYSTEM_COMPLETE.md` - Full system guide
- `test_license_server.sh` - Automated tests
- `start_license_server.sh` - Quick start script

---

**Default Admin Key**: `pgaiview-admin-2024` ⚠️ Change in production!

**Default Port**: `5000`

**License Format**: Base64-encoded encrypted JSON
