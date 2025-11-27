# Multi-Database Testing Guide
**Date:** November 27, 2025

## Overview

This guide provides comprehensive instructions for testing DatabaseAI with **all supported database types**:
- ✅ **PostgreSQL** - World's most advanced open-source relational database
- ✅ **MySQL** - Most popular open-source relational database
- ✅ **Oracle** - Enterprise-grade commercial database
- ✅ **Neo4j** - Leading graph database
- ✅ **SQLite** - Embedded file-based database

## Quick Start - All Databases

### 1. Generate SQLite Sample Databases

```powershell
# Run from project root
python create_sqlite_samples.py
```

### 2. Start All Database Services

```powershell
# Start all databases + DatabaseAI application
docker compose -f docker-compose.all.yml up --build
```

This will start:
- PostgreSQL on port `5432`
- MySQL on port `3306`
- Oracle on port `1521`
- Neo4j on ports `7474` (HTTP) and `7687` (Bolt)
- DatabaseAI on port `80` (frontend) and `8000` (backend)
- SQLite databases mounted at `/app/sqlite-data/`

### 3. Access DatabaseAI

Open your browser: **http://localhost**

---

## Connection Details - All Databases

### 1. PostgreSQL

```yaml
Database Type: PostgreSQL
Host: postgres-db
Port: 5432
Database: testdb
Username: postgres
Password: postgres123
```

**From Host Machine (for external tools):**
```yaml
Host: localhost
Port: 5432
Database: testdb
Username: postgres
Password: postgres123
```

**Test Query:**
```sql
SELECT version();
SELECT current_database();
```

---

### 2. MySQL

```yaml
Database Type: MySQL
Host: mysql-db
Port: 3306
Database: testdb
Username: root
Password: mysql123
```

**From Host Machine:**
```yaml
Host: localhost
Port: 3306
Database: testdb
Username: root
Password: mysql123
```

**Test Query:**
```sql
SELECT VERSION();
SELECT DATABASE();
SHOW DATABASES;
```

---

### 3. Oracle

```yaml
Database Type: Oracle
Host: oracle-db
Port: 1521
Service Name: XEPDB1
Username: system
Password: oracle123
```

**From Host Machine:**
```yaml
Host: localhost
Port: 1521
Service Name: XEPDB1
Username: system
Password: oracle123
```

**Test Query:**
```sql
SELECT * FROM V$VERSION;
SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM DUAL;
```

**Note:** Oracle may take 2-3 minutes to fully start on first run.

---

### 4. Neo4j

```yaml
Database Type: Neo4j
URI: bolt://neo4j-db:7687
Username: neo4j
Password: neo4j123
Database: neo4j
```

**From Host Machine:**
```yaml
URI: bolt://localhost:7687
Username: neo4j
Password: neo4j123
```

**Web Interface:** http://localhost:7474

**Test Query (Cypher):**
```cypher
MATCH (n) RETURN count(n) AS node_count;
SHOW DATABASES;
```

---

### 5. SQLite

```yaml
Database Type: SQLite
Database File: /app/sqlite-data/test.db
```

**Available SQLite Databases:**
- `/app/sqlite-data/test.db` - Simple test database
- `/app/sqlite-data/employees.db` - Employee management
- `/app/sqlite-data/products.db` - E-commerce
- `/app/sqlite-data/university.db` - University system

**Test Query:**
```sql
SELECT sqlite_version();
SELECT * FROM sqlite_master WHERE type='table';
```

---

## Database-Specific Features

### PostgreSQL Features
- ✅ Advanced data types (JSON, JSONB, Arrays, UUID)
- ✅ Full-text search
- ✅ Window functions
- ✅ CTEs and recursive queries
- ✅ Materialized views
- ✅ Foreign data wrappers

**Sample Advanced Query:**
```sql
-- JSON query
SELECT info->>'name' AS name, info->>'age' AS age 
FROM users 
WHERE info->'address'->>'city' = 'New York';

-- Window function
SELECT 
    employee_name,
    salary,
    AVG(salary) OVER (PARTITION BY department) as avg_dept_salary
FROM employees;
```

### MySQL Features
- ✅ High performance for web applications
- ✅ Replication and clustering
- ✅ Full-text search (InnoDB)
- ✅ JSON data type
- ✅ Geographic data types (spatial)

