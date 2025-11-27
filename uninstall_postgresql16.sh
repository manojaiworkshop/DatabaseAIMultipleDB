#!/bin/bash

# PostgreSQL 16 Uninstallation Script for Ubuntu
# This script completely removes PostgreSQL 16 from Ubuntu systems

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

# Function to display warning and get confirmation
display_warning() {
    echo "================================================"
    echo "PostgreSQL 16 UNINSTALLATION Script for Ubuntu"
    echo "================================================"
    echo
    print_warning "WARNING: This script will COMPLETELY REMOVE PostgreSQL 16 from your system!"
    print_warning "This includes:"
    echo "  - All PostgreSQL 16 packages"
    echo "  - All databases and data"
    echo "  - All configuration files"
    echo "  - PostgreSQL user accounts"
    echo "  - PostgreSQL repositories"
    echo
    print_error "THIS ACTION CANNOT BE UNDONE!"
    echo
    
    read -p "Are you absolutely sure you want to proceed? Type 'YES' to continue: " confirmation
    if [[ "$confirmation" != "YES" ]]; then
        print_status "Uninstallation cancelled by user"
        exit 0
    fi
    
    echo
    read -p "Last chance! Type 'REMOVE' to confirm uninstallation: " final_confirmation
    if [[ "$final_confirmation" != "REMOVE" ]]; then
        print_status "Uninstallation cancelled by user"
        exit 0
    fi
}

