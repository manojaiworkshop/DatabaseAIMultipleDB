"""
License management routes for PGAIView
Handles license activation, validation, and information retrieval
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import yaml
import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/license", tags=["license"])

# Configuration file
CONFIG_FILE = 'app_config.yml'

def get_license_server_url():
    """Get license server URL from config or environment"""
    config = load_config()
    # Check config first, then environment variable, then default to new portal
    return config.get('license', {}).get('server_url') or os.environ.get('LICENSE_SERVER_URL', 'http://localhost:8000')

class LicenseActivateRequest(BaseModel):
    license_key: str

class LicenseValidateRequest(BaseModel):
    license_key: str = None

def load_config():
    """Load configuration from YAML file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config):
    """Save configuration to YAML file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_stored_license():
    """Get stored license key from config"""
    config = load_config()
    return config.get('license', {}).get('key')


def validate_license_with_server(license_key):
    """Validate license key with license server (new portal API)"""
    try:
        license_server_url = get_license_server_url()
        # Use new portal API endpoint
        response = requests.post(
            f"{license_server_url}/api/license/validate",
            json={"license_key": license_key},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            # Map new portal response format to old format
            return {
                "valid": data.get("valid", False),
                "deployment_id": data.get("deployment_id"),
                "license_type": data.get("license_type"),
                "expiry_date": data.get("expiry_date"),
                "issue_date": data.get("issue_date"),
                "days_remaining": data.get("days_remaining", 0),
                "expired": data.get("expired", True),
                "error": data.get("error")
            }
        return {"valid": False, "error": "License server error"}
    except Exception as e:
        logger.error(f"License validation error: {e}")
        return {"valid": False, "error": str(e)}

@router.post("/activate")
async def activate_license(request: LicenseActivateRequest):
    """
    Activate a license key
    Validates the key with license server and stores it in config
    """
    license_key = request.license_key.strip()
    
    if not license_key:
        raise HTTPException(status_code=400, detail="License key is required")
    
    # Validate with license server
    validation = validate_license_with_server(license_key)
    
    if not validation.get('valid'):
        raise HTTPException(
            status_code=400,
            detail=validation.get('error', 'Invalid license key')
        )
    
    # Store in app config
    config = load_config()
    if 'license' not in config:
        config['license'] = {}
    
    config['license']['key'] = license_key
    config['license']['activated_at'] = datetime.utcnow().isoformat()
    config['license']['deployment_id'] = validation.get('deployment_id')
    config['license']['license_type'] = validation.get('license_type')
    config['license']['expiry_date'] = validation.get('expiry_date')
    
    if not save_config(config):
        raise HTTPException(status_code=500, detail="Failed to save license")
    
    # Also save to license_config.yml for middleware access
    try:
        from ..middleware.license import save_license_config
        license_config = {
            "activated": True,
            "license_key": license_key,
            "activated_at": datetime.utcnow().isoformat(),
            "license_info": {
                "license_type": validation.get('license_type'),
                "expiration_date": validation.get('expiry_date'),
                "days_remaining": validation.get('days_remaining'),
                "deployment_id": validation.get('deployment_id')
            }
        }
        save_license_config(license_config)
    except Exception as e:
        logger.error(f"Failed to save license config: {e}")
    
    return {
        "success": True,
        "message": "License activated successfully",
        "license_info": {
            "valid": True,
            "license_type": validation.get('license_type'),
            "expiry_date": validation.get('expiry_date'),
            "days_remaining": validation.get('days_remaining')
        }
    }

@router.post("/validate")
async def validate_current_license(request: LicenseValidateRequest = None):
    """
    Validate the current license
    Checks stored license or provided license key
    """
    license_key = None
    
    if request and request.license_key:
        license_key = request.license_key
    else:
        license_key = get_stored_license()
    
    if not license_key:
        return {
            "valid": False,
            "error": "No license activated"
        }
    
    validation = validate_license_with_server(license_key)
    return validation

@router.get("/info")
async def get_license_info():
    """
    Get information about the current license
    Returns license status, expiration, and remaining days
    """
    license_key = get_stored_license()
    
    if not license_key:
        return {
            "activated": False,
            "license_key": "",
            "message": "No license activated"
        }
    
    # Try to get from background validator first (faster)
    try:
        from ..services.license_validator import get_license_validator
        validator = get_license_validator()
        validator_state = validator.get_license_state()
        
        # If validator has recent data, use it
        if validator_state.get("license_key") == license_key and validator_state.get("last_check"):
            config = load_config()
            license_config = config.get('license', {})
            
            return {
                "activated": True,
                "license_key": license_key,
                "valid": validator_state.get('valid', False),
                "license_type": validator_state.get('license_type'),
                "deployment_id": config.get('license', {}).get('deployment_id'),
                "activated_at": license_config.get('activated_at'),
                "expiry_date": validator_state.get('expiry_date'),
                "days_remaining": validator_state.get('days_remaining', 0),
                "expired": validator_state.get('expired', True),
                "offline_mode": validator_state.get('offline_mode', False),
                "last_check": validator_state.get('last_check')
            }
    except Exception as e:
        logger.warning(f"Could not get license state from validator: {e}")
    
    # Fallback to direct server validation
    validation = validate_license_with_server(license_key)
    
    config = load_config()
    license_config = config.get('license', {})
    
    return {
        "activated": True,
        "license_key": license_key,
        "valid": validation.get('valid', False),
        "license_type": validation.get('license_type'),
        "deployment_id": validation.get('deployment_id'),
        "activated_at": license_config.get('activated_at'),
        "expiry_date": validation.get('expiry_date'),
        "days_remaining": validation.get('days_remaining', 0),
        "expired": validation.get('expired', True),
        "offline_mode": False
    }

@router.get("/status")
async def get_license_status():
    """Get current license status (alias for /info)"""
    return await get_license_info()

@router.delete("/deactivate")
async def deactivate_license():
    """
    Deactivate the current license
    Removes license from config
    """
    config = load_config()
    
    if 'license' in config:
        del config['license']
        if save_config(config):
            return {"success": True, "message": "License deactivated"}
    
    raise HTTPException(status_code=500, detail="Failed to deactivate license")

@router.delete("/remove")
async def remove_license():
    """Remove stored license (alias for /deactivate)"""
    return await deactivate_license()

class LicenseKeyUpdateRequest(BaseModel):
    """Request to update license key"""
    license_key: str

@router.put("/key")
async def update_license_key(request: LicenseKeyUpdateRequest):
    """
    Update the license key
    Validates the new key and stores it if valid
    """
    license_key = request.license_key.strip()
    
    if not license_key:
        raise HTTPException(status_code=400, detail="License key is required")
    
    # Validate with license server
    validation = validate_license_with_server(license_key)
    
    if not validation.get('valid'):
        raise HTTPException(
            status_code=400,
            detail=validation.get('error', 'Invalid license key')
        )
    
    # Store in app config
    config = load_config()
    if 'license' not in config:
        config['license'] = {}
    
    config['license']['key'] = license_key
    config['license']['activated_at'] = datetime.utcnow().isoformat()
    config['license']['deployment_id'] = validation.get('deployment_id')
    config['license']['license_type'] = validation.get('license_type')
    config['license']['expiry_date'] = validation.get('expiry_date')
    
    if not save_config(config):
        raise HTTPException(status_code=500, detail="Failed to save license")
    
    # Also save to license_config.yml for middleware access
    try:
        from ..middleware.license import save_license_config
        license_config = {
            "activated": True,
            "license_key": license_key,
            "activated_at": datetime.utcnow().isoformat(),
            "license_info": {
                "license_type": validation.get('license_type'),
                "expiration_date": validation.get('expiry_date'),
                "days_remaining": validation.get('days_remaining'),
                "deployment_id": validation.get('deployment_id')
            }
        }
        save_license_config(license_config)
    except Exception as e:
        logger.error(f"Failed to save license config: {e}")
    
    # Update background validator with new license key
    try:
        from ..services.license_validator import get_license_validator
        validator = get_license_validator()
        validator.set_license_key(license_key)
        logger.info("License validator updated with new license key")
    except Exception as e:
        logger.error(f"Failed to update license validator: {e}")
    
    return {
        "success": True,
        "message": "License key updated successfully",
        "license_info": {
            "valid": True,
            "license_type": validation.get('license_type'),
            "expiry_date": validation.get('expiry_date'),
            "days_remaining": validation.get('days_remaining')
        }
    }

@router.get("/check")
async def check_license():
    """
    Quick check if license is valid
    Returns simple boolean response
    """
    license_key = get_stored_license()
    
    if not license_key:
        return {"valid": False}
    
    validation = validate_license_with_server(license_key)
    return {"valid": validation.get('valid', False)}

class LicenseServerConfigRequest(BaseModel):
    """Request to update license server configuration"""
    server_url: str

@router.get("/server-config")
async def get_license_server_config():
    """
    Get license server configuration
    Returns the current license server URL
    """
    try:
        config = load_config()
        license_config = config.get('license', {})
        
        return {
            "success": True,
            "server_url": license_config.get('server_url', 'http://localhost:8000')
        }
    except Exception as e:
        logger.error(f"Failed to get license server config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/server-config")
async def update_license_server_config(request: LicenseServerConfigRequest):
    """
    Update license server URL
    Saves the new URL to config file
    """
    try:
        server_url = request.server_url.strip()
        
        if not server_url:
            raise HTTPException(status_code=400, detail="Server URL is required")
        
        # Remove trailing slash if present
        if server_url.endswith('/'):
            server_url = server_url[:-1]
        
        # Validate URL format
        if not (server_url.startswith('http://') or server_url.startswith('https://')):
            raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")
        
        config = load_config()
        if 'license' not in config:
            config['license'] = {}
        
        config['license']['server_url'] = server_url
        
        if not save_config(config):
            raise HTTPException(status_code=500, detail="Failed to save configuration")
        
        return {
            "success": True,
            "message": "License server URL updated successfully",
            "server_url": server_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update license server config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
