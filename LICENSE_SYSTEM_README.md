# 🔐 PGAIView License System

## Overview

The PGAIView license system uses **encrypted time-based licenses** with Fernet symmetric encryption to protect your application from unauthorized use.

## 🔬 Algorithm Explained

### 1. **Encryption Method: Fernet (Symmetric)**
- **Algorithm**: AES-128-CBC + HMAC-SHA256
- **Key Size**: 256-bit (32 bytes)
- **Security**: Industry-standard cryptography from `cryptography` library

### 2. **License Structure**

```
┌─────────────────────────────────────────────────┐
│  Raw License Data (JSON)                         │
├─────────────────────────────────────────────────┤
│  {                                                │
│    "deployment_id": "unique-id",                 │
│    "issue_date": "2025-10-26T00:00:00",         │
│    "expiry_date": "2025-11-05T00:00:00",        │
│    "license_type": "trial",                      │
│    "version": "1.0"                              │
│  }                                                │
└─────────────────────────────────────────────────┘
                    ↓
        ┌──────────────────────┐
        │  JSON.stringify()    │
        └──────────────────────┘
                    ↓
        ┌──────────────────────┐
        │  Fernet Encryption   │
        │  (AES + HMAC)        │
        └──────────────────────┘
                    ↓
        ┌──────────────────────┐
        │  Base64 URL Encoding │
        └──────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Final License Key                               │
│  gAAAAABmTx8Y2F... (base64 encoded)             │
└─────────────────────────────────────────────────┘
```

### 3. **Validation Flow**

```
License Key Input
    ↓
Base64 Decode
    ↓
Fernet Decrypt
    ↓
Parse JSON
    ↓
Check Expiration Date
    ↓
Valid? → Allow Access
Invalid? → Show License Modal
```

## 🛠️ How to Use

### Step 1: Start License Server

```bash
./start_license_server.sh
```

Or manually:
```bash
python3 license_server.py
```

The server will run on **http://localhost:5000**

### Step 2: Generate License

**Option A: Using Script (Recommended)**
```bash
./generate_license.sh
```

Then follow the interactive prompts:
1. Select license type (trial/standard/enterprise)
2. Enter deployment ID (or use auto-generated)
3. Copy the generated license key

**Option B: Using API**
```bash
curl -X POST http://localhost:5000/license/generate \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_id": "my-deployment",
    "license_type": "trial",
    "admin_key": "pgaiview-admin-2024"
  }'
```

### Step 3: Activate License in Application