**Sample Advanced Query:**
```sql
-- JSON query
SELECT 
    JSON_EXTRACT(data, '$.name') AS name,
    JSON_EXTRACT(data, '$.email') AS email
FROM users
WHERE JSON_EXTRACT(data, '$.active') = true;

-- Full-text search
SELECT * FROM articles
WHERE MATCH(title, body) AGAINST('database' IN NATURAL LANGUAGE MODE);
```

### Oracle Features
- ✅ Enterprise-grade reliability
- ✅ Advanced partitioning
- ✅ Flashback technology
- ✅ Real Application Clusters (RAC)
- ✅ Advanced security features

**Sample Advanced Query:**
```sql
-- Hierarchical query
SELECT LEVEL, employee_name, manager_id
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;

-- Flashback query (if enabled)
SELECT * FROM employees 
AS OF TIMESTAMP (SYSTIMESTAMP - INTERVAL '1' HOUR);
```

### Neo4j Features
- ✅ Native graph database
- ✅ Cypher query language
- ✅ Relationship-first design
- ✅ Pattern matching
- ✅ Shortest path algorithms

**Sample Graph Queries:**
```cypher
-- Create nodes and relationships
CREATE (p:Person {name: 'Alice', age: 30})
CREATE (c:Company {name: 'TechCorp'})
CREATE (p)-[:WORKS_AT {since: 2020}]->(c);

-- Pattern matching
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
RETURN p.name, c.name;

-- Shortest path
MATCH path = shortestPath(
  (p1:Person {name: 'Alice'})-[*]-(p2:Person {name: 'Bob'})
)
RETURN path;
```

### SQLite Features
- ✅ Zero configuration
- ✅ Single file database
- ✅ ACID transactions
- ✅ Full SQL support
- ✅ JSON extensions
- ✅ Common Table Expressions

**Sample Advanced Query:**
```sql
-- Recursive CTE
WITH RECURSIVE cnt(x) AS (
  SELECT 1
  UNION ALL
  SELECT x+1 FROM cnt WHERE x<10
)
SELECT x FROM cnt;

-- JSON query (if JSON1 extension enabled)
SELECT json_extract(data, '$.name') FROM users;
```

---

## Testing Scenarios

### Scenario 1: Basic Connectivity Test

Test each database connection:

1. **PostgreSQL**: `SELECT 1;`
2. **MySQL**: `SELECT 1;`
3. **Oracle**: `SELECT 1 FROM DUAL;`
4. **Neo4j**: `RETURN 1;`
5. **SQLite**: `SELECT 1;`

### Scenario 2: Schema Exploration

Ask DatabaseAI to show the schema:

- "Show me all tables"
- "What columns does the users table have?"
- "Show me all foreign key relationships"

### Scenario 3: Natural Language Queries

Test AI-powered query generation:

**For employees.db (SQLite):**
- "Show me all employees earning more than 70000"
- "Which department has the highest average salary?"
- "List all employees working on active projects"

**For Test Databases:**
- "Show me all users"
- "How many posts has each user written?"
- "What's the total revenue from all orders?"

### Scenario 4: Complex Joins

Test multi-table queries:

```sql
-- PostgreSQL/MySQL/SQLite
SELECT 
    u.username,
    COUNT(p.id) as post_count,
    SUM(CASE WHEN p.published = 1 THEN 1 ELSE 0 END) as published_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username
ORDER BY post_count DESC;
```

### Scenario 5: Aggregations and Analytics

Test analytical queries:

```sql
-- Sales analysis (products.db)
SELECT 
    DATE(o.order_date) as order_day,
    COUNT(DISTINCT o.order_id) as order_count,
    SUM(oi.quantity * oi.unit_price) as daily_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY DATE(o.order_date)
ORDER BY order_day DESC;
```

---

## Performance Testing

### PostgreSQL Performance Test

```sql
-- Explain query plan
EXPLAIN ANALYZE
SELECT * FROM employees WHERE department_id = 1;

-- Index creation
CREATE INDEX idx_employee_dept ON employees(department_id);
```

### MySQL Performance Test

