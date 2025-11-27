"""
License validation middleware
"""
from fastapi import HTTPException, Request
from typing import Dict, Any
import logging
import os
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)

LICENSE_CONFIG_FILE = "license_config.yml"


def load_license_config() -> Dict[str, Any]:
    """Load license configuration"""
    if not os.path.exists(LICENSE_CONFIG_FILE):
        return {"license_key": None, "activated": False}
    
    try:
        with open(LICENSE_CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f) or {"license_key": None, "activated": False}
    except Exception as e:
        logger.error(f"Failed to load license config: {e}")
        return {"license_key": None, "activated": False}


def save_license_config(config: Dict[str, Any]):
    """Save license configuration"""
    try:
        with open(LICENSE_CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        logger.error(f"Failed to save license config: {e}")
        raise


def check_license_valid() -> tuple[bool, str, Dict[str, Any]]:
    """
    Check if license is valid
    Returns: (is_valid, message, license_info)
    """
    license_config = load_license_config()
    
    if not license_config.get("activated") or not license_config.get("license_key"):
        return False, "No license activated. Please activate a valid license.", {}
    
    license_info = license_config.get("license_info", {})
    
    # Check expiration
    if "expiration_date" in license_info:
        try:
            expiration = datetime.fromisoformat(license_info["expiration_date"].replace('Z', '+00:00'))
            if datetime.now(expiration.tzinfo) > expiration:
                return False, "License has expired. Please renew your license.", license_info
        except Exception as e:
            logger.error(f"Failed to parse expiration date: {e}")
            return False, "Invalid license information.", license_info
    
    return True, "License is valid", license_info


async def require_valid_license(request: Request):
    """
    Dependency to require valid license for protected endpoints
    """
    is_valid, message, license_info = check_license_valid()
    
    if not is_valid:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "License Required",
                "message": message,
                "license_info": license_info
            }
        )
    
    return license_info
