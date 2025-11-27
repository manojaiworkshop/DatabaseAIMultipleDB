"""
License validation models and utilities
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import json
import base64


class LicenseInfo(BaseModel):
    """License information model"""
    license_key: str = Field(..., description="License key")
    company_name: Optional[str] = Field(None, description="Company name")
    email: Optional[str] = Field(None, description="Contact email")
    max_users: int = Field(1, description="Maximum concurrent users")
    expiry_date: Optional[datetime] = Field(None, description="License expiry date")
    features: list[str] = Field(default_factory=list, description="Enabled features")
    is_trial: bool = Field(False, description="Is trial license")
    

class LicenseValidation(BaseModel):
    """License validation request"""
    license_key: str = Field(..., description="License key to validate")


class LicenseStatus(BaseModel):
    """License status response"""
    is_valid: bool = Field(..., description="Whether license is valid")
    is_active: bool = Field(..., description="Whether license is active")
    company_name: Optional[str] = None
    max_users: int = 1
    expiry_date: Optional[datetime] = None
    days_remaining: Optional[int] = None
    features: list[str] = Field(default_factory=list)
    is_trial: bool = False
    message: str = Field("", description="Status message")


class LicenseManager:
    """License management utilities"""
    
    # Secret key for license generation (in production, use environment variable)
    SECRET_KEY = "pgaiview-license-secret-2025"
    
    @staticmethod
    def generate_license_key(company_name: str, expiry_days: int = 365, is_trial: bool = False) -> str:
        """Generate a license key for given parameters"""
        expiry_date = datetime.now() + timedelta(days=expiry_days)
        
        data = {
            "company": company_name,
            "expiry": expiry_date.isoformat(),
            "trial": is_trial,
            "timestamp": datetime.now().isoformat()
        }
        
        # Create signature
        json_str = json.dumps(data, sort_keys=True)
        signature = hashlib.sha256(
            (json_str + LicenseManager.SECRET_KEY).encode()
        ).hexdigest()[:16]
        
        # Encode data + signature
        payload = json.dumps({**data, "sig": signature})
        license_key = base64.b64encode(payload.encode()).decode()
        
        # Format as XXXX-XXXX-XXXX-XXXX
        formatted = '-'.join([license_key[i:i+4] for i in range(0, min(len(license_key), 16), 4)])
        return formatted
    
    @staticmethod
    def validate_license(license_key: str) -> LicenseStatus:
        """Validate a license key"""
        try:
            # Remove dashes and decode
            clean_key = license_key.replace('-', '')
            
            # Try to decode
            try:
                decoded = base64.b64decode(clean_key + '==').decode()
                data = json.loads(decoded)
            except Exception:
                return LicenseStatus(
                    is_valid=False,
                    is_active=False,
                    message="Invalid license key format"
                )
            
            # Verify signature
            sig = data.pop('sig', '')
            json_str = json.dumps(data, sort_keys=True)
            expected_sig = hashlib.sha256(
                (json_str + LicenseManager.SECRET_KEY).encode()
            ).hexdigest()[:16]
            
            if sig != expected_sig:
                return LicenseStatus(
                    is_valid=False,
                    is_active=False,
                    message="Invalid license signature"
                )
            
            # Check expiry
            expiry_date = datetime.fromisoformat(data['expiry'])
            days_remaining = (expiry_date - datetime.now()).days
            is_active = days_remaining > 0
            
            return LicenseStatus(
                is_valid=True,
                is_active=is_active,
                company_name=data.get('company', 'Unknown'),
                max_users=data.get('max_users', 1),
                expiry_date=expiry_date,
                days_remaining=max(0, days_remaining),
                features=data.get('features', ['basic']),
                is_trial=data.get('trial', False),
                message="License is active" if is_active else f"License expired {-days_remaining} days ago"
            )
            
        except Exception as e:
            return LicenseStatus(
                is_valid=False,
                is_active=False,
                message=f"License validation error: {str(e)}"
            )


# Demo license keys for testing
def get_demo_licenses():
    """Generate demo license keys"""
    return {
        "trial_30days": LicenseManager.generate_license_key("Trial User", 30, is_trial=True),
        "standard_1year": LicenseManager.generate_license_key("Standard User", 365, is_trial=False),
        "expired": LicenseManager.generate_license_key("Expired User", -10, is_trial=False),
    }
