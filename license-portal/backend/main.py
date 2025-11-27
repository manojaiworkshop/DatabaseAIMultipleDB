"""
PGAIView License Portal - FastAPI Backend
Modern REST API for license management
"""
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import os
import json
import base64
import yaml
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import uvicorn
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================================
# Load Configuration
# ============================================================================

def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent.parent / 'config.yml'
    
    # Default configuration
    default_config = {
        'server': {
            'backend': {'host': '0.0.0.0', 'port': 8000, 'reload': True},
            'frontend': {'host': '0.0.0.0', 'port': 3000}
        },
        'security': {
            'admin_key': 'pgaiview-admin-2024',
            'secret_key': '',
            'cors': {
                'enabled': True,
                'allowed_origins': ['*'],
                'allow_credentials': True,
                'allowed_methods': ['*'],
                'allowed_headers': ['*']
            }
        },
        'licenses': {
            'types': {
                'trial': {'days': 10, 'description': 'Trial License - Perfect for testing'},
                'standard': {'days': 60, 'description': 'Standard License - 2 months access'},
                'enterprise': {'days': 365, 'description': 'Enterprise License - Full year'}
            }
        },
        'api': {
            'version_prefix': '/api',
            'docs': {
                'enabled': True,
                'swagger_url': '/api/docs',
                'redoc_url': '/api/redoc',
                'title': 'PGAIView License Portal API',
                'description': 'REST API for generating, validating, and managing PGAIView licenses',
                'version': '2.0.0'
            }
        }
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                # Merge with defaults
                return {**default_config, **config} if config else default_config
        except Exception as e:
            print(f"Warning: Could not load config.yml: {e}")
            print("Using default configuration")
    
    return default_config

# Load configuration
CONFIG = load_config()

# Initialize FastAPI app
app = FastAPI(
    title=CONFIG['api']['docs']['title'],
    description=CONFIG['api']['docs']['description'],
    version=CONFIG['api']['docs']['version'],
    docs_url=CONFIG['api']['docs']['swagger_url'] if CONFIG['api']['docs']['enabled'] else None,
    redoc_url=CONFIG['api']['docs']['redoc_url'] if CONFIG['api']['docs']['enabled'] else None
)

# CORS configuration
if CONFIG['security']['cors']['enabled']:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CONFIG['security']['cors']['allowed_origins'],
        allow_credentials=CONFIG['security']['cors']['allow_credentials'],
        allow_methods=CONFIG['security']['cors']['allowed_methods'],
        allow_headers=CONFIG['security']['cors']['allowed_headers'],
    )

# Secret key for encryption
SECRET_KEY = os.environ.get(
    'LICENSE_SECRET_KEY',
    CONFIG['security']['secret_key'] if CONFIG['security']['secret_key'] else Fernet.generate_key().decode()
)
cipher = Fernet(SECRET_KEY.encode())

# Admin key for authorization
ADMIN_KEY = os.environ.get('ADMIN_KEY', CONFIG['security']['admin_key'])

# License configuration
LICENSE_CONFIG = CONFIG['licenses']['types']

# ============================================================================
# Email Functions
# ============================================================================

def send_license_email(email: str, license_key: str, license_info: dict):
    """
    Send license key via email (placeholder for now)
    Configure SMTP settings in config.yml to enable
    """
    try:
        # Check if email is configured
        email_config = CONFIG.get('email', {})
        if not email_config.get('enabled', False):
            print(f"Email not configured. License would be sent to: {email}")
            print(f"License Key: {license_key[:50]}...")
            return
        
        # Email configuration
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 587)
        sender_email = email_config.get('sender_email')
        sender_password = email_config.get('sender_password')
        
        if not all([smtp_server, sender_email, sender_password]):
            print("Email configuration incomplete. Skipping email notification.")
            return
        
        # Create email
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your PGAIView {license_info['license_type'].capitalize()} License"
        message["From"] = sender_email
        message["To"] = email
        
        # Email body
        text = f"""
Dear Customer,

Your PGAIView license has been generated successfully!

License Details:
- License Type: {license_info['license_type'].capitalize()}
- Deployment ID: {license_info['deployment_id']}
- Valid For: {license_info['days_valid']} days
- Issue Date: {license_info['issue_date']}
- Expiry Date: {license_info['expiry_date']}

Your License Key:
{license_key}

Please keep this license key secure and use it to activate your PGAIView deployment.

Best regards,
PGAIView Team
        """
        
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
      <h2 style="color: #0ea5e9;">Your PGAIView License</h2>
      <p>Dear Customer,</p>
      <p>Your PGAIView license has been generated successfully!</p>
      
      <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #0369a1;">License Details</h3>
        <ul style="list-style: none; padding: 0;">
          <li><strong>License Type:</strong> {license_info['license_type'].capitalize()}</li>
          <li><strong>Deployment ID:</strong> {license_info['deployment_id']}</li>
          <li><strong>Valid For:</strong> {license_info['days_valid']} days</li>
          <li><strong>Issue Date:</strong> {license_info['issue_date']}</li>
          <li><strong>Expiry Date:</strong> {license_info['expiry_date']}</li>
        </ul>
      </div>
      
      <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Your License Key:</h3>
        <p style="font-family: monospace; background: white; padding: 10px; border: 1px solid #ddd; border-radius: 4px; word-break: break-all;">
          {license_key}
        </p>
      </div>
      
      <p style="color: #ef4444; font-size: 14px;">
        ⚠️ Please keep this license key secure and use it to activate your PGAIView deployment.
      </p>
      
      <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
      <p style="font-size: 12px; color: #666;">
        Best regards,<br>
        <strong>PGAIView Team</strong>
      </p>
    </div>
  </body>
