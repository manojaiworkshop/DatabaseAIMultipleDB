# Multi-Database Support Implementation Guide

## Overview
Extension of DatabaseAI to support PostgreSQL, MySQL, Oracle, and SQLite with modular architecture.

## Architecture

### 1. Database Adapters (Created)
✅ `backend/app/database_adapters/base_adapter.py` - Base abstract class
✅ `backend/app/database_adapters/postgres_adapter.py` - PostgreSQL implementation
✅ `backend/app/database_adapters/mysql_adapter.py` - MySQL implementation  
✅ `backend/app/database_adapters/oracle_adapter.py` - Oracle implementation
⏳ `backend/app/database_adapters/sqlite_adapter.py` - **NEED TO CREATE**
⏳ `backend/app/database_adapters/adapter_factory.py` - **NEED TO CREATE**

### 2. Backend Changes Required

#### A. Update Models (`backend/app/models/schemas.py`)
```python
from enum import Enum

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLITE = "sqlite"

class DatabaseConnection(BaseModel):
    database_type: DatabaseType = Field(..., description="Type of database")
    host: Optional[str] = Field(None, description="Database host (not for SQLite)")
    port: Optional[int] = Field(None, description="Database port")
    database: str = Field(..., description="Database name or file path for SQLite")
    username: Optional[str] = Field(None, description="Username (not for SQLite)")
    password: Optional[str] = Field(None, description="Password")
    
    # Oracle specific
    sid: Optional[str] = Field(None, description="Oracle SID")
    service_name: Optional[str] = Field(None, description="Oracle Service Name")
    
    # Legacy fields
    use_docker: bool = Field(default=False)
    docker_container: Optional[str] = None
```

#### B. Update Database Service (`backend/app/services/database.py`)
```python
from ..database_adapters import DatabaseAdapterFactory

class DatabaseService:
    def __init__(self):
        self.adapter = None
        self.connection_params = None
        
    def set_connection(self, database_type: str, **params):
        """Set database connection using factory pattern"""
        self.connection_params = {
            'database_type': database_type,
            **params
        }
        
        # Create appropriate adapter
        self.adapter = DatabaseAdapterFactory.create_adapter(
            database_type, 
            self.connection_params
        )
    
    def test_connection(self):
        if not self.adapter:
            raise ValueError("No database adapter configured")
        return self.adapter.test_connection()
    
    def get_database_snapshot(self):
        if not self.adapter:
            raise ValueError("No database adapter configured")
        return self.adapter.get_database_snapshot()
    
    # ... delegate all other methods to adapter
```

#### C. Update LLM Service for SQL Dialects
```python
def generate_sql(self, question: str, schema_context: str, 
                database_type: str = "postgresql"):
    """Generate SQL with database-specific dialect"""
    
    dialect_map = {
        'postgresql': 'PostgreSQL',
        'mysql': 'MySQL',
        'oracle': 'Oracle SQL',
        'sqlite': 'SQLite'
    }
    
    sql_dialect = dialect_map.get(database_type, 'PostgreSQL')
    
    system_prompt = f'''You are a {sql_dialect} query generator...
    
Generate ONLY {sql_dialect} compatible queries...
```

### 3. Frontend Changes Required

#### A. Update Connection Page (`frontend/src/pages/ConnectionPage.js`)

Add database type selector:
```javascript
const [formData, setFormData] = useState({
  database_type: 'postgresql',
  host: 'localhost',
  port: 5432,
  database: '',
  username: 'postgres',
  password: '',
  // Oracle specific
  sid: '',
  service_name: '',
  // SQLite specific
  file_path: '',
  use_docker: false,
  docker_container: '',
});

// Dynamic port defaults
const getDefaultPort = (dbType) => {
  const ports = {
    postgresql: 5432,
    mysql: 3306,
    oracle: 1521,
    sqlite: null
  };
  return ports[dbType];
};

// Handle database type change
const handleDatabaseTypeChange = (newType) => {
  setFormData({
    ...formData,
    database_type: newType,
    port: getDefaultPort(newType),
    username: newType === 'sqlite' ? '' : formData.username
  });
};

// Render dynamic form fields based on database type
{formData.database_type === 'oracle' && (
  <>
    <input name="sid" placeholder="SID" />
    <input name="service_name" placeholder="Service Name" />
  </>
)}

{formData.database_type === 'sqlite' && (
  <input name="file_path" placeholder="/path/to/database.db" />
)}

{formData.database_type !== 'sqlite' && (
  <>
    <input name="host" />
    <input name="port" />
    <input name="username" />
    <input name="password" type="password" />
  </>
)}
```

