#!/bin/bash

# PostgreSQL 16 Installation Script for Ubuntu
# This script installs PostgreSQL 16 on Ubuntu systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        print_status "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Function to check Ubuntu version
check_ubuntu_version() {
    if ! command -v lsb_release &> /dev/null; then
        print_error "lsb_release not found. Please ensure you're running Ubuntu."
        exit 1
    fi
    
    local ubuntu_version=$(lsb_release -rs)
    local ubuntu_codename=$(lsb_release -cs)
    
    print_status "Detected Ubuntu $ubuntu_version ($ubuntu_codename)"
    
    # Check if Ubuntu version is supported
    case $ubuntu_codename in
        focal|jammy|mantic|noble)
            print_success "Ubuntu version is supported"
            ;;
        *)
            print_warning "Ubuntu version may not be officially supported, but proceeding..."
            ;;
    esac
}

# Function to update system packages
update_system() {
    print_status "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    print_success "System packages updated"
}

# Function to install prerequisites
install_prerequisites() {
    print_status "Installing prerequisites..."
    sudo apt install -y wget ca-certificates gnupg lsb-release curl
    print_success "Prerequisites installed"
}

# Function to add PostgreSQL official repository
add_postgresql_repo() {
    print_status "Adding PostgreSQL official repository..."
    
    # Create directory for keyrings if it doesn't exist
    sudo mkdir -p /etc/apt/keyrings
    
    # Download and add PostgreSQL signing key
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/keyrings/postgresql.gpg
    
    # Add PostgreSQL repository
    local ubuntu_codename=$(lsb_release -cs)
    echo "deb [arch=amd64,arm64,ppc64el signed-by=/etc/apt/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt/ $ubuntu_codename-pgdg main" | sudo tee /etc/apt/sources.list.d/postgresql.list
    
    # Update package list
    sudo apt update
    
    print_success "PostgreSQL repository added"
}

# Function to install PostgreSQL 16
install_postgresql() {
    print_status "Installing PostgreSQL 16..."
    
    # Install PostgreSQL 16 and contrib package
    sudo apt install -y postgresql-16 postgresql-contrib-16 postgresql-client-16
    
    print_success "PostgreSQL 16 installed"
}

# Function to start and enable PostgreSQL service
start_postgresql_service() {
    print_status "Starting and enabling PostgreSQL service..."
    
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Check if service is running
    if sudo systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL service is running"
    else
        print_error "PostgreSQL service failed to start"
        exit 1
    fi
}

# Function to configure PostgreSQL
configure_postgresql() {
    print_status "Configuring PostgreSQL..."
    
    # Get PostgreSQL version and data directory
    local pg_version="16"
    local pg_data_dir="/etc/postgresql/$pg_version/main"
    
    # Backup original configuration
    sudo cp "$pg_data_dir/postgresql.conf" "$pg_data_dir/postgresql.conf.backup"
    sudo cp "$pg_data_dir/pg_hba.conf" "$pg_data_dir/pg_hba.conf.backup"
    
    print_status "Original configuration backed up"
    
    # Configure PostgreSQL to listen on all addresses (optional, for development)
    read -p "Do you want to configure PostgreSQL to accept connections from all IP addresses? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$pg_data_dir/postgresql.conf"
        
        # Add entry to pg_hba.conf to allow connections (use with caution in production)
        echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a "$pg_data_dir/pg_hba.conf"
        
        print_warning "PostgreSQL configured to accept connections from all IP addresses"
        print_warning "This is not recommended for production environments"
    fi
}

# Function to set up PostgreSQL user and database
setup_postgresql_user() {
    print_status "Setting up PostgreSQL user and database..."
    
    # Set password for postgres user
    print_status "Setting password for postgres user..."
    echo "Please enter a password for the PostgreSQL 'postgres' user:"
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$(read -s -p "Password: "; echo $REPLY)';"
    echo
    
    # Create a database user with the same name as the system user
    local current_user=$(whoami)
    print_status "Creating database user '$current_user'..."
    
    echo "Please enter a password for the database user '$current_user':"
    read -s -p "Password: " user_password
    echo
    
    sudo -u postgres createuser --createdb --pwprompt "$current_user" || true
    
    # Create a database for the user
    sudo -u postgres createdb "$current_user" || true
    
    print_success "Database user '$current_user' created"
}

# Function to restart PostgreSQL service
restart_postgresql() {
    print_status "Restarting PostgreSQL service to apply configuration changes..."
    sudo systemctl restart postgresql
    
    if sudo systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL service restarted successfully"
    else
        print_error "PostgreSQL service failed to restart"
        exit 1
    fi
}

# Function to test PostgreSQL installation
test_installation() {
    print_status "Testing PostgreSQL installation..."
    
    # Check PostgreSQL version
    local pg_version=$(sudo -u postgres psql -t -c "SELECT version();" | head -1)
    print_success "PostgreSQL version: $pg_version"
    
    # Check if we can connect
    if sudo -u postgres psql -c "\l" > /dev/null 2>&1; then
        print_success "PostgreSQL is working correctly"
    else
        print_error "Failed to connect to PostgreSQL"
        exit 1
    fi
}

# Function to install additional tools (optional)
install_additional_tools() {
    read -p "Do you want to install pgAdmin4 (PostgreSQL administration tool)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing pgAdmin4..."
        
        # Add pgAdmin repository
        curl -fsSL https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /etc/apt/keyrings/packages-pgadmin-org.gpg
        echo "deb [signed-by=/etc/apt/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" | sudo tee /etc/apt/sources.list.d/pgadmin4.list
        
        sudo apt update
        sudo apt install -y pgadmin4
        
        print_success "pgAdmin4 installed"
        print_status "You can access pgAdmin4 at: http://localhost/pgadmin4"
    fi
}

# Function to display connection information
display_connection_info() {
    print_success "PostgreSQL 16 installation completed successfully!"
    echo
    print_status "Connection Information:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: postgres (default)"
    echo "  Username: postgres"
    echo
    print_status "Useful Commands:"
    echo "  Connect to PostgreSQL: sudo -u postgres psql"
    echo "  Connect as your user: psql -d $(whoami)"
    echo "  Check service status: sudo systemctl status postgresql"
    echo "  Start service: sudo systemctl start postgresql"
    echo "  Stop service: sudo systemctl stop postgresql"
    echo "  Restart service: sudo systemctl restart postgresql"
    echo
    print_status "Configuration files location:"
    echo "  /etc/postgresql/16/main/postgresql.conf"
    echo "  /etc/postgresql/16/main/pg_hba.conf"
    echo
    print_status "Log files location:"
    echo "  /var/log/postgresql/postgresql-16-main.log"
}

# Main installation function
main() {
    echo "================================================"
    echo "PostgreSQL 16 Installation Script for Ubuntu"
    echo "================================================"
    echo
    
    check_root
    check_ubuntu_version
    
    read -p "Do you want to proceed with PostgreSQL 16 installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installation cancelled by user"
        exit 0
    fi
    
    update_system
    install_prerequisites
    add_postgresql_repo
    install_postgresql
    start_postgresql_service
    configure_postgresql
    restart_postgresql
    setup_postgresql_user
    test_installation
    install_additional_tools
    display_connection_info
    
    print_success "PostgreSQL 16 installation and configuration completed!"
}

# Run main function
main "$@"