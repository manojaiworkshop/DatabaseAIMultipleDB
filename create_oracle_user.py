#!/usr/bin/env python3
"""
Oracle Database User Creation Script
Creates a user with DBA privileges for PGAIView/DatabaseAI
"""

import oracledb
import sys
import os
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

# Oracle Connection Details
ORACLE_CONFIG = {
    'user': 'system',
    'password': os.environ.get('ORACLE_PASSWORD', 'oracle123'),
    'dsn': os.environ.get('ORACLE_DSN', 'localhost:1521/XE'),
    'mode': None  # Connect as normal user (SYSTEM has DBA privileges)
}

# New User Configuration
NEW_USER_CONFIG = {
    'username': os.environ.get('NEW_USER', 'pgaiview'),
    'password': os.environ.get('NEW_PASSWORD', 'pgaiview123'),
    'default_tablespace': 'USERS',
    'temporary_tablespace': 'TEMP'
}

# ============================================================================
# SQL Statements
# ============================================================================

def get_create_user_sql(username, password, default_ts, temp_ts):
    """Generate CREATE USER SQL"""
    return f"""
    CREATE USER {username}
    IDENTIFIED BY {password}
    DEFAULT TABLESPACE {default_ts}
    TEMPORARY TABLESPACE {temp_ts}
    QUOTA UNLIMITED ON {default_ts}
    """

def get_grant_privileges_sql(username):
    """Generate GRANT privileges SQL"""
    privileges = [
        # System privileges
        f"GRANT CONNECT TO {username}",
        f"GRANT RESOURCE TO {username}",
        f"GRANT DBA TO {username}",
        
        # Session privileges
        f"GRANT CREATE SESSION TO {username}",
        f"GRANT ALTER SESSION TO {username}",
        
        # Object privileges
        f"GRANT CREATE TABLE TO {username}",
        f"GRANT CREATE VIEW TO {username}",
        f"GRANT CREATE SEQUENCE TO {username}",
        f"GRANT CREATE PROCEDURE TO {username}",
        f"GRANT CREATE TRIGGER TO {username}",
        f"GRANT CREATE SYNONYM TO {username}",
        f"GRANT CREATE TYPE TO {username}",
        
        # Additional privileges
        f"GRANT SELECT ANY TABLE TO {username}",
        f"GRANT INSERT ANY TABLE TO {username}",
        f"GRANT UPDATE ANY TABLE TO {username}",
        f"GRANT DELETE ANY TABLE TO {username}",
        f"GRANT EXECUTE ANY PROCEDURE TO {username}",
        
        # Administrative privileges
        f"GRANT UNLIMITED TABLESPACE TO {username}",
    ]
    return privileges

# ============================================================================
# Main Functions
# ============================================================================

def check_user_exists(cursor, username):
    """Check if user already exists"""
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM dba_users WHERE username = UPPER(:username)",
            username=username
        )
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"Error checking user existence: {e}")
        return False

def drop_user(cursor, username):
    """Drop existing user"""
    try:
        print(f"   Dropping existing user: {username}")
        cursor.execute(f"DROP USER {username} CASCADE")
        print(f"   ✓ User {username} dropped successfully")
        return True
    except Exception as e:
        print(f"   ✗ Error dropping user: {e}")
        return False

def create_user(cursor, username, password, default_ts, temp_ts):
    """Create new database user"""
    try:
        print(f"   Creating user: {username}")
        sql = get_create_user_sql(username, password, default_ts, temp_ts)
        cursor.execute(sql)
        print(f"   ✓ User {username} created successfully")
        return True
    except Exception as e:
        print(f"   ✗ Error creating user: {e}")
        return False

def grant_privileges(cursor, username):
    """Grant all privileges to user"""
    try:
        print(f"   Granting privileges to: {username}")
        privileges = get_grant_privileges_sql(username)
        
        for privilege_sql in privileges:
            try:
                cursor.execute(privilege_sql)
            except Exception as e:
                print(f"   ⚠ Warning: {privilege_sql.split()[1]} - {e}")
        
        print(f"   ✓ Privileges granted to {username}")
        return True
    except Exception as e:
        print(f"   ✗ Error granting privileges: {e}")
        return False

def verify_user(cursor, username):
    """Verify user creation and privileges"""
    try:
        print(f"\n   Verifying user: {username}")
        
        # Check user details
        cursor.execute("""
            SELECT username, account_status, default_tablespace, 
                   temporary_tablespace, created
            FROM dba_users 
            WHERE username = UPPER(:username)
        """, username=username)
        
        row = cursor.fetchone()
        if row:
            print(f"   ✓ Username: {row[0]}")
            print(f"   ✓ Status: {row[1]}")
            print(f"   ✓ Default Tablespace: {row[2]}")
            print(f"   ✓ Temp Tablespace: {row[3]}")
            print(f"   ✓ Created: {row[4]}")
            
            # Check privileges
            cursor.execute("""
                SELECT COUNT(*) 
                FROM dba_sys_privs 
                WHERE grantee = UPPER(:username)
            """, username=username)
            
            priv_count = cursor.fetchone()[0]
            print(f"   ✓ System Privileges: {priv_count}")
            
            # Check roles
            cursor.execute("""
                SELECT granted_role 
                FROM dba_role_privs 
                WHERE grantee = UPPER(:username)
                ORDER BY granted_role
            """, username=username)
            
            roles = [row[0] for row in cursor.fetchall()]
            print(f"   ✓ Granted Roles: {', '.join(roles)}")
            
            return True
        else:
            print(f"   ✗ User {username} not found")
            return False
            
    except Exception as e:
        print(f"   ✗ Error verifying user: {e}")
        return False