#### B. Add Database Type Selector Component
```javascript
const DatabaseTypeSelector = ({ value, onChange }) => {
  const databases = [
    { type: 'postgresql', name: 'PostgreSQL', icon: '🐘' },
    { type: 'mysql', name: 'MySQL', icon: '🐬' },
    { type: 'oracle', name: 'Oracle', icon: '🔴' },
    { type: 'sqlite', name: 'SQLite', icon: '📁' }
  ];
  
  return (
    <div className="grid grid-cols-4 gap-4">
      {databases.map(db => (
        <button
          key={db.type}
          className={value === db.type ? 'selected' : ''}
          onClick={() => onChange(db.type)}
        >
          <span>{db.icon}</span>
          <span>{db.name}</span>
        </button>
      ))}
    </div>
  );
};
```

### 4. Docker Compose Files

#### `docker-compose.postgres.yml`
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: testdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  pgaiview:
    image: opendockerai/pgaiview:latest
    ports:
      - "80:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

#### `docker-compose.mysql.yml`
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: testdb
      MYSQL_USER: dbuser
      MYSQL_PASSWORD: dbpass
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  pgaiview:
    image: opendockerai/pgaiview:latest
    ports:
      - "80:80"
    depends_on:
      - mysql

volumes:
  mysql_data:
```

#### `docker-compose.oracle.yml`
```yaml
version: '3.8'
services:
  oracle:
    image: gvenzl/oracle-xe:latest
    environment:
      ORACLE_PASSWORD: oracle
    ports:
      - "1521:1521"
    volumes:
      - oracle_data:/opt/oracle/oradata

  pgaiview:
    image: opendockerai/pgaiview:latest
    ports:
      - "80:80"
    depends_on:
      - oracle

volumes:
  oracle_data:
```

### 5. Requirements Updates

Add to `backend/requirements.txt`:
```
psycopg2-binary==2.9.9  # PostgreSQL (existing)
mysql-connector-python==8.2.0  # MySQL
cx-Oracle==8.3.0  # Oracle
# SQLite is built-in to Python
```

### 6. Backend Spec Updates

Add to `backend.spec`:
```python
hiddenimports=[
    # ... existing ...
    'mysql.connector',
    'cx_Oracle',
],
```

## Implementation Steps

1. ✅ Create base adapter and PostgreSQL adapter
2. ✅ Create MySQL adapter
3. ✅ Create Oracle adapter
4. ⏳ Create SQLite adapter
5. ⏳ Create adapter factory
6. ⏳ Update database service to use adapters
7. ⏳ Update Pydantic models
8. ⏳ Update frontend connection page
9. ⏳ Update LLM service for SQL dialects
10. ⏳ Create Docker Compose files
11. ⏳ Update requirements and rebuild

## Testing Checklist

- [ ] PostgreSQL connection and queries
- [ ] MySQL connection and queries
- [ ] Oracle connection and queries (with SID and Service Name)
- [ ] SQLite connection and queries
- [ ] Schema tree rendering for each database
- [ ] SQL generation with correct dialect
- [ ] Neo4j sync with different databases
- [ ] Ontology generation for different databases

## Notes

- SQLite doesn't need host/port/username/password
- Oracle requires either SID or Service Name
- MySQL uses database=schema concept
- PostgreSQL has schema within database
- Oracle has users=schemas concept

