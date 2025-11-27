# SQLite Sample Databases

This directory contains sample SQLite databases for testing DatabaseAI.

## Available Databases

### 1. test.db
- **Tables**: users (3), posts (4)
- **Description**: Simple test database for quick testing
- **Use Case**: Basic SQL queries, joins

### 2. employees.db
- **Tables**: departments (5), employees (10), projects (5), employee_projects (9)
- **Description**: Employee management system with departments and projects
- **Use Case**: HR queries, organizational structure, project management

### 3. products.db
- **Tables**: categories (7), products (10), customers (5), orders (6), order_items (10)
- **Description**: E-commerce database with products, orders, and customers
- **Use Case**: Sales analysis, inventory management, customer orders

### 4. university.db
- **Tables**: students (5), courses (6), professors (5), enrollments (8), course_sections (6)
- **Description**: University management system with students, courses, and enrollments
- **Use Case**: Academic queries, student performance, course management

## Regenerating Databases

To regenerate all sample databases:

```powershell
python create_sqlite_samples.py
```

This will recreate all 4 databases with fresh sample data.

## Using in DatabaseAI

When connecting from the DatabaseAI web interface:

```
Database Type: SQLite
Database File: /app/sqlite-data/test.db
```

Replace `test.db` with any of the available databases.

## Adding Your Own Databases

Simply copy your SQLite database files into this directory:

```powershell
Copy-Item "C:\path\to\your\database.db" -Destination ".\sqlite-data\"
```

Then connect using: `/app/sqlite-data/database.db`

---

For detailed testing instructions, see `SQLITE_TESTING_GUIDE.md` in the project root.
