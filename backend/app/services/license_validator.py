"""
Continuous license validation service
- Background thread checks license every 5 minutes with server
- Offline datetime validation when server is unreachable
- Thread-safe license state management
"""
import threading
import time
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)

class LicenseValidator:
    """Background license validation service"""
    
    def __init__(self, check_interval=300):  # 5 minutes = 300 seconds
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # License state
        self.license_state = {
            "valid": False,
            "license_key": None,
            "license_type": None,
            "expiry_date": None,
            "issue_date": None,
            "days_remaining": 0,
            "expired": True,
            "last_check": None,
            "last_server_check": None,
            "offline_mode": False,
            "error": None
        }
    
    def start(self):
        """Start the background validation thread"""
        if self.running:
            logger.warning("License validator already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._validation_loop, daemon=True)
        self.thread.start()
        logger.info(f"License validator started (check interval: {self.check_interval}s)")
    
    def stop(self):
        """Stop the background validation thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("License validator stopped")
    
    def _validation_loop(self):
        """Main validation loop running in background thread"""
        while self.running:
            try:
                self.validate_license()
            except Exception as e:
                logger.error(f"License validation error in background thread: {e}")
            
            # Sleep in small increments to allow quick shutdown
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def validate_license(self, license_key: Optional[str] = None, server_url: Optional[str] = None) -> Dict:
        """
        Validate license with server and fallback to offline validation
        
        Args:
            license_key: License key to validate (optional, uses stored if not provided)
            server_url: License server URL (optional, uses stored if not provided)
        
        Returns:
            Dict with validation result
        """
        with self.lock:
            # If license_key provided, update stored key
            if license_key:
                self.license_state["license_key"] = license_key
            
            # Get license key from state if not provided
            current_key = license_key or self.license_state.get("license_key")
            
            if not current_key:
                self.license_state.update({
                    "valid": False,
                    "error": "No license key available",
                    "last_check": datetime.utcnow().isoformat()
                })
                return self.license_state.copy()
            
            # Try server validation first
            server_result = self._validate_with_server(current_key, server_url)
            
            if server_result.get("success"):
                # Server validation succeeded
                self.license_state.update({
                    "valid": server_result.get("valid", False),
                    "license_type": server_result.get("license_type"),
                    "expiry_date": server_result.get("expiry_date"),
                    "issue_date": server_result.get("issue_date"),
                    "days_remaining": server_result.get("days_remaining", 0),
                    "expired": server_result.get("expired", True),
                    "last_check": datetime.utcnow().isoformat(),
                    "last_server_check": datetime.utcnow().isoformat(),
                    "offline_mode": False,
                    "error": server_result.get("error")
                })
            else:
                # Server validation failed, try offline validation
                logger.warning(f"Server validation failed: {server_result.get('error')}")
                offline_result = self._validate_offline()
                
                self.license_state.update({
                    "valid": offline_result.get("valid", False),
                    "expired": offline_result.get("expired", True),
                    "days_remaining": offline_result.get("days_remaining", 0),
                    "last_check": datetime.utcnow().isoformat(),
                    "offline_mode": True,
                    "error": f"Offline mode: {offline_result.get('error', 'Server unreachable')}"
                })
            
            return self.license_state.copy()
    
    def _validate_with_server(self, license_key: str, server_url: Optional[str] = None) -> Dict:
        """
        Validate license with remote server
        
        Returns:
            Dict with validation result and success flag
        """
        try:
            # Load server URL from config if not provided
            if not server_url:
                from ..routes.license import get_license_server_url
                server_url = get_license_server_url()
            
            # Clean license key
            clean_key = license_key.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Call license server API
            response = requests.post(
                f"{server_url}/api/license/validate",
                json={"license_key": clean_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "valid": data.get("valid", False),
                    "license_type": data.get("license_type"),
                    "expiry_date": data.get("expiry_date"),
                    "issue_date": data.get("issue_date"),
                    "days_remaining": data.get("days_remaining", 0),
                    "expired": data.get("expired", True),
                    "deployment_id": data.get("deployment_id"),
                    "error": data.get("error")
                }
            else:
                return {
                    "success": False,
                    "error": f"Server returned {response.status_code}"
                }
        
        except requests.Timeout:
            return {"success": False, "error": "Server timeout"}
        except requests.ConnectionError:
            return {"success": False, "error": "Cannot connect to server"}
        except Exception as e:
            return {"success": False, "error": f"Validation error: {str(e)}"}
    
    def _validate_offline(self) -> Dict:
        """
        Offline datetime validation without server
        Uses stored expiry_date to check validity
        
        Returns:
            Dict with validation result
        """
        try:
            expiry_date_str = self.license_state.get("expiry_date")
            
            if not expiry_date_str:
                return {
                    "valid": False,
                    "expired": True,
                    "days_remaining": 0,
                    "error": "No expiry date available for offline validation"
                }
            
            # Parse expiry date
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
            except:
                expiry_date = datetime.fromisoformat(expiry_date_str)
            
            # Get current time
            now = datetime.utcnow()
            
            # Make sure both are naive or both are aware
            if expiry_date.tzinfo is not None:
                expiry_date = expiry_date.replace(tzinfo=None)
            
            # Check if expired
            is_valid = now < expiry_date
            
            # Calculate days remaining
            if is_valid:
                time_remaining = expiry_date - now
                days_remaining = time_remaining.days
                if days_remaining == 0 and time_remaining.total_seconds() > 0:
                    days_remaining = 1
            else:
                days_remaining = 0
            
            return {
                "valid": is_valid,
                "expired": not is_valid,
                "days_remaining": days_remaining,
                "error": None if is_valid else "License expired (offline validation)"
            }
        
        except Exception as e:
            logger.error(f"Offline validation error: {e}")
            return {
                "valid": False,
                "expired": True,
                "days_remaining": 0,
                "error": f"Offline validation failed: {str(e)}"
            }
    
    def get_license_state(self) -> Dict:
        """
        Get current license state (thread-safe)
        
        Returns:
            Dict with current license state
        """
        with self.lock:
            return self.license_state.copy()
    
    def set_license_key(self, license_key: str, server_url: Optional[str] = None):
        """
        Set new license key and validate immediately
        
        Args:
            license_key: New license key
            server_url: License server URL (optional)
        """
        self.validate_license(license_key, server_url)
    
    def is_valid(self) -> bool:
        """
        Quick check if license is currently valid
        
        Returns:
            bool: True if license is valid
        """
        with self.lock:
            return self.license_state.get("valid", False)


# Global instance
_license_validator = None

def get_license_validator() -> LicenseValidator:
    """Get or create global license validator instance"""
    global _license_validator
    if _license_validator is None:
        _license_validator = LicenseValidator(check_interval=300)  # 5 minutes
    return _license_validator

def start_license_validator():
    """Start the global license validator"""
    validator = get_license_validator()
    validator.start()
    logger.info("Global license validator started")

def stop_license_validator():
    """Stop the global license validator"""
    validator = get_license_validator()
    validator.stop()
    logger.info("Global license validator stopped")