</html>
        """
        
        # Attach both text and HTML versions
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        print(f"License email sent successfully to {email}")
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Don't raise exception - license generation should still succeed

# ============================================================================
# Pydantic Models
# ============================================================================

class LicenseGenerateRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    deployment_id: str = Field(..., min_length=3, max_length=100, description="Unique deployment identifier")
    license_type: str = Field(..., description="License type: trial, standard, or enterprise")

class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., description="License key to validate")

class LicenseRenewRequest(BaseModel):
    current_license_key: str = Field(..., description="Current license key to renew")
    admin_key: str = Field(..., description="Admin authentication key")

class LicenseResponse(BaseModel):
    license_key: str
    deployment_id: str
    license_type: str
    issue_date: str
    expiry_date: str
    days_valid: int
    email: Optional[str] = None

class ValidationResponse(BaseModel):
    valid: bool
    deployment_id: Optional[str] = None
    license_type: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    days_remaining: Optional[int] = None
    expired: bool
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str

# ============================================================================
# Helper Functions
# ============================================================================

def verify_admin_key(provided_key: str) -> bool:
    """Verify admin authentication key"""
    return provided_key == ADMIN_KEY

def generate_license_key(deployment_id: str, license_type: str, email: str) -> Dict[str, Any]:
    """Generate an encrypted license key with metadata"""
    if license_type not in LICENSE_CONFIG:
        raise ValueError(f"Invalid license type: {license_type}")
    
    config = LICENSE_CONFIG[license_type]
    expiry_days = config['days']
    
    # Generate dates
    issue_date = datetime.utcnow()
    expiry_date = issue_date + timedelta(days=expiry_days)
    
    # Create license payload
    license_data = {
        'deployment_id': deployment_id,
        'issue_date': issue_date.isoformat(),
        'expiry_date': expiry_date.isoformat(),
        'license_type': license_type,
        'email': email,
        'version': '2.0'
    }
    
    # Encrypt and encode
    license_json = json.dumps(license_data)
    encrypted = cipher.encrypt(license_json.encode())
    license_key = base64.urlsafe_b64encode(encrypted).decode()
    
    return {
        'license_key': license_key,
        'deployment_id': deployment_id,
        'license_type': license_type,
        'issue_date': issue_date.isoformat(),
        'expiry_date': expiry_date.isoformat(),
        'days_valid': expiry_days,
        'email': email
    }

def validate_license_key(license_key: str) -> Dict[str, Any]:
    """Validate and decode a license key"""
    try:
        print(f"[DEBUG] Validating license key - Length: {len(license_key)}, First 50: {license_key[:50]}, Last 50: {license_key[-50:]}")
        
        # Decode and decrypt
        encrypted = base64.urlsafe_b64decode(license_key.encode())
        print(f"[DEBUG] Decoded encrypted data - Length: {len(encrypted)}")
        
        # Create a new cipher instance for each validation to avoid race conditions
        # This prevents thread-safety issues when multiple requests arrive simultaneously
        local_cipher = Fernet(SECRET_KEY.encode())
        decrypted = local_cipher.decrypt(encrypted, ttl=None)
        print(f"[DEBUG] Decrypted successfully - Length: {len(decrypted)}")
        
        license_data = json.loads(decrypted.decode())
        print(f"[DEBUG] Parsed JSON successfully")
        
        # Parse dates (handle both timezone-aware and naive datetimes)
        expiry_date = datetime.fromisoformat(license_data['expiry_date'])
        issue_date = datetime.fromisoformat(license_data['issue_date'])
        
        # Always use naive UTC for consistency (since we generate with naive UTC)
        now = datetime.utcnow()
        
        # Convert aware datetimes to naive UTC if needed
        if expiry_date.tzinfo is not None:
            expiry_date = expiry_date.replace(tzinfo=None)
        if issue_date.tzinfo is not None:
            issue_date = issue_date.replace(tzinfo=None)
        
        # Check validity
        is_valid = now < expiry_date
        
        # Calculate days remaining more accurately
        if is_valid:
            time_remaining = expiry_date - now
            days_remaining = time_remaining.days
            # If less than a day but still valid, show 1 day
            if days_remaining == 0 and time_remaining.total_seconds() > 0:
                days_remaining = 1
        else:
            days_remaining = 0
        
        print(f"✓ Validation success - Valid: {is_valid}, Days: {days_remaining}, Expiry: {expiry_date}, Now: {now}")
        
        return {
            'valid': is_valid,
            'deployment_id': license_data['deployment_id'],
            'license_type': license_data['license_type'],
            'issue_date': issue_date.isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'days_remaining': max(0, days_remaining),
            'expired': not is_valid,
            'error': None
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"✗ License validation error: {str(e)}\n{error_details}")  # Full debug logging
        return {
            'valid': False,
            'deployment_id': None,
            'license_type': None,
            'issue_date': None,
            'expiry_date': None,
            'days_remaining': 0,
            'expired': True,
            'error': f"Invalid license key: {str(e)}"
        }

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "PGAIView License Portal API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="PGAIView License Portal API",
        version="2.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/license/generate", response_model=LicenseResponse)
async def generate_license(request: LicenseGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate a new license key and send it via email
    
    Admin key is used internally for authentication
    """
    # Validate license type
    if request.license_type not in LICENSE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid license type. Available: {', '.join(LICENSE_CONFIG.keys())}"
        )
    
    try:
        license_info = generate_license_key(
            request.deployment_id,
            request.license_type,
            request.email
        )
        
        # Send email in background (non-blocking)
        background_tasks.add_task(
            send_license_email,
            request.email,
            license_info['license_key'],
            license_info
        )
        
        return LicenseResponse(**license_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate license: {str(e)}")

@app.post("/api/license/validate", response_model=ValidationResponse)
async def validate_license(request: LicenseValidateRequest):
    """
    Validate a license key
    
    Returns license details and validity status
    """
    try:
        # Clean the license key (remove whitespace, newlines, etc.)
        clean_key = request.license_key.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        validation_result = validate_license_key(clean_key)
        return ValidationResponse(**validation_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/license/renew", response_model=LicenseResponse)
async def renew_license(request: LicenseRenewRequest):
    """
    Renew an existing license
    
    Generates a new license key with extended validity
    Requires admin authentication
    """
    # Verify admin key
    if not verify_admin_key(request.admin_key):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin key")
    
    # Validate current license
    current_license = validate_license_key(request.current_license_key)
    
    if current_license.get('error'):
        raise HTTPException(status_code=400, detail="Invalid current license key")
    
    try:
        # Generate new license with same details
        new_license = generate_license_key(
            current_license['deployment_id'],
            current_license['license_type'],
            current_license.get('email', 'renewed@license.com')
        )
        return LicenseResponse(**new_license)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to renew license: {str(e)}")

@app.get("/api/license/types")
async def get_license_types():
    """Get available license types and their configurations"""
    return LICENSE_CONFIG

@app.get("/api/stats")
async def get_stats():
    """Get API statistics"""
    return {
        "license_types": len(LICENSE_CONFIG),
        "available_types": list(LICENSE_CONFIG.keys()),
        "api_version": "2.0.0",
        "encryption": "Fernet (AES-128)",
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Get configuration
    host = CONFIG['server']['backend']['host']
    port = int(os.environ.get("PORT", CONFIG['server']['backend']['port']))
    reload = CONFIG['server']['backend']['reload']
    
    print("=" * 60)
    print("  PGAIView License Portal API v2.0")
    print("=" * 60)
    print(f"\n🚀 Starting server on http://{host}:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/api/docs")
    print(f"🔐 Secret Key: {SECRET_KEY[:20]}... (keep secure!)")
    print(f"🔑 Admin Key: {ADMIN_KEY}")
    print("\n📋 Available License Types:")
    for ltype, config in LICENSE_CONFIG.items():
        print(f"   • {ltype.capitalize()}: {config['days']} days - {config['description']}")
    print("\n" + "=" * 60)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
