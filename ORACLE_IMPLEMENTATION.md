# Oracle Database Support - Complete Implementation

## Overview
DatabaseAI now supports Oracle Database with full feature parity including connection management, schema introspection, and Oracle SQL dialect support.

## ✅ Completed Implementation

### Backend Changes

#### 1. **Data Models** (`backend/app/models/schemas.py`)
- Added `DatabaseType` enum with `ORACLE`, `POSTGRESQL`, `MYSQL`, `SQLITE`
- Extended `DatabaseConnection` model with Oracle-specific fields:
  - `sid`: Oracle System Identifier (Optional)
  - `service_name`: Oracle Service Name (Optional)
  - Made host/port/username/password optional for SQLite support

#### 2. **Database Adapter** (`backend/app/database_adapters/oracle_adapter.py`)
- Full Oracle adapter implementation using `cx_Oracle`
- Supports both SID and Service Name connections
- Oracle-specific schema introspection:
  - Uses `DBA_USERS` or `ALL_USERS` for schema list
  - Uses `ALL_TABLES`, `ALL_TAB_COLUMNS` for table metadata
  - Handles Oracle's dual concept (queries vs tables)
- Proper Oracle DSN construction
- Sample data fetching with `ROWNUM` instead of `LIMIT`

#### 3. **Database Service** (`backend/app/services/database.py`)
- Refactored to use adapter pattern
- Tracks current `database_type` for LLM context
- All database operations delegated to appropriate adapter
- `get_database_type()` method for SQL dialect detection

#### 4. **API Routes** (`backend/app/routes/api.py`)
- Updated `/database/connect` endpoint to accept all connection parameters
- Passes `database_type`, `sid`, `service_name` to database service
- Returns database type in connection response

#### 5. **LLM Service** (`backend/app/services/llm.py`)
- Added `database_type` parameter to `generate_sql()` method
- Implemented `_get_database_specific_instructions()` for dialect-specific SQL:
  - **Oracle**: DUAL, ROWNUM, SYSDATE, TO_DATE, || operator
  - **PostgreSQL**: LIMIT, information_schema, NOW()
  - **MySQL**: LIMIT, CONCAT(), backticks, SHOW commands
  - **SQLite**: LIMIT, sqlite_master, datetime()
- Dynamic system prompts based on database type

#### 6. **SQL Agent** (`backend/app/services/sql_agent.py`)
- Retrieves database type from `db_service`
- Passes database type to LLM for appropriate SQL generation
- Logs database type in query generation process

#### 7. **Dependencies**
- **requirements.txt**: Added `cx-Oracle==8.3.0`, `mysql-connector-python==8.2.0`
- **backend.spec**: Added hidden imports for `cx_Oracle`, `mysql.connector`, `sqlite3`

### Frontend Changes

#### 8. **Connection Page** (`frontend/src/pages/ConnectionPage.js`)
- Database type selector with 4 options (PostgreSQL, Oracle, MySQL, SQLite)
- Dynamic form fields based on selection:
  - **PostgreSQL/MySQL**: Host, Port, Database, Username, Password
  - **Oracle**: Host, Port, SID/Service Name (either/or), Username, Password
  - **SQLite**: File path only
- Auto-fills default ports when switching database types:
  - PostgreSQL: 5432
  - Oracle: 1521
  - MySQL: 3306
- Visual card-based selector for better UX
- Help text for Oracle SID/Service Name fields

### Docker & Testing

#### 9. **Docker Compose** (`docker-compose.oracle.yml`)
- Oracle XE (Express Edition) container setup
- DatabaseAI container configured for Oracle
- Volume mounting for data persistence
- Health checks for service readiness
- Network configuration for inter-container communication

#### 10. **Initialization Scripts** (`init-oracle/01-init-schema.sql`)
- Sample schema with employees, departments, projects tables
- Demo user creation with proper privileges
- Sample data insertion
- Example view creation

## 🚀 Usage

### 1. Start Oracle Environment
```bash
# Start Oracle database and DatabaseAI
docker-compose -f docker-compose.oracle.yml up -d

# Check Oracle is ready
docker logs oracle-db

# Oracle should be accessible at localhost:1521
```

### 2. Connect via UI
1. Open http://localhost in browser
2. Select **Oracle** database type
3. Fill in connection details:
   - **Host**: `oracle-db` (or `localhost` for external connection)
   - **Port**: `1521`
   - **Service Name**: `XEPDB1` (for Oracle XE)
   - **Username**: `system`
   - **Password**: `oracle123`
4. Click "Connect to Database"

### 3. Alternative: Connect to Demo Schema
```
Host: oracle-db
Port: 1521
Service Name: XEPDB1
Username: demouser
Password: demo123
```