```sql
-- Explain query plan
EXPLAIN
SELECT * FROM employees WHERE department_id = 1;

-- Index creation
CREATE INDEX idx_employee_dept ON employees(department_id);
```

### SQLite Performance Test

```sql
-- Explain query plan
EXPLAIN QUERY PLAN
SELECT * FROM employees WHERE department_id = 1;

-- Index creation
CREATE INDEX idx_employee_dept ON employees(department_id);
```

---

## Monitoring and Health Checks

### Check Container Status

```powershell
# Check all running containers
docker ps

# Check container logs
docker logs databaseai-app
docker logs postgres-db
docker logs mysql-db
docker logs oracle-db
docker logs neo4j-db
```

### Database Health Checks

All databases have health checks configured:

```yaml
# PostgreSQL
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]

# MySQL
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]

# Oracle
healthcheck:
  test: ["CMD", "healthcheck.sh"]

# Neo4j
healthcheck:
  test: ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:7474"]
```

---

## Troubleshooting

### Issue: Container fails to start

**Solution:**
```powershell
# Check logs
docker compose -f docker-compose.all.yml logs <service-name>

# Restart specific service
docker compose -f docker-compose.all.yml restart <service-name>

# Rebuild and restart
docker compose -f docker-compose.all.yml up --build --force-recreate
```

### Issue: "Connection refused"

**Solution:**
- Wait for health checks to pass (especially Oracle, takes 2-3 minutes)
- Check if ports are already in use: `netstat -ano | findstr :<port>`
- Verify you're using the correct hostname (`postgres-db`, not `localhost` from within the container)

### Issue: Oracle slow to start

**Solution:**
- Oracle XE requires significant initialization time on first run
- Monitor logs: `docker logs -f oracle-db`
- Wait for "DATABASE IS READY TO USE!" message

### Issue: Neo4j connection fails

**Solution:**
- Verify bolt port 7687 is accessible
- Check Neo4j web interface: http://localhost:7474
- Ensure credentials are correct: `neo4j / neo4j123`

### Issue: SQLite "database is locked"

**Solution:**
- SQLite locks the database file during writes
- Close other connections to the same database file
- Restart the container if lock persists

---

## Docker Compose Commands Cheat Sheet

```powershell
# Start all services
docker compose -f docker-compose.all.yml up -d

# Start with rebuild
docker compose -f docker-compose.all.yml up --build

# Stop all services
docker compose -f docker-compose.all.yml down

# Stop and remove volumes (WARNING: Deletes data!)
docker compose -f docker-compose.all.yml down -v

# View logs for all services
docker compose -f docker-compose.all.yml logs -f

# View logs for specific service
docker compose -f docker-compose.all.yml logs -f databaseai

# Restart specific service
docker compose -f docker-compose.all.yml restart postgres-db

# Check service status
docker compose -f docker-compose.all.yml ps

# Execute command in running container
docker compose -f docker-compose.all.yml exec databaseai bash
```

---

## Data Persistence

All databases use Docker volumes for data persistence:

```yaml
volumes:
  postgres-data:    # PostgreSQL data
  mysql-data:       # MySQL data
  oracle-data:      # Oracle data
  neo4j-data:       # Neo4j graph data
  neo4j-logs:       # Neo4j logs
  neo4j-import:     # Neo4j import directory
  neo4j-plugins:    # Neo4j plugins
```

**SQLite** uses bind mount: `./sqlite-data:/app/sqlite-data`

To reset a database:
```powershell
# Stop services
docker compose -f docker-compose.all.yml down

# Remove specific volume
docker volume rm databaseai_postgres-data

# Start services (will recreate fresh database)
docker compose -f docker-compose.all.yml up -d
```

---

## Network Configuration

All services run on the same Docker network:

```yaml
networks:
  databaseai-network:
    driver: bridge
```

**Service-to-Service Communication:**
- Use service names as hostnames: `postgres-db`, `mysql-db`, `oracle-db`, `neo4j-db`
- Ports are accessible between services without port mapping

**External Access (from host):**
- Use `localhost` with mapped ports
- PostgreSQL: `localhost:5432`
- MySQL: `localhost:3306`
- Oracle: `localhost:1521`
- Neo4j HTTP: `localhost:7474`
- Neo4j Bolt: `localhost:7687`
- DatabaseAI: `localhost:80`

