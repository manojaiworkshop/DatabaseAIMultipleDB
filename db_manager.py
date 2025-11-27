#!/usr/bin/env python3
"""
Database Import/Export Script
Supports PostgreSQL database import and export operations using configuration from config.yml
"""

import os
import sys
import yaml
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DatabaseManager:
    """Manages database import and export operations"""
    
    def __init__(self, config_path='config.yml'):
        """Initialize with configuration file"""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.docker_enabled = self.config.get('docker', {}).get('enabled', False)
        self.docker_container = self.config.get('docker', {}).get('container_name', 'postgres')
        
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config
        except FileNotFoundError:
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            sys.exit(1)
            
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.config.get('options', {}).get('log_file', 'database_operations.log')
        log_level = self.config.get('options', {}).get('log_level', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_connection_string(self):
        """Generate database connection string"""
        db_config = self.config['database']
        return f"host={db_config['host']} port={db_config['port']} dbname={db_config['database']} user={db_config['user']} password={db_config['password']}"
    
    def get_pg_env(self):
        """Get environment variables for PostgreSQL commands"""
        db_config = self.config['database']
        return {
            **os.environ,
            'PGPASSWORD': db_config['password'],
            'PGHOST': db_config['host'],
            'PGPORT': str(db_config['port']),
            'PGUSER': db_config['user'],
            'PGDATABASE': db_config['database']
        }
    
    def test_connection(self):
        """Test database connection"""
        try:
            self.logger.info("Testing database connection...")
            conn = psycopg2.connect(self.get_connection_string())
            conn.close()
            self.logger.info("✓ Database connection successful")
            return True
        except psycopg2.Error as e:
            self.logger.error(f"✗ Database connection failed: {e}")
            return False
    
    def database_exists(self, dbname):
        """Check if database exists"""
        try:
            db_config = self.config['database']
            # Connect to postgres database to check if target database exists
            conn_string = f"host={db_config['host']} port={db_config['port']} dbname=postgres user={db_config['user']} password={db_config['password']}"
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            return exists
        except psycopg2.Error as e:
            self.logger.error(f"Error checking database existence: {e}")
            return False
    
    def create_database(self, dbname):
        """Create database if it doesn't exist"""
        try:
            if self.database_exists(dbname):
                self.logger.info(f"Database '{dbname}' already exists")
                return True
                
            self.logger.info(f"Creating database '{dbname}'...")
            db_config = self.config['database']
            conn_string = f"host={db_config['host']} port={db_config['port']} dbname=postgres user={db_config['user']} password={db_config['password']}"
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            
            cursor.close()
            conn.close()
            self.logger.info(f"✓ Database '{dbname}' created successfully")
            return True
        except psycopg2.Error as e:
            self.logger.error(f"✗ Error creating database: {e}")
            return False
    
    def drop_database(self, dbname):
        """Drop database if it exists"""
        try:
            if not self.database_exists(dbname):
                self.logger.info(f"Database '{dbname}' does not exist")
                return True
                
            self.logger.warning(f"Dropping database '{dbname}'...")
            db_config = self.config['database']
            conn_string = f"host={db_config['host']} port={db_config['port']} dbname=postgres user={db_config['user']} password={db_config['password']}"
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Terminate existing connections
            cursor.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                AND pid <> pg_backend_pid()
            """, (dbname,))
            
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(dbname)))
            
            cursor.close()
            conn.close()
            self.logger.info(f"✓ Database '{dbname}' dropped successfully")
            return True
        except psycopg2.Error as e:
            self.logger.error(f"✗ Error dropping database: {e}")
            return False
    
    def import_database(self, sql_file=None):
        """Import SQL file into database"""
        if sql_file is None:
            sql_file = self.config['paths']['import_file']
        
        sql_file_path = Path(sql_file).resolve()
        
        if not sql_file_path.exists():
            self.logger.error(f"✗ SQL file not found: {sql_file}")
            return False
        
        self.logger.info(f"Starting database import from '{sql_file}'...")
        
        db_config = self.config['database']
        options = self.config.get('options', {})
        
        # Handle database creation/dropping
        if options.get('drop_existing', False):
            self.drop_database(db_config['database'])
        
        if options.get('create_database', False):
            self.create_database(db_config['database'])
        
        # Import using psql
        try:
            if self.docker_enabled:
                # Copy SQL file to Docker container and execute
                self.logger.info(f"Using Docker container: {self.docker_container}")
                
                # Copy file to container
                container_path = f"/tmp/{sql_file_path.name}"
                self.logger.info(f"Copying SQL file to container...")
                copy_cmd = ['docker', 'cp', str(sql_file_path), f"{self.docker_container}:{container_path}"]
                
                copy_result = subprocess.run(
                    copy_cmd,
                    capture_output=True,
                    text=True
                )
                
                if copy_result.returncode != 0:
                    self.logger.error(f"✗ Failed to copy file to container: {copy_result.stderr}")
                    return False
                
                # Execute psql inside container
                cmd = [
                    'docker', 'exec', '-i', self.docker_container,
                    'psql',
                    '-U', db_config['user'],
                    '-d', db_config['database'],
                    '-f', container_path
                ]
                
                env = {'PGPASSWORD': db_config['password']}
            else:
                # Direct psql command
                cmd = [
                    'psql',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['user'],
                    '-d', db_config['database'],
                    '-f', str(sql_file_path)
                ]
                
                env = self.get_pg_env()
            
            self.logger.info("Executing import command...")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            # Clean up temporary file in container
            if self.docker_enabled:
                cleanup_cmd = ['docker', 'exec', self.docker_container, 'rm', '-f', container_path]
                subprocess.run(cleanup_cmd, capture_output=True)
            
            if result.returncode == 0:
                self.logger.info("✓ Database import completed successfully")
                if result.stdout:
                    self.logger.debug(f"Output: {result.stdout}")
                return True
            else:
                self.logger.error(f"✗ Database import failed with return code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error: {result.stderr}")
                return False
                
        except FileNotFoundError as e:
            if self.docker_enabled:
                self.logger.error("✗ 'docker' command not found. Please install Docker.")
            else:
                self.logger.error("✗ 'psql' command not found. Please install PostgreSQL client tools.")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error during import: {e}")
            return False
    
    def export_database(self, output_file=None):
        """Export database to SQL file"""
        if output_file is None:
            # Add timestamp to default export file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = Path(self.config['paths']['export_file']).stem
            extension = Path(self.config['paths']['export_file']).suffix
            output_file = f"{base_name}_{timestamp}{extension}"
        
        output_file_path = Path(output_file).resolve()
        self.logger.info(f"Starting database export to '{output_file}'...")
        
        db_config = self.config['database']
        options = self.config.get('options', {})
        backup_format = options.get('backup_format', 'plain')
        
        try:
            if self.docker_enabled:
                # Export from Docker container
                self.logger.info(f"Using Docker container: {self.docker_container}")
                
                container_path = f"/tmp/{output_file_path.name}"
                
                # Execute pg_dump inside container
                cmd = [
                    'docker', 'exec', '-i', self.docker_container,
                    'pg_dump',
                    '-U', db_config['user'],
                    '-d', db_config['database'],
                    '-f', container_path
                ]
                
                # Add format option if not plain
                if backup_format != 'plain':
                    cmd.extend(['-F', backup_format[0]])  # c for custom, d for directory, t for tar
                
                env = {'PGPASSWORD': db_config['password']}
                
                self.logger.info("Executing export command in container...")
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"✗ Database export failed with return code {result.returncode}")
                    if result.stderr:
                        self.logger.error(f"Error: {result.stderr}")
                    return False
                
                # Copy file from container to host
                self.logger.info("Copying export file from container...")
                copy_cmd = ['docker', 'cp', f"{self.docker_container}:{container_path}", str(output_file_path)]
                
                copy_result = subprocess.run(
                    copy_cmd,
                    capture_output=True,
                    text=True
                )
                
                # Clean up temporary file in container
                cleanup_cmd = ['docker', 'exec', self.docker_container, 'rm', '-f', container_path]
                subprocess.run(cleanup_cmd, capture_output=True)
                
                if copy_result.returncode != 0:
                    self.logger.error(f"✗ Failed to copy file from container: {copy_result.stderr}")
                    return False
                    
            else:
                # Direct pg_dump command
                cmd = [
                    'pg_dump',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['user'],
                    '-d', db_config['database'],
                    '-f', str(output_file_path)
                ]
                
                # Add format option if not plain
                if backup_format != 'plain':
                    cmd.extend(['-F', backup_format[0]])  # c for custom, d for directory, t for tar
                
                env = self.get_pg_env()
                
                self.logger.info("Executing export command...")
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"✗ Database export failed with return code {result.returncode}")
                    if result.stderr:
                        self.logger.error(f"Error: {result.stderr}")
                    return False
            
            file_size = os.path.getsize(output_file_path) / (1024 * 1024)  # Size in MB
            self.logger.info(f"✓ Database export completed successfully")
            self.logger.info(f"  Output file: {output_file}")
            self.logger.info(f"  File size: {file_size:.2f} MB")
            return True
                
        except FileNotFoundError as e:
            if self.docker_enabled:
                self.logger.error("✗ 'docker' command not found. Please install Docker.")
            else:
                self.logger.error("✗ 'pg_dump' command not found. Please install PostgreSQL client tools.")
            return False
        except Exception as e:
            self.logger.error(f"✗ Error during export: {e}")
            return False


def print_usage():
    """Print usage information"""
    print("""
Database Import/Export Tool

Usage:
    python db_manager.py [command] [options]

Commands:
    import              Import SQL file into database
    export              Export database to SQL file
    test                Test database connection
    
Options:
    --config PATH       Path to config file (default: config.yml)
    --file PATH         Path to SQL file for import/export
    
Examples:
    python db_manager.py test
    python db_manager.py import
    python db_manager.py import --file backup.sql
    python db_manager.py export
    python db_manager.py export --file my_backup.sql
    python db_manager.py --config custom_config.yml import
    """)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    # Parse arguments
    config_file = 'config.yml'
    sql_file = None
    command = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '--config' and i + 1 < len(sys.argv):
            config_file = sys.argv[i + 1]
            i += 2
        elif arg == '--file' and i + 1 < len(sys.argv):
            sql_file = sys.argv[i + 1]
            i += 2
        elif arg in ['import', 'export', 'test']:
            command = arg
            i += 1
        else:
            print(f"Unknown argument: {arg}")
            print_usage()
            sys.exit(1)
    
    if command is None:
        print("Error: No command specified")
        print_usage()
        sys.exit(1)
    
    # Initialize database manager
    try:
        db_manager = DatabaseManager(config_file)
    except Exception as e:
        print(f"Error initializing database manager: {e}")
        sys.exit(1)
    
    # Execute command
    success = False
    
    if command == 'test':
        success = db_manager.test_connection()
    elif command == 'import':
        success = db_manager.import_database(sql_file)
    elif command == 'export':
        success = db_manager.export_database(sql_file)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