# Function to backup databases (optional)
backup_databases() {
    echo
    read -p "Do you want to create a backup of your databases before uninstalling? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Creating database backup..."
        
        local backup_dir="$HOME/postgresql_backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Check if PostgreSQL is running and accessible
        if sudo systemctl is-active --quiet postgresql 2>/dev/null && sudo -u postgres psql -l > /dev/null 2>&1; then
            # Backup all databases
            sudo -u postgres pg_dumpall > "$backup_dir/all_databases.sql"
            
            # Get list of databases and backup each one individually
            local databases=$(sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;" | grep -v "^$" | xargs)
            
            for db in $databases; do
                print_status "Backing up database: $db"
                sudo -u postgres pg_dump "$db" > "$backup_dir/${db}.sql" 2>/dev/null || true
            done
            
            print_success "Databases backed up to: $backup_dir"
        else
            print_warning "PostgreSQL is not running or not accessible. Skipping backup."
        fi
    fi
}

# Function to stop PostgreSQL service
stop_postgresql_service() {
    print_status "Stopping PostgreSQL service..."
    
    if sudo systemctl is-active --quiet postgresql 2>/dev/null; then
        sudo systemctl stop postgresql
        print_success "PostgreSQL service stopped"
    else
        print_status "PostgreSQL service is not running"
    fi
    
    # Disable the service
    if sudo systemctl is-enabled --quiet postgresql 2>/dev/null; then
        sudo systemctl disable postgresql
        print_success "PostgreSQL service disabled"
    fi
}

# Function to remove PostgreSQL packages
remove_postgresql_packages() {
    print_status "Removing PostgreSQL packages..."
    
    # Get list of installed PostgreSQL packages
    local pg_packages=$(dpkg -l | grep -i postgresql | awk '{print $2}' | xargs)
    
    if [ -n "$pg_packages" ]; then
        print_status "Found PostgreSQL packages: $pg_packages"
        
        # Remove packages
        sudo apt remove --purge -y $pg_packages
        
        # Remove any remaining PostgreSQL related packages
        sudo apt autoremove --purge -y
        
        print_success "PostgreSQL packages removed"
    else
        print_status "No PostgreSQL packages found to remove"
    fi
}

# Function to remove pgAdmin if installed
remove_pgadmin() {
    print_status "Checking for pgAdmin installation..."
    
    if dpkg -l | grep -q pgadmin; then
        print_status "Removing pgAdmin..."
        sudo apt remove --purge -y pgadmin4* || true
        print_success "pgAdmin removed"
    else
        print_status "pgAdmin not found"
    fi
}

# Function to remove PostgreSQL user and group
remove_postgresql_user() {
    print_status "Removing PostgreSQL system user and group..."
    
    # Remove postgres user
    if id "postgres" &>/dev/null; then
        sudo userdel postgres 2>/dev/null || true
        print_success "PostgreSQL user removed"
    else
        print_status "PostgreSQL user not found"
    fi
    
    # Remove postgres group
    if getent group postgres &>/dev/null; then
        sudo groupdel postgres 2>/dev/null || true
        print_success "PostgreSQL group removed"
    else
        print_status "PostgreSQL group not found"
    fi
}

# Function to remove data directories
remove_data_directories() {
    print_status "Removing PostgreSQL data directories..."
    
    local directories=(
        "/var/lib/postgresql"
        "/etc/postgresql"
        "/var/log/postgresql"
        "/run/postgresql"
        "/tmp/.s.PGSQL.*"
    )
    
    for dir in "${directories[@]}"; do
        if [ -e "$dir" ]; then
            print_status "Removing: $dir"
            sudo rm -rf "$dir"
        fi
    done
    
    print_success "PostgreSQL data directories removed"
}

# Function to remove configuration files
remove_config_files() {
    print_status "Removing PostgreSQL configuration files..."
    
    # Remove logrotate config
    if [ -f "/etc/logrotate.d/postgresql-common" ]; then
        sudo rm -f /etc/logrotate.d/postgresql-common
        print_status "Removed logrotate configuration"
    fi
    
    # Remove any remaining config files
    sudo find /etc -name "*postgresql*" -type f -delete 2>/dev/null || true
    
    print_success "Configuration files removed"
}

# Function to remove PostgreSQL repositories
remove_repositories() {
    print_status "Removing PostgreSQL repositories..."
    
    # Remove repository files
    sudo rm -f /etc/apt/sources.list.d/postgresql.list
    sudo rm -f /etc/apt/sources.list.d/pgadmin4.list
    
    # Remove GPG keys
    sudo rm -f /etc/apt/keyrings/postgresql.gpg
    sudo rm -f /etc/apt/keyrings/packages-pgadmin-org.gpg
    
    # Update package list
    sudo apt update
    
    print_success "PostgreSQL repositories removed"
}

# Function to clean up remaining files
cleanup_remaining_files() {
    print_status "Cleaning up remaining PostgreSQL files..."
    
    # Remove any PostgreSQL related files in common locations
    local cleanup_paths=(
        "/usr/share/postgresql*"
        "/usr/lib/postgresql*"
        "/var/cache/apt/archives/postgresql*"
    )
    
    for path in "${cleanup_paths[@]}"; do
        if compgen -G "$path" > /dev/null; then
            sudo rm -rf $path
        fi
    done
    
    # Clean package cache
    sudo apt clean
    sudo apt autoremove --purge -y
    
    print_success "Cleanup completed"
}

# Function to verify removal
verify_removal() {
    print_status "Verifying PostgreSQL removal..."
    
    local found_issues=false
    
    # Check for remaining packages
    if dpkg -l | grep -i postgresql > /dev/null 2>&1; then
        print_warning "Some PostgreSQL packages may still be installed:"
        dpkg -l | grep -i postgresql
        found_issues=true
    fi
    
    # Check for remaining processes
    if pgrep -f postgres > /dev/null 2>&1; then
        print_warning "Some PostgreSQL processes are still running:"
        pgrep -f postgres
        found_issues=true
    fi
    
    # Check for remaining directories
    local check_dirs=("/var/lib/postgresql" "/etc/postgresql" "/var/log/postgresql")
    for dir in "${check_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_warning "Directory still exists: $dir"
            found_issues=true
        fi
    done
    
    if [ "$found_issues" = false ]; then
        print_success "PostgreSQL has been completely removed from the system"
    else
        print_warning "Some PostgreSQL components may still remain on the system"
        print_status "You may need to manually remove them or rerun the script"
    fi
}

# Function to display post-removal information
display_post_removal_info() {
    echo
    print_success "PostgreSQL 16 uninstallation completed!"
    echo
    print_status "What was removed:"
    echo "  ✓ All PostgreSQL packages and dependencies"
    echo "  ✓ PostgreSQL system user and group"
    echo "  ✓ All databases and data files"
    echo "  ✓ Configuration files"
    echo "  ✓ Log files"
    echo "  ✓ Repository configurations"
    echo "  ✓ Service configurations"
    echo
    
    if [ -d "$HOME/postgresql_backup_"* ] 2>/dev/null; then
        print_status "Database backups (if created) are still available in:"
        ls -d "$HOME/postgresql_backup_"* 2>/dev/null || true
    fi
    
    echo
    print_status "To reinstall PostgreSQL in the future, you can use the install script."
    print_status "System reboot is recommended to ensure all changes take effect."
}

# Main uninstallation function
main() {
    check_root
    display_warning
    backup_databases
    stop_postgresql_service
    remove_postgresql_packages
    remove_pgadmin
    remove_postgresql_user
    remove_data_directories
    remove_config_files
    remove_repositories
    cleanup_remaining_files
    verify_removal
    display_post_removal_info
    
    echo
    read -p "Do you want to reboot the system now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Rebooting system in 5 seconds... Press Ctrl+C to cancel"
        sleep 5
        sudo reboot
    else
        print_status "Please remember to reboot your system later"
    fi
}

# Run main function
main "$@"