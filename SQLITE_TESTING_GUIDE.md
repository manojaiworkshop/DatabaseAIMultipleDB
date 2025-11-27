# SQLite Database Testing Guide
**Date:** November 27, 2025

## Overview

This guide explains how to test SQLite databases with DatabaseAI. SQLite is a file-based database that doesn't require a separate server process, making it perfect for development, testing, and embedded applications.

## Quick Start

### 1. Generate Sample Databases

```powershell
# Run from the project root directory
python create_sqlite_samples.py
```

This creates 4 sample databases in `./sqlite-data/`:
- **test.db** - Simple test database (users & posts)
- **employees.db** - Employee management (10 employees, 5 projects)
- **products.db** - E-commerce (10 products, 6 orders)
- **university.db** - University system (5 students, 6 courses)

### 2. Start All Database Services

```powershell
# Start all databases (PostgreSQL, MySQL, Oracle, Neo4j) + DatabaseAI
docker compose -f docker-compose.all.yml up --build
```

The SQLite databases are automatically mounted at `/app/sqlite-data/` inside the container.

### 3. Connect to SQLite from DatabaseAI UI

1. Open your browser: http://localhost
2. Click **"New Connection"**
3. Fill in the connection details:
   - **Database Type**: SQLite
   - **Database File**: `/app/sqlite-data/test.db`
   - **Connection Name**: Test SQLite DB

4. Click **"Test Connection"** then **"Save"**

## Sample Database Details

### 1. test.db - Simple Test Database

**Tables:**
- `users` - User accounts (3 records)
- `posts` - Blog posts (4 records)

**Sample Queries:**
```sql
-- Get all users
SELECT * FROM users;

-- Get published posts with user info
SELECT u.username, p.title, p.content, p.created_at
FROM posts p
JOIN users u ON p.user_id = u.id
WHERE p.published = 1;

-- Count posts per user
SELECT u.username, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.username;
```

### 2. employees.db - Employee Management

**Tables:**
- `departments` - Company departments (5 records)
- `employees` - Employee records (10 records)
- `projects` - Active projects (5 records)
- `employee_projects` - Employee-project assignments (9 records)

**Sample Queries:**
```sql
-- Get all employees with their departments
SELECT e.first_name, e.last_name, e.email, e.salary, d.department_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
ORDER BY e.salary DESC;

-- Find employees working on active projects
SELECT DISTINCT e.first_name, e.last_name, p.project_name, ep.role
FROM employees e
JOIN employee_projects ep ON e.employee_id = ep.employee_id
JOIN projects p ON ep.project_id = p.project_id
WHERE p.status = 'Active';

-- Department budget vs employee costs
SELECT 
    d.department_name,
    d.budget,
    SUM(e.salary) as total_salaries,
    d.budget - SUM(e.salary) as remaining_budget
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
GROUP BY d.department_id;
```

### 3. products.db - E-Commerce

**Tables:**
- `categories` - Product categories (7 records, hierarchical)
- `products` - Product catalog (10 records)
- `customers` - Customer accounts (5 records)
- `orders` - Customer orders (6 records)
- `order_items` - Order line items (10 records)

**Sample Queries:**
```sql
-- Get products with categories
SELECT p.product_name, p.price, p.stock_quantity, c.category_name
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
WHERE p.is_active = 1;

-- Get customer order history
SELECT 
    c.first_name || ' ' || c.last_name as customer_name,
    o.order_date,
    o.status,
    o.total_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
ORDER BY o.order_date DESC;

-- Top selling products
SELECT 
    p.product_name,
    SUM(oi.quantity) as total_sold,
    SUM(oi.quantity * oi.unit_price) as total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id
ORDER BY total_sold DESC;

-- Low stock alert
SELECT product_name, stock_quantity, reorder_level
FROM products
WHERE stock_quantity <= reorder_level
ORDER BY stock_quantity ASC;
```

### 4. university.db - University System

**Tables:**
- `students` - Student records (5 records)
- `courses` - Course catalog (6 records)
- `professors` - Faculty members (5 records)
- `enrollments` - Student course enrollments (8 records)
- `course_sections` - Course sections with professors (6 records)

**Sample Queries:**
```sql
-- Get student enrollment details
SELECT 
    s.first_name || ' ' || s.last_name as student_name,
    c.course_code,
    c.course_name,
    e.semester,
    e.year,
    e.grade
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
ORDER BY s.last_name, c.course_code;

-- Find professors teaching Computer Science courses
SELECT DISTINCT
    p.first_name || ' ' || p.last_name as professor_name,
    c.course_code,
    c.course_name,
    cs.semester,
    cs.year
FROM professors p
JOIN course_sections cs ON p.professor_id = cs.professor_id
JOIN courses c ON cs.course_id = c.course_id
WHERE c.department = 'Computer Science';

-- Students with highest GPAs
SELECT 
    first_name || ' ' || last_name as student_name,
    major,
    gpa,
    credits_completed
FROM students
ORDER BY gpa DESC
LIMIT 5;

-- Course capacity analysis
SELECT 
    c.course_code,
    c.course_name,
    cs.capacity,
    cs.enrolled_count,
    cs.capacity - cs.enrolled_count as available_seats,
    ROUND((cs.enrolled_count * 100.0 / cs.capacity), 2) as fill_percentage
FROM course_sections cs
JOIN courses c ON cs.course_id = c.course_id
ORDER BY fill_percentage DESC;
```

## Connection Details

### From Host Machine (Windows)

When testing locally (not in Docker):
```
Database Type: SQLite
Database File: C:\Users\SAP-WORKSTATION\Documents\DatabaseAI\DatabaseAIMulitiple\DatabaseAI\sqlite-data\test.db
```