### 4. Test Queries
Try these natural language queries:
- "Show all employees"
- "How many departments are there?"
- "List employees with salary greater than 80000"
- "Show employee details with department information"

## 📋 Oracle Connection Options

### SID vs Service Name
- **SID (System Identifier)**: Legacy identifier for Oracle instances
  - Example: `ORCL`
  - DSN: `host:port/sid`
  
- **Service Name**: Modern service-based identifier
  - Example: `XEPDB1` (Pluggable Database)
  - DSN: `host:port/?service_name=servicename`
  
**Provide EITHER SID or Service Name, not both**

### Common Oracle Ports
- **1521**: Default Oracle listener port
- **5500**: Oracle Enterprise Manager Express

## 🔧 Configuration

### Environment Variables (for Docker)
```yaml
environment:
  - DATABASE_TYPE=oracle
  - ORACLE_HOST=oracle-db
  - ORACLE_PORT=1521
  - ORACLE_SERVICE_NAME=XEPDB1
  - ORACLE_USER=system
  - ORACLE_PASSWORD=oracle123
```

### Manual Connection (Non-Docker)
Use the UI connection form with your Oracle instance details:
- Host: Your Oracle server IP/hostname
- Port: Usually 1521
- SID or Service Name: From your DBA
- Username/Password: Oracle credentials

## 📊 Oracle SQL Dialect Support

DatabaseAI automatically generates Oracle-compatible SQL:

### Row Limiting
```sql
-- PostgreSQL/MySQL
SELECT * FROM employees LIMIT 10;

-- Oracle (auto-generated)
SELECT * FROM employees WHERE ROWNUM <= 10;
```

### Current Timestamp
```sql
-- PostgreSQL/MySQL
SELECT NOW();

-- Oracle (auto-generated)
SELECT SYSDATE FROM DUAL;
```

### String Concatenation
```sql
-- MySQL
SELECT CONCAT(first_name, ' ', last_name) FROM employees;

-- Oracle (auto-generated)
SELECT first_name || ' ' || last_name FROM employees;
```

## 🐛 Troubleshooting

### Oracle Connection Issues
```bash
# Check Oracle is running
docker ps | grep oracle

# View Oracle logs
docker logs oracle-db

# Test connection from host
docker exec -it oracle-db sqlplus system/oracle123@//localhost:1521/XEPDB1
```

### cx_Oracle Installation Issues
If you encounter installation errors with cx_Oracle:
```bash
# Install Oracle Instant Client first
# For Ubuntu/Debian:
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basiclite-linuxx64.zip
unzip instantclient-basiclite-linuxx64.zip
export LD_LIBRARY_PATH=/path/to/instantclient_19_X:$LD_LIBRARY_PATH

# Then install cx_Oracle
pip install cx-Oracle
```

### Common Errors

**Error: "ORA-12154: TNS:could not resolve the connect identifier"**
- Solution: Check service name or SID is correct
- Verify Oracle listener is running on specified port

**Error: "ORA-01017: invalid username/password"**
- Solution: Verify credentials
- For Docker: Use `system` / `oracle123` by default

**Error: "DPI-1047: Cannot locate a 64-bit Oracle Client library"**
- Solution: Install Oracle Instant Client
- Set `LD_LIBRARY_PATH` environment variable

## 🔐 Security Notes

1. **Never commit passwords** to version control
2. Use environment variables for production credentials
3. Oracle XE is for **development/testing only**
4. For production, use Oracle Standard/Enterprise Edition
5. Implement proper user access controls and roles

## 📚 Next Steps

- ✅ Oracle support complete
- 🔄 MySQL support (adapter created, needs testing)
- 🔄 SQLite support (adapter created, needs testing)
- 📋 Create MySQL/SQLite docker-compose files
- 🔄 Test all adapters with real databases
- 📝 Add database-specific optimization hints

## 🎯 Testing Checklist

- [x] Oracle adapter connects successfully
- [x] Schema introspection works (users, tables, columns)
- [x] SQL generation uses Oracle dialect (ROWNUM, SYSDATE, etc.)
- [x] Query execution returns results
- [x] Sample data fetching works
- [x] Frontend displays Oracle-specific fields
- [ ] Comprehensive query testing with complex joins
- [ ] Performance testing with large schemas
- [ ] Error handling with invalid credentials
- [ ] Network failure resilience

## 📖 References

- [cx_Oracle Documentation](https://cx-oracle.readthedocs.io/)
- [Oracle SQL Reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/)
- [Oracle Docker Images](https://github.com/gvenzl/oci-oracle-xe)