def test_connection(username, password, dsn):
    """Test connection with new user"""
    try:
        print(f"\n   Testing connection with new user: {username}")
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        print(f"   ✓ Connected as: {current_user}")
        
        # Test table creation
        cursor.execute("""
            BEGIN
                EXECUTE IMMEDIATE 'DROP TABLE test_table CASCADE CONSTRAINTS';
            EXCEPTION
                WHEN OTHERS THEN NULL;
            END;
        """)
        cursor.execute("""
            CREATE TABLE test_table (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print(f"   ✓ Test table created successfully")
        
        # Test insert
        cursor.execute("""
            INSERT INTO test_table (id, name) VALUES (1, 'Test')
        """)
        connection.commit()
        print(f"   ✓ Test insert successful")
        
        # Test select
        cursor.execute("SELECT * FROM test_table")
        row = cursor.fetchone()
        print(f"   ✓ Test select successful: {row}")
        
        # Cleanup
        cursor.execute("DROP TABLE test_table")
        print(f"   ✓ Test table dropped")
        
        cursor.close()
        connection.close()
        print(f"   ✓ Connection test successful!")
        return True
        
    except Exception as e:
        print(f"   ✗ Connection test failed: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 70)
    print(" Oracle Database User Creation Script")
    print(" For PGAIView/DatabaseAI")
    print("=" * 70)
    print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    username = NEW_USER_CONFIG['username']
    password = NEW_USER_CONFIG['password']
    default_ts = NEW_USER_CONFIG['default_tablespace']
    temp_ts = NEW_USER_CONFIG['temporary_tablespace']
    
    print(f"📋 Configuration:")
    print(f"   • Database: {ORACLE_CONFIG['dsn']}")
    print(f"   • Admin User: {ORACLE_CONFIG['user']}")
    print(f"   • New User: {username}")
    print(f"   • Default Tablespace: {default_ts}")
    print(f"   • Temporary Tablespace: {temp_ts}")
    print()
    
    try:
        # Connect as SYSTEM (has DBA privileges)
        print("🔌 Connecting to Oracle Database as SYSTEM...")
        if ORACLE_CONFIG['mode']:
            connection = oracledb.connect(
                user=ORACLE_CONFIG['user'],
                password=ORACLE_CONFIG['password'],
                dsn=ORACLE_CONFIG['dsn'],
                mode=ORACLE_CONFIG['mode']
            )
        else:
            connection = oracledb.connect(
                user=ORACLE_CONFIG['user'],
                password=ORACLE_CONFIG['password'],
                dsn=ORACLE_CONFIG['dsn']
            )
        cursor = connection.cursor()
        print("   ✓ Connected successfully\n")
        
        # Check database version
        cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
        version = cursor.fetchone()[0]
        print(f"📊 Database Version: {version}\n")
        
        # Step 1: Check if user exists
        print("🔍 Step 1: Checking if user exists...")
        user_exists = check_user_exists(cursor, username)
        
        if user_exists:
            print(f"   ⚠ User {username} already exists")
            response = input(f"   Do you want to drop and recreate? (yes/no): ").lower()
            if response in ['yes', 'y']:
                if not drop_user(cursor, username):
                    print("   ✗ Failed to drop user. Exiting.")
                    sys.exit(1)
            else:
                print("   Skipping user creation.")
                sys.exit(0)
        else:
            print(f"   ✓ User {username} does not exist")
        
        print()
        
        # Step 2: Create user
        print("👤 Step 2: Creating new user...")
        if not create_user(cursor, username, password, default_ts, temp_ts):
            print("   ✗ Failed to create user. Exiting.")
            sys.exit(1)
        print()
        
        # Step 3: Grant privileges
        print("🔐 Step 3: Granting privileges...")
        if not grant_privileges(cursor, username):
            print("   ✗ Failed to grant privileges. Exiting.")
            sys.exit(1)
        print()
        
        # Step 4: Commit changes
        print("💾 Step 4: Committing changes...")
        connection.commit()
        print("   ✓ Changes committed\n")
        
        # Step 5: Verify user
        print("✅ Step 5: Verifying user creation...")
        verify_user(cursor, username)
        
        # Close SYSDBA connection
        cursor.close()
        connection.close()
        
        # Step 6: Test connection
        print("\n🧪 Step 6: Testing new user connection...")
        test_connection(username, password, ORACLE_CONFIG['dsn'])
        
        # Success summary
        print("\n" + "=" * 70)
        print(" ✓ USER CREATION SUCCESSFUL!")
        print("=" * 70)
        print(f"\n📝 Connection Details:")
        print(f"   • Username: {username}")
        print(f"   • Password: {password}")
        print(f"   • Connection String: {ORACLE_CONFIG['dsn']}")
        print(f"\n📌 Sample Connection Code:")
        print(f"""
   import oracledb
   
   connection = oracledb.connect(
       user='{username}',
       password='{password}',
       dsn='{ORACLE_CONFIG['dsn']}'
   )
        """)
        print("\n⏰ Completed: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"\n❌ Database Error:")
        print(f"   Code: {error.code}")
        print(f"   Message: {error.message}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Check if oracledb is installed
    try:
        import oracledb
    except ImportError:
        print("❌ Error: oracledb module not installed")
        print("   Install with: pip install oracledb")
        sys.exit(1)
    
    main()