---

## Best Practices

### 1. Connection Management
- ✅ Always test connections before running queries
- ✅ Use connection pooling for production
- ✅ Close connections when done
- ✅ Use descriptive connection names

### 2. Query Optimization
- ✅ Use EXPLAIN/EXPLAIN ANALYZE to understand query plans
- ✅ Create indexes on frequently queried columns
- ✅ Avoid SELECT * in production queries
- ✅ Use appropriate data types

### 3. Security
- ✅ Change default passwords in production
- ✅ Use environment variables for sensitive data
- ✅ Never commit `app_config.yml` with real credentials
- ✅ Limit database user permissions
- ✅ Use SSL/TLS for remote connections

### 4. Backup and Recovery
- ✅ Regular backups of Docker volumes
- ✅ Export important data periodically
- ✅ Test restore procedures
- ✅ Keep SQLite files in version control (for test data only)

### 5. Development Workflow
- ✅ Use SQLite for quick local testing
- ✅ Test with PostgreSQL/MySQL for production parity
- ✅ Use Neo4j for relationship-heavy data
- ✅ Keep sample data realistic and representative

---

## Sample Data Summary

### SQLite Databases (./sqlite-data/)

| Database | Tables | Records | Use Case |
|----------|--------|---------|----------|
| test.db | 2 | 7 | Simple testing |
| employees.db | 4 | 29 | HR management |
| products.db | 5 | 37 | E-commerce |
| university.db | 5 | 24 | Education |

### PostgreSQL/MySQL/Oracle

Use the same SQLite sample data by:
1. Exporting SQLite to SQL: `sqlite3 test.db .dump > test.sql`
2. Importing to target database
3. Or use init scripts in `init-postgres/`, `init-mysql/`, `init-oracle/`

---

## Advanced Topics

### Using Neo4j with Relational Data

Create a knowledge graph from relational data:

```cypher
-- Import employees as nodes
CREATE (e:Employee {
    id: 1,
    name: 'John Doe',
    department: 'Engineering'
});

-- Create relationships
MATCH (e1:Employee {id: 1}), (e2:Employee {id: 2})
CREATE (e1)-[:REPORTS_TO]->(e2);

-- Query the graph
MATCH (e:Employee)-[:REPORTS_TO*1..3]->(manager)
RETURN e.name, manager.name;
```

### Multi-Database Queries (Future Feature)

DatabaseAI can potentially federate queries across multiple databases:

```sql
-- Conceptual example (not yet implemented)
SELECT 
    pg.user_id,
    neo4j.recommendations
FROM postgres.users pg
JOIN neo4j.user_interests neo4j ON pg.user_id = neo4j.user_id;
```

---

## Summary

✅ **5 Database Types** - PostgreSQL, MySQL, Oracle, Neo4j, SQLite  
✅ **Pre-configured** - Ready to use with docker-compose  
✅ **Sample Data** - Realistic test databases included  
✅ **Health Checks** - Automatic service health monitoring  
✅ **Persistent Storage** - Data survives container restarts  
✅ **Network Isolated** - Secure internal communication  

---

## Quick Reference Card

| Database | Host (Container) | Port | User | Password | Database/Service |
|----------|------------------|------|------|----------|------------------|
| PostgreSQL | postgres-db | 5432 | postgres | postgres123 | testdb |
| MySQL | mysql-db | 3306 | root | mysql123 | testdb |
| Oracle | oracle-db | 1521 | system | oracle123 | XEPDB1 |
| Neo4j | neo4j-db | 7687 | neo4j | neo4j123 | neo4j |
| SQLite | N/A | N/A | N/A | N/A | /app/sqlite-data/*.db |

---

**For detailed SQLite testing, see:** `SQLITE_TESTING_GUIDE.md`  
**For Oracle schema filtering, see:** `ORACLE_SCHEMA_FIX_SUMMARY.md`  
**For Docker build issues, see:** `GIT_HISTORY_CLEANUP_SUMMARY.md`

**Next Steps:**
1. `docker compose -f docker-compose.all.yml up --build`
2. Open http://localhost
3. Start testing with natural language queries!
