"""
PGAIView License Server
Generates and validates time-based licenses with configurable expiration
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import secrets

app = Flask(__name__)
CORS(app)

# Secret key for HMAC signing (should be stored securely in production)
SECRET_KEY = os.environ.get('LICENSE_SECRET_KEY', Fernet.generate_key().decode())
cipher = Fernet(SECRET_KEY.encode())

# License configuration
LICENSE_CONFIG = {
    'trial': {'days': 10, 'description': 'Trial License'},
    'standard': {'days': 60, 'description': 'Standard 2-Month License'},
    'enterprise': {'days': 365, 'description': 'Enterprise Annual License'},
}

def generate_license_key(deployment_id, license_type='standard'):
    """
    Generate a time-limited license key
    
    Args:
        deployment_id: Unique identifier for the deployment
        license_type: Type of license (trial, standard, enterprise)
    
    Returns:
        dict: License key and metadata
    """
    if license_type not in LICENSE_CONFIG:
        raise ValueError(f"Invalid license type: {license_type}")
    
    config = LICENSE_CONFIG[license_type]
    expiry_days = config['days']
    
    # Generate expiration date
    issue_date = datetime.utcnow()
    expiry_date = issue_date + timedelta(days=expiry_days)
    
    # Create license payload
    license_data = {
        'deployment_id': deployment_id,
        'issue_date': issue_date.isoformat(),
        'expiry_date': expiry_date.isoformat(),
        'license_type': license_type,
        'version': '1.0'
    }
    
    # Encrypt and encode the license
    license_json = json.dumps(license_data)
    encrypted = cipher.encrypt(license_json.encode())
    license_key = base64.urlsafe_b64encode(encrypted).decode()
    
    return {
        'license_key': license_key,
        'deployment_id': deployment_id,
        'license_type': license_type,
        'issue_date': issue_date.isoformat(),
        'expiry_date': expiry_date.isoformat(),
        'days_valid': expiry_days
    }

def validate_license_key(license_key):
    """
    Validate a license key and return its details
    
    Args:
        license_key: The license key to validate
    
    Returns:
        dict: License validation result with details
    """
    try:
        # Decode and decrypt
        encrypted = base64.urlsafe_b64decode(license_key.encode())
        decrypted = cipher.decrypt(encrypted)
        license_data = json.loads(decrypted.decode())
        
        # Parse dates
        expiry_date = datetime.fromisoformat(license_data['expiry_date'])
        issue_date = datetime.fromisoformat(license_data['issue_date'])
        now = datetime.utcnow()
        
        # Check if expired
        is_valid = now < expiry_date
        days_remaining = (expiry_date - now).days if is_valid else 0
        
        return {
            'valid': is_valid,
            'deployment_id': license_data['deployment_id'],
            'license_type': license_data['license_type'],
            'issue_date': issue_date.isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'days_remaining': max(0, days_remaining),
            'expired': not is_valid
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'expired': True
        }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'PGAIView License Server'})

@app.route('/license/generate', methods=['POST'])
def generate_license():
    """
    Generate a new license key
    
    Request body:
        {
            "deployment_id": "unique-deployment-id",
            "license_type": "trial|standard|enterprise",
            "admin_key": "admin-secret-key"
        }
    """
    data = request.json
    
    # Validate admin key (basic security)
    admin_key = data.get('admin_key')
    expected_admin_key = os.environ.get('ADMIN_KEY', 'pgaiview-admin-2024')
    
    if admin_key != expected_admin_key:
        return jsonify({'error': 'Unauthorized'}), 401
    
    deployment_id = data.get('deployment_id')
    license_type = data.get('license_type', 'standard')
    
    if not deployment_id:
        return jsonify({'error': 'deployment_id is required'}), 400
    
    try:
        license_info = generate_license_key(deployment_id, license_type)
        return jsonify(license_info), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to generate license: {str(e)}'}), 500

@app.route('/license/validate', methods=['POST'])
def validate_license():
    """
    Validate a license key
    
    Request body:
        {
            "license_key": "base64-encoded-license-key"
        }
    """
    data = request.json
    license_key = data.get('license_key')
    
    if not license_key:
        return jsonify({'error': 'license_key is required'}), 400
    
    validation_result = validate_license_key(license_key)
    return jsonify(validation_result), 200

@app.route('/license/renew', methods=['POST'])
def renew_license():
    """
    Renew an existing license (generates new key with extended expiry)
    
    Request body:
        {
            "current_license_key": "existing-key",
            "admin_key": "admin-secret-key"
        }
    """
    data = request.json
    
    # Validate admin key
    admin_key = data.get('admin_key')
    expected_admin_key = os.environ.get('ADMIN_KEY', 'pgaiview-admin-2024')
    
    if admin_key != expected_admin_key:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_key = data.get('current_license_key')
    if not current_key:
        return jsonify({'error': 'current_license_key is required'}), 400
    
    # Validate current license
    current_license = validate_license_key(current_key)
    if 'error' in current_license:
        return jsonify({'error': 'Invalid current license'}), 400
    
    # Generate new license with same deployment ID and type
    try:
        new_license = generate_license_key(
            current_license['deployment_id'],
            current_license['license_type']
        )
        return jsonify(new_license), 200
    except Exception as e:
        return jsonify({'error': f'Failed to renew license: {str(e)}'}), 500

@app.route('/license/types', methods=['GET'])
def get_license_types():
    """Get available license types and their configurations"""
    return jsonify(LICENSE_CONFIG), 200

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🔐 PGAIView License Server starting on port {port}")
    print(f"🔑 Secret Key: {SECRET_KEY[:20]}... (keep this secure!)")
    print("\nAvailable license types:")
    for ltype, config in LICENSE_CONFIG.items():
        print(f"  - {ltype}: {config['days']} days ({config['description']})")
    
    app.run(host='0.0.0.0', port=port, debug=True)
