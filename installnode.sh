#!/bin/bash

# Script to install Node.js 22 on Linux
# This script uses the NodeSource repository for Ubuntu/Debian-based systems

set -e  # Exit on error

echo "=========================================="
echo "Installing Node.js 22.x"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. This script supports Ubuntu/Debian-based systems."
    exit 1
fi

echo "Detected OS: $OS"

# Install Node.js 22.x based on distribution
case $OS in
    ubuntu|debian|pop|linuxmint)
        echo "Installing Node.js 22.x for Debian/Ubuntu-based system..."
        
        # Remove old installations if any
        echo "Removing old Node.js installations..."
        apt-get remove -y nodejs npm || true
        
        # Install prerequisites
        echo "Installing prerequisites..."
        apt-get update
        apt-get install -y ca-certificates curl gnupg
        
        # Add NodeSource repository
        echo "Adding NodeSource repository for Node.js 22.x..."
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
        
        NODE_MAJOR=22
        echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
        
        # Install Node.js
        echo "Installing Node.js 22.x..."
        apt-get update
        apt-get install -y nodejs
        ;;
        
    fedora|rhel|centos|rocky|almalinux)
        echo "Installing Node.js 22.x for RHEL/Fedora-based system..."
        
        # Remove old installations
        echo "Removing old Node.js installations..."
        dnf remove -y nodejs npm || yum remove -y nodejs npm || true
        
        # Add NodeSource repository
        echo "Adding NodeSource repository for Node.js 22.x..."
        curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
        
        # Install Node.js
        echo "Installing Node.js 22.x..."
        dnf install -y nodejs || yum install -y nodejs
        ;;
        
    arch|manjaro)
        echo "Installing Node.js 22.x for Arch-based system..."
        pacman -Syu --noconfirm nodejs npm
        ;;
        
    *)
        echo "Unsupported distribution: $OS"
        echo "Please install Node.js 22 manually from https://nodejs.org/"
        exit 1
        ;;
esac

# Verify installation
echo ""
echo "=========================================="
echo "Verifying installation..."
echo "=========================================="

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js installed successfully: $NODE_VERSION"
else
    echo "✗ Node.js installation failed"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ npm installed successfully: $NPM_VERSION"
else
    echo "✗ npm installation failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"
echo ""
echo "You can now use Node.js and npm commands."
