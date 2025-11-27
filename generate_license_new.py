#!/usr/bin/env python3
"""
PGAIView License Generator
Quick script to generate licenses for your application
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
LICENSE_SERVER = "http://localhost:5000"
ADMIN_KEY = "pgaiview-admin-2024"

# Colors
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

def print_header():
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{Colors.BOLD}       PGAIView License Generator v1.0{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

def check_server():
    """Check if license server is running"""
    print(f"{Colors.YELLOW}🔍 Checking license server...{Colors.NC}")
    try:
        response = requests.get(f"{LICENSE_SERVER}/health", timeout=2)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ License server is running{Colors.NC}\n")
            return True
    except:
        pass
    
    print(f"{Colors.RED}❌ License server is not running!{Colors.NC}\n")
    print("Please start the license server first:")
    print("  python3 license_server.py")
    print("\nOr use:")
    print("  ./start_license_server.sh\n")
    return False

def generate_deployment_id():
    """Generate a random deployment ID"""
    import random
    import string
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"deploy-{date_str}-{random_str}"

def save_license_to_file(license_key, license_type):
    """Save license key to a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"license_{license_type}_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write(license_key)
    return filename

def generate_license(license_type, deployment_id):
    """Generate a license key"""
    print(f"{Colors.BLUE}📝 Generating {license_type} license...{Colors.NC}\n")
    
    payload = {
        "deployment_id": deployment_id,
        "license_type": license_type,
        "admin_key": ADMIN_KEY
    }
    
    try:
        response = requests.post(
            f"{LICENSE_SERVER}/license/generate",
            json=payload,
            timeout=5
        )
        
        if response.status_code != 200:
            error_data = response.json()
            print(f"{Colors.RED}❌ Error: {error_data.get('error', 'Unknown error')}{Colors.NC}")
            return None
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Request failed: {str(e)}{Colors.NC}")
        return None
    except json.JSONDecodeError:
        print(f"{Colors.RED}❌ Invalid response from server{Colors.NC}")
        return None

def display_license(data):
    """Display the generated license"""
    print(f"{Colors.GREEN}{'=' * 60}{Colors.NC}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✅ License Generated Successfully!{Colors.NC}")
    print(f"{Colors.GREEN}{'=' * 60}{Colors.NC}\n")
    
    print(f"{Colors.YELLOW}License Type:{Colors.NC}     {data['license_type']}")
    print(f"{Colors.YELLOW}Deployment ID:{Colors.NC}    {data['deployment_id']}")
    print(f"{Colors.YELLOW}Valid for:{Colors.NC}        {data['days_valid']} days")
    print(f"{Colors.YELLOW}Expires:{Colors.NC}          {data['expiry_date']}")
    print()
    
    print(f"{Colors.GREEN}🔑 Your License Key:{Colors.NC}")
    print("━" * 60)
    print(f"{Colors.BLUE}{data['license_key']}{Colors.NC}")
    print("━" * 60)
    print()
    
    # Save to file
    filename = save_license_to_file(data['license_key'], data['license_type'])
    print(f"{Colors.GREEN}💾 License key saved to: {filename}{Colors.NC}")
    print(f"{Colors.YELLOW}📋 Copy this license key and use it in PGAIView{Colors.NC}\n")

def main():
    print_header()
    
    # Check if server is running
    if not check_server():
        sys.exit(1)
    
    # Show license types
    print("Select license type to generate:\n")
    print("  1) Trial        (10 days)   - For testing")
    print("  2) Standard     (60 days)   - 2 months")
    print("  3) Enterprise   (365 days)  - 1 year")
    print("  4) Custom       (manual)    - Enter details manually")
    print()
    
    # Get user choice
    choice = input("Enter choice [1-4]: ").strip()
    
    license_type_map = {
        '1': 'trial',
        '2': 'standard',
        '3': 'enterprise'
    }
    
    if choice in license_type_map:
        license_type = license_type_map[choice]
    elif choice == '4':
        license_type = input("\nEnter license type (trial/standard/enterprise): ").strip().lower()
        if license_type not in ['trial', 'standard', 'enterprise']:
            print(f"{Colors.RED}Invalid license type!{Colors.NC}")
            sys.exit(1)
    else:
        print(f"{Colors.RED}Invalid choice!{Colors.NC}")
        sys.exit(1)
    
    # Get deployment ID
    default_deployment = generate_deployment_id()
    print(f"\nEnter deployment ID (or press Enter for default):")
    deployment_id = input(f"[{default_deployment}]: ").strip()
    deployment_id = deployment_id if deployment_id else default_deployment
    
    print()
    
    # Generate license
    data = generate_license(license_type, deployment_id)
    
    if data:
        display_license(data)
    else:
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.NC}")
        sys.exit(1)