### From Docker Container

When DatabaseAI is running in Docker:
```
Database Type: SQLite
Database File: /app/sqlite-data/test.db
```

**Important:** Always use the container path (`/app/sqlite-data/`) when connecting from the DatabaseAI web interface!

## File Structure

```
DatabaseAI/
├── sqlite-data/                    # SQLite database files directory
│   ├── README.md                   # Directory documentation
│   ├── test.db                     # Simple test database
│   ├── employees.db                # Employee management database
│   ├── products.db                 # E-commerce database
│   └── university.db               # University system database
├── create_sqlite_samples.py        # Database generator script
└── docker-compose.all.yml          # Docker compose with SQLite mount
```

## Docker Volume Mounting

The SQLite data directory is mounted in `docker-compose.all.yml`:

```yaml
databaseai:
  volumes:
    # SQLite data directory (for file-based SQLite databases)
    - ./sqlite-data:/app/sqlite-data
```

This means:
- **Host path**: `./sqlite-data/` (your local directory)
- **Container path**: `/app/sqlite-data/` (inside the container)

## Using Your Own SQLite Databases

### Option 1: Copy to sqlite-data Directory

```powershell
# Copy your SQLite database
Copy-Item "C:\path\to\your\database.db" -Destination ".\sqlite-data\"
```

Then connect using: `/app/sqlite-data/database.db`

### Option 2: Mount Additional Directory

Edit `docker-compose.all.yml` and add another volume:

```yaml
databaseai:
  volumes:
    - ./sqlite-data:/app/sqlite-data
    - C:/path/to/your/databases:/app/custom-db:ro  # Add this line
```

Then connect using: `/app/custom-db/database.db`

## Testing Natural Language Queries

Once connected, you can test DatabaseAI's AI capabilities with natural language:

**Examples for employees.db:**
- "Show me all employees in the Engineering department"
- "Who is the highest paid employee?"
- "List all active projects with their assigned employees"
- "What's the average salary by department?"

**Examples for products.db:**
- "Show me products that are low in stock"
- "Which customers have placed the most orders?"
- "What are the top 5 best-selling products?"
- "Show me all pending orders"

**Examples for university.db:**
- "Which students have a GPA above 3.5?"
- "Show me all courses taught by Dr. Williams"
- "List students enrolled in Computer Science courses"
- "Which courses have the most available seats?"

## SQLite Features Supported

DatabaseAI supports all standard SQLite features:
- ✅ Tables, indexes, views
- ✅ Foreign key relationships
- ✅ Transactions
- ✅ Full-text search (FTS)
- ✅ JSON extensions
- ✅ Window functions
- ✅ Common Table Expressions (CTEs)
- ✅ Recursive queries

## Troubleshooting

### Issue: "Unable to open database file"

**Solution:** Ensure you're using the container path:
- ❌ Wrong: `./sqlite-data/test.db`
- ❌ Wrong: `C:\Users\...\sqlite-data\test.db`
- ✅ Correct: `/app/sqlite-data/test.db`

### Issue: "Database is locked"

**Solution:** SQLite locks the database file when writing. Ensure:
- Only one connection is writing at a time
- Close connections when done
- Restart the container if the lock persists

### Issue: "No such table"

**Solution:** 
- Regenerate databases: `python create_sqlite_samples.py`
- Check the database file path is correct
- Verify the database file exists in `./sqlite-data/`

### Issue: Changes not reflected

**Solution:**
- SQLite databases are file-based and changes persist immediately
- Refresh your query results
- Check you're connected to the correct database file

## Creating New Sample Databases

To add your own sample databases, edit `create_sqlite_samples.py` and add a new function:

```python
def create_my_database():
    """Create my custom database"""
    db_path = 'sqlite-data/mydb.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS my_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value INTEGER
        )
    ''')
    
    # Insert data
    data = [('Item1', 100), ('Item2', 200)]
    cursor.executemany(
        'INSERT INTO my_table (name, value) VALUES (?, ?)',
        data
    )
    
    conn.commit()
    conn.close()
    print(f'✓ Created mydb.db')

# Add to main():
def main():
    # ... existing code ...
    create_my_database()  # Add this line
```

Then run: `python create_sqlite_samples.py`

## Best Practices

1. **Use descriptive database names**: `employees.db` instead of `db1.db`
2. **Keep databases small**: SQLite works best with databases under 1GB
3. **Use read-only mode** for reference databases: Add `:ro` to volume mount
4. **Backup regularly**: Copy `.db` files to backup location
5. **Use WAL mode** for better concurrency (DatabaseAI does this automatically)
6. **Index frequently queried columns** for better performance

## Advanced: Creating Read-Only Databases

To prevent accidental modifications, mount databases as read-only:

```yaml
databaseai:
  volumes:
    - ./sqlite-data:/app/sqlite-data:ro  # Read-only mount
```

Or open the connection in read-only mode from the backend (modify SQLite adapter).

## Summary

✅ **4 sample databases created** with realistic data  
✅ **Mounted at** `/app/sqlite-data/` in the container  
✅ **Ready to test** with natural language queries  
✅ **Easy to extend** with your own databases  

---

**Next Steps:**
1. Start the services: `docker compose -f docker-compose.all.yml up --build`
2. Open: http://localhost
3. Connect to: `/app/sqlite-data/test.db`
4. Try natural language queries!

For testing all databases (PostgreSQL, MySQL, Oracle, Neo4j, SQLite), see `MULTI_DATABASE_TESTING_GUIDE.md`.