1. Open PGAIView (http://localhost/)
2. Connect to database
3. Try to send a message
4. License modal appears
5. Paste your license key
6. Click "Activate"
7. ✅ Chat functionality unlocked!

### Step 4: Validate License (Optional)

```bash
./validate_license.sh
```

Or using API:
```bash
curl -X POST http://localhost:5000/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "YOUR_LICENSE_KEY_HERE"}'
```

## 📋 License Types

| Type       | Duration | Description              | Use Case                |
|------------|----------|--------------------------|-------------------------|
| Trial      | 10 days  | Free trial license       | Testing & Evaluation    |
| Standard   | 60 days  | 2-month license          | Short-term projects     |
| Enterprise | 365 days | Annual license           | Production deployments  |

## 🔒 Security Features

### 1. **Encrypted Storage**
- License data encrypted with Fernet (AES-128 + HMAC-SHA256)
- Cannot be forged without the secret key
- Tamper-proof with HMAC verification

### 2. **Time-Based Expiration**
- Expiration date embedded in encrypted payload
- Server validates expiration on each request
- Cannot be modified without invalidating signature

### 3. **Admin Key Protection**
- License generation requires admin key
- Default: `pgaiview-admin-2024` (change in production!)
- Prevents unauthorized license generation

### 4. **Deployment ID Tracking**
- Each license tied to unique deployment
- Helps track license usage
- Can be used for license auditing

## 🎯 API Endpoints

### Health Check
```bash
GET http://localhost:5000/health
```

### Generate License
```bash
POST http://localhost:5000/license/generate
{
  "deployment_id": "string",
  "license_type": "trial|standard|enterprise",
  "admin_key": "string"
}
```

### Validate License
```bash
POST http://localhost:5000/license/validate
{
  "license_key": "string"
}
```

### Renew License
```bash
POST http://localhost:5000/license/renew
{
  "current_license_key": "string",
  "admin_key": "string"
}
```

### Get License Types
```bash
GET http://localhost:5000/license/types
```

## 🔐 Algorithm Deep Dive

### Fernet Encryption Process

1. **Key Generation**
   ```python
   SECRET_KEY = Fernet.generate_key()  # 32 bytes (256 bits)
   cipher = Fernet(SECRET_KEY)
   ```

2. **Encryption**
   ```python
   # Create license data
   license_data = {
       "deployment_id": "xyz",
       "expiry_date": "2025-11-05T00:00:00",
       ...
   }
   
   # Convert to JSON
   license_json = json.dumps(license_data)
   
   # Encrypt with Fernet
   encrypted = cipher.encrypt(license_json.encode())
   
   # Base64 encode for transport
   license_key = base64.urlsafe_b64encode(encrypted).decode()
   ```

3. **Decryption & Validation**
   ```python
   # Decode from base64
   encrypted = base64.urlsafe_b64decode(license_key)
   
   # Decrypt with Fernet
   decrypted = cipher.decrypt(encrypted)  # Throws if tampered!
   
   # Parse JSON
   license_data = json.loads(decrypted.decode())
   
   # Check expiration
   expiry_date = datetime.fromisoformat(license_data['expiry_date'])
   is_valid = datetime.utcnow() < expiry_date
   ```

### Why Fernet?

1. **Authenticated Encryption**: Combines encryption (AES) + authentication (HMAC)
2. **Tamper-Proof**: Any modification invalidates the license
3. **Industry Standard**: Used by major applications and services
4. **Simple API**: Easy to implement and maintain
5. **Version Tracking**: Includes version bytes for future compatibility

## 🚨 Important Security Notes

### For Production:

1. **Change Admin Key**
   ```bash
   export ADMIN_KEY="your-secure-random-key-here"
   ```

2. **Store Secret Key Securely**
   ```bash
   export LICENSE_SECRET_KEY="your-fernet-key-here"
   ```
   
   Generate a secure key:
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```

3. **Use HTTPS**
   - Never send licenses over plain HTTP in production
   - Use SSL/TLS certificates

4. **Implement Rate Limiting**
   - Prevent brute force attacks on license validation
   - Use tools like `Flask-Limiter`

5. **Log License Events**
   - Track activations, validations, failures
   - Monitor for suspicious activity

## 📊 File Structure

```
DATABASEAI/
├── license_server.py          # Main license server
├── start_license_server.sh    # Start server script
├── generate_license.sh        # Generate license script
├── validate_license.sh        # Validate license script
├── license_config.yml         # Active license config (generated)
└── backend/
    └── app/
        └── middleware/
            └── license.py     # License validation middleware
```

## 🎓 Example Workflow

```bash
# Terminal 1: Start License Server
./start_license_server.sh

# Terminal 2: Generate a Trial License
./generate_license.sh
# Select: 1 (Trial)
# Copy the generated license key

# Terminal 3: Start Application
docker start pgaiview

# Browser: Open http://localhost/
# 1. Connect to database
# 2. Try to send message
# 3. Paste license key in modal
# 4. Click Activate
# 5. ✅ Start chatting!
```

## 🔧 Troubleshooting

### Error: "Request failed with status code 400"
**Cause**: License server not running
**Solution**: 
```bash
./start_license_server.sh
```

### Error: "Invalid license key"
**Causes**:
1. License expired
2. Wrong license key
3. Secret key changed on server

**Solution**: Generate a new license

### Error: "Unauthorized"
**Cause**: Wrong admin key
**Solution**: Check `ADMIN_KEY` environment variable

## 📝 License Example

```
License Type: trial
Valid for: 10 days
License Key:
gAAAAABmTx8Y2F5vZ3VsYXJ0ZXh0aGVyZSB3aXRoIG1vcmUgZGF0YSB0byBl
bmNyeXB0IHRoYXQgd2lsbCBiZSBsb25nZXIgdGhhbiB0aGUga2V5IHNpemU=
```

This key contains:
- Deployment ID: deploy-20251026-aBc123Xy
- Issue Date: 2025-10-26T00:00:00
- Expiry Date: 2025-11-05T00:00:00
- Type: trial
- Version: 1.0

All encrypted with Fernet and base64 encoded!

## 🎉 That's It!

You now have a complete understanding of the PGAIView license system. The algorithm is secure, simple, and effective at protecting your application from unauthorized use.

For questions or issues, check the logs:
```bash
docker logs pgaiview
tail -f /var/log/license_server.log
```
