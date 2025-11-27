# Oracle User Creation Script

## 📋 Overview

This script creates a new Oracle database user with full DBA privileges, suitable for PGAIView/DatabaseAI operations.

## 🚀 Quick Start

### Method 1: Run Shell Script (Recommended)
```bash
./create_oracle_user.sh
```

### Method 2: Run Python Script Directly
```bash
python3 create_oracle_user.py
```

## ⚙️ Configuration

### Environment Variables

You can customize the configuration using environment variables:

```bash
# Oracle admin password (default: oracle)
export ORACLE_PASSWORD="your_system_password"

# New user credentials
export NEW_USER="myuser"
export NEW_PASSWORD="mypassword"

# Run the script
./create_oracle_user.sh
```

### Default Values

- **Database Connection**: `localhost:1521/XE`
- **Admin User**: `system` (with DBA privileges)
- **Admin Password**: `oracle123`
- **New Username**: `pgaiview`
- **New Password**: `pgaiview123`
- **Default Tablespace**: `USERS`
- **Temporary Tablespace**: `TEMP`

## 🎯 What the Script Does

1. **Connects as SYSTEM** - Uses system user with DBA privileges
2. **Checks if user exists** - Prompts to drop if already exists
3. **Creates new user** - With specified username and password
4. **Grants privileges**:
   - `CONNECT` - Basic connection privilege
   - `RESOURCE` - Create objects
   - `DBA` - Full database administrator role
   - `CREATE SESSION, TABLE, VIEW, SEQUENCE, PROCEDURE, TRIGGER, SYNONYM, TYPE`
   - `SELECT/INSERT/UPDATE/DELETE ANY TABLE`
   - `EXECUTE ANY PROCEDURE`
   - `UNLIMITED TABLESPACE`
5. **Verifies creation** - Checks user details and privileges
6. **Tests connection** - Creates test table to validate functionality

## 📦 Prerequisites

### 1. Python Requirements

```bash
pip install oracledb
```

### 2. Running Oracle Database

Make sure Oracle database is running:

```bash
docker compose -f docker-compose.oracle.yml up
```

Wait for: `DATABASE IS READY TO USE!`

## 💡 Usage Examples

### Example 1: Default User (pgaiview)
```bash
./create_oracle_user.sh
```

### Example 2: Custom User
```bash
export NEW_USER="analytics"
export NEW_PASSWORD="analytics2024"
./create_oracle_user.sh
```

### Example 3: Different Oracle Password
```bash
export ORACLE_PASSWORD="mysystempassword"
./create_oracle_user.sh
```

### Example 4: All Custom
```bash
ORACLE_PASSWORD="admin123" NEW_USER="dataai" NEW_PASSWORD="dataai2024" ./create_oracle_user.sh
```

## 📊 Script Output

The script provides detailed output:

```
======================================================================
 Oracle User Creation Script
 For PGAIView/DatabaseAI
======================================================================

⏰ Started: 2025-11-27 10:30:00

📋 Configuration:
   • Database: localhost:1521/XE
   • Admin User: system
   • New User: pgaiview
   • Default Tablespace: USERS
   • Temporary Tablespace: TEMP

🔌 Connecting to Oracle Database as SYSDBA...
   ✓ Connected successfully

📊 Database Version: Oracle Database 21c Express Edition...

🔍 Step 1: Checking if user exists...
   ✓ User pgaiview does not exist

👤 Step 2: Creating new user...
   Creating user: pgaiview
   ✓ User pgaiview created successfully

🔐 Step 3: Granting privileges...
   Granting privileges to: pgaiview
   ✓ Privileges granted to pgaiview

💾 Step 4: Committing changes...
   ✓ Changes committed

✅ Step 5: Verifying user creation...
   Verifying user: pgaiview
   ✓ Username: PGAIVIEW
   ✓ Status: OPEN
   ✓ Default Tablespace: USERS
   ✓ Temp Tablespace: TEMP
   ✓ Created: 2025-11-27 10:30:01
   ✓ System Privileges: 15
   ✓ Granted Roles: CONNECT, DBA, RESOURCE

🧪 Step 6: Testing new user connection...
   Testing connection with new user: pgaiview
   ✓ Connected as: PGAIVIEW
   ✓ Test table created successfully
   ✓ Test insert successful
   ✓ Test select successful: (1, 'Test', ...)
   ✓ Test table dropped
   ✓ Connection test successful!

======================================================================
 ✓ USER CREATION SUCCESSFUL!
======================================================================

📝 Connection Details:
   • Username: pgaiview
   • Password: pgaiview123
   • Connection String: localhost:1521/XE

📌 Sample Connection Code:
   import oracledb
   
   connection = oracledb.connect(
       user='pgaiview',
       password='pgaiview123',
       dsn='localhost:1521/XE'
   )

⏰ Completed: 2025-11-27 10:30:05
```

## 🔐 Privileges Granted

The created user receives the following privileges:

### System Privileges
- `CONNECT` - Connect to database
- `RESOURCE` - Create objects
- `DBA` - Full administrative access
- `CREATE SESSION` - Start sessions
- `ALTER SESSION` - Modify session parameters
- `UNLIMITED TABLESPACE` - No space restrictions

### Object Privileges
- `CREATE TABLE, VIEW, SEQUENCE, PROCEDURE, TRIGGER, SYNONYM, TYPE`
- `SELECT ANY TABLE` - Query any table
- `INSERT ANY TABLE` - Insert into any table
- `UPDATE ANY TABLE` - Update any table
- `DELETE ANY TABLE` - Delete from any table
- `EXECUTE ANY PROCEDURE` - Execute any stored procedure

## 🔄 Update Existing User

If the user already exists, the script will:
1. Detect existing user
2. Prompt: "Do you want to drop and recreate? (yes/no)"
3. If yes: Drop CASCADE and recreate
4. If no: Exit without changes

## 🐛 Troubleshooting

### Connection Refused
```
Error: ORA-12541: TNS:no listener
```
**Solution**: Ensure Oracle container is running
```bash
docker compose -f docker-compose.oracle.yml up -d
```

### Invalid Password
```
Error: ORA-01017: invalid username/password
```
**Solution**: Check ORACLE_PASSWORD environment variable matches your system password

### Permission Denied
```
Error: Insufficient privileges
```
**Solution**: Ensure connecting as SYSTEM user with DBA privileges

### Module Not Found
```
Error: No module named 'oracledb'
```
**Solution**: Install oracledb
```bash
pip install oracledb
```

## 📝 Notes

1. **SYSTEM User**: Script connects as SYSTEM user (which has DBA privileges)
2. **CASCADE Drop**: When dropping existing user, all objects are removed
3. **Password Security**: Change default passwords in production
4. **Connection Test**: Script validates functionality after creation
5. **Commit**: All changes are committed automatically

## 🔗 Integration with DatabaseAI

After creating the user, update your DatabaseAI configuration:

```yaml
# In config.yml or app_config.yml
oracle:
  host: localhost
  port: 1521
  service_name: XE
  username: pgaiview
  password: pgaiview123
```

Or use connection string:
```
pgaiview/pgaiview123@localhost:1521/XE
```

## 📞 Support

For issues or questions, refer to:
- Oracle documentation
- DatabaseAI documentation
- Check Docker logs: `docker logs oracle-db`
