#!/usr/bin/env python3
"""
SQLite Sample Database Generator
Creates multiple sample SQLite databases for testing DatabaseAI
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

# Create sqlite-data directory if it doesn't exist
os.makedirs('sqlite-data', exist_ok=True)

def create_employees_database():
    """Create a sample employee management database"""
    db_path = 'sqlite-data/employees.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL,
            location TEXT,
            budget REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            hire_date DATE,
            salary REAL,
            department_id INTEGER,
            manager_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (department_id) REFERENCES departments(department_id),
            FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            description TEXT,
            start_date DATE,
            end_date DATE,
            budget REAL,
            department_id INTEGER,
            status TEXT CHECK(status IN ('Planning', 'Active', 'Completed', 'On Hold')),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_projects (
            employee_id INTEGER,
            project_id INTEGER,
            role TEXT,
            hours_allocated REAL,
            PRIMARY KEY (employee_id, project_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    ''')
    
    # Insert sample data
    departments = [
        ('Engineering', 'Building A', 500000),
        ('Sales', 'Building B', 300000),
        ('Marketing', 'Building C', 250000),
        ('Human Resources', 'Building A', 150000),
        ('Finance', 'Building D', 200000)
    ]
    
    cursor.executemany(
        'INSERT INTO departments (department_name, location, budget) VALUES (?, ?, ?)',
        departments
    )
    
    employees = [
        ('John', 'Doe', 'john.doe@company.com', '555-0101', '2020-01-15', 85000, 1, None),
        ('Jane', 'Smith', 'jane.smith@company.com', '555-0102', '2019-03-20', 95000, 1, 1),
        ('Mike', 'Johnson', 'mike.johnson@company.com', '555-0103', '2021-06-10', 75000, 2, None),
        ('Sarah', 'Williams', 'sarah.williams@company.com', '555-0104', '2020-09-05', 70000, 2, 3),
        ('David', 'Brown', 'david.brown@company.com', '555-0105', '2022-01-12', 65000, 3, None),
        ('Emily', 'Davis', 'emily.davis@company.com', '555-0106', '2021-11-18', 72000, 3, 5),
        ('Robert', 'Miller', 'robert.miller@company.com', '555-0107', '2019-07-22', 68000, 4, None),
        ('Lisa', 'Wilson', 'lisa.wilson@company.com', '555-0108', '2020-04-30', 78000, 5, None),
        ('Tom', 'Anderson', 'tom.anderson@company.com', '555-0109', '2022-03-15', 62000, 1, 2),
        ('Amy', 'Taylor', 'amy.taylor@company.com', '555-0110', '2021-08-20', 69000, 2, 3)
    ]
    
    cursor.executemany(
        '''INSERT INTO employees (first_name, last_name, email, phone, hire_date, 
           salary, department_id, manager_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        employees
    )
    
    projects = [
        ('Website Redesign', 'Complete overhaul of company website', '2024-01-01', '2024-06-30', 100000, 1, 'Active'),
        ('Sales CRM Implementation', 'New CRM system rollout', '2024-02-15', '2024-09-30', 150000, 2, 'Active'),
        ('Marketing Campaign Q1', 'Social media marketing campaign', '2024-01-01', '2024-03-31', 50000, 3, 'Completed'),
        ('HR Portal Upgrade', 'Employee self-service portal', '2024-03-01', '2024-08-31', 75000, 4, 'Planning'),
        ('Financial System Migration', 'Move to cloud-based accounting', '2024-04-01', '2024-12-31', 200000, 5, 'Active')
    ]
    
    cursor.executemany(
        '''INSERT INTO projects (project_name, description, start_date, end_date, 
           budget, department_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)''',
        projects
    )
    
    # Assign employees to projects
    assignments = [
        (1, 1, 'Lead Developer', 40),
        (2, 1, 'Senior Developer', 35),
        (9, 1, 'Junior Developer', 30),
        (3, 2, 'Project Manager', 20),
        (4, 2, 'Sales Analyst', 30),
        (5, 3, 'Marketing Manager', 25),
        (6, 3, 'Content Creator', 35),
        (7, 4, 'HR Lead', 15),
        (8, 5, 'Finance Manager', 20)
    ]
    
    cursor.executemany(
        'INSERT INTO employee_projects (employee_id, project_id, role, hours_allocated) VALUES (?, ?, ?, ?)',
        assignments
    )
    
    conn.commit()
    conn.close()
    print(f'✓ Created employees.db with {len(employees)} employees and {len(projects)} projects')


def create_products_database():
    """Create a sample e-commerce products database"""
    db_path = 'sqlite-data/products.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE,
            description TEXT,
            parent_category_id INTEGER,
            FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            description TEXT,
            sku TEXT UNIQUE,
            category_id INTEGER,
            price REAL NOT NULL,
            cost REAL,
            stock_quantity INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 10,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            city TEXT,
            country TEXT,
            registration_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled')),
            total_amount REAL,
            shipping_address TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount REAL DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')
    
    # Insert sample data
    categories = [
        ('Electronics', 'Electronic devices and accessories', None),
        ('Laptops', 'Portable computers', 1),
        ('Smartphones', 'Mobile phones', 1),
        ('Accessories', 'Electronic accessories', 1),
        ('Clothing', 'Apparel and fashion', None),
        ('Books', 'Books and literature', None),
        ('Home & Garden', 'Home improvement and garden supplies', None)
    ]
    
    cursor.executemany(
        'INSERT INTO categories (category_name, description, parent_category_id) VALUES (?, ?, ?)',
        categories
    )
    
    products = [
        ('Dell XPS 15 Laptop', '15-inch premium laptop', 'DELL-XPS15', 2, 1299.99, 950.00, 45, 10),
        ('MacBook Pro 14"', 'Apple MacBook Pro', 'MBP-14-2024', 2, 1999.99, 1500.00, 30, 5),
        ('iPhone 15 Pro', 'Latest iPhone model', 'IP15-PRO', 3, 999.99, 700.00, 120, 20),
        ('Samsung Galaxy S24', 'Samsung flagship phone', 'SGS24', 3, 899.99, 650.00, 85, 15),
        ('Wireless Mouse', 'Ergonomic wireless mouse', 'WM-001', 4, 29.99, 12.00, 200, 50),
        ('USB-C Hub', '7-in-1 USB-C adapter', 'USBC-HUB', 4, 49.99, 20.00, 150, 30),
        ('Cotton T-Shirt', 'Comfortable cotton t-shirt', 'TSHIRT-001', 5, 19.99, 8.00, 500, 100),
        ('Jeans', 'Classic blue jeans', 'JEANS-001', 5, 49.99, 20.00, 300, 50),
        ('Python Programming', 'Learn Python book', 'BOOK-PY', 6, 39.99, 15.00, 75, 20),
        ('Garden Tools Set', '5-piece garden tool set', 'GARDEN-001', 7, 79.99, 35.00, 40, 10)
    ]
    
    cursor.executemany(
        '''INSERT INTO products (product_name, description, sku, category_id, price, 
           cost, stock_quantity, reorder_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        products
    )
    
    customers = [
        ('Alice', 'Cooper', 'alice.cooper@email.com', '555-1001', '123 Main St', 'New York', 'USA'),
        ('Bob', 'Dylan', 'bob.dylan@email.com', '555-1002', '456 Oak Ave', 'Los Angeles', 'USA'),
        ('Carol', 'King', 'carol.king@email.com', '555-1003', '789 Pine Rd', 'Chicago', 'USA'),
        ('David', 'Bowie', 'david.bowie@email.com', '555-1004', '321 Elm St', 'Houston', 'USA'),
        ('Emma', 'Stone', 'emma.stone@email.com', '555-1005', '654 Maple Dr', 'Phoenix', 'USA')
    ]
    
    cursor.executemany(
        '''INSERT INTO customers (first_name, last_name, email, phone, address, city, country) 
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        customers
    )
    
    orders = [
        (1, '2024-11-01 10:30:00', 'Delivered', 1329.98, '123 Main St, New York, USA'),
        (2, '2024-11-05 14:20:00', 'Shipped', 999.99, '456 Oak Ave, Los Angeles, USA'),
        (1, '2024-11-10 09:15:00', 'Processing', 79.98, '123 Main St, New York, USA'),
        (3, '2024-11-15 16:45:00', 'Pending', 899.99, '789 Pine Rd, Chicago, USA'),
        (4, '2024-11-20 11:30:00', 'Delivered', 149.97, '321 Elm St, Houston, USA'),
        (5, '2024-11-25 13:00:00', 'Processing', 69.98, '654 Maple Dr, Phoenix, USA')
    ]
    
    cursor.executemany(
        'INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address) VALUES (?, ?, ?, ?, ?)',
        orders
    )
    
    order_items = [
        (1, 1, 1, 1299.99, 0),
        (1, 5, 1, 29.99, 0),
        (2, 3, 1, 999.99, 0),
        (3, 5, 2, 29.99, 5),
        (3, 6, 1, 49.99, 0),
        (4, 4, 1, 899.99, 0),
        (5, 6, 1, 49.99, 0),
        (5, 7, 5, 19.99, 0),
        (6, 7, 2, 19.99, 10),
        (6, 9, 1, 39.99, 0)
    ]
    
    cursor.executemany(
        'INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount) VALUES (?, ?, ?, ?, ?)',
        order_items
    )
    
    conn.commit()
    conn.close()
    print(f'✓ Created products.db with {len(products)} products and {len(orders)} orders')


def create_university_database():
    """Create a sample university database"""
    db_path = 'sqlite-data/university.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            enrollment_date DATE,
            major TEXT,
            gpa REAL CHECK(gpa >= 0 AND gpa <= 4.0),
            credits_completed INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            credits INTEGER,
            department TEXT,
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            semester TEXT,
            year INTEGER,
            grade TEXT CHECK(grade IN ('A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', 'W', 'IP')),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id),
            UNIQUE(student_id, course_id, semester, year)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS professors (
            professor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT,
            hire_date DATE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_sections (
            section_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            semester TEXT,
            year INTEGER,
            room TEXT,
            capacity INTEGER,
            enrolled_count INTEGER DEFAULT 0,
            FOREIGN KEY (course_id) REFERENCES courses(course_id),
            FOREIGN KEY (professor_id) REFERENCES professors(professor_id)
        )
    ''')
    
    # Insert sample data
    students = [
        ('Alex', 'Johnson', 'alex.j@university.edu', '2022-09-01', 'Computer Science', 3.8, 60),
        ('Maria', 'Garcia', 'maria.g@university.edu', '2022-09-01', 'Computer Science', 3.6, 58),
        ('James', 'Lee', 'james.l@university.edu', '2023-01-15', 'Business', 3.4, 32),
        ('Sophie', 'Chen', 'sophie.c@university.edu', '2021-09-01', 'Mathematics', 3.9, 90),
        ('Daniel', 'Kim', 'daniel.k@university.edu', '2023-09-01', 'Engineering', 3.5, 28)
    ]
    
    cursor.executemany(
        'INSERT INTO students (first_name, last_name, email, enrollment_date, major, gpa, credits_completed) VALUES (?, ?, ?, ?, ?, ?, ?)',
        students
    )
    
    courses = [
        ('CS101', 'Introduction to Programming', 3, 'Computer Science', 'Basic programming concepts'),
        ('CS201', 'Data Structures', 3, 'Computer Science', 'Advanced data structures'),
        ('CS301', 'Database Systems', 3, 'Computer Science', 'Relational database design'),
        ('MATH201', 'Calculus I', 4, 'Mathematics', 'Differential calculus'),
        ('BUS101', 'Introduction to Business', 3, 'Business', 'Business fundamentals'),
        ('ENG201', 'Engineering Mechanics', 3, 'Engineering', 'Statics and dynamics')
    ]
    
    cursor.executemany(
        'INSERT INTO courses (course_code, course_name, credits, department, description) VALUES (?, ?, ?, ?, ?)',
        courses
    )
    
    professors = [
        ('Dr. Sarah', 'Williams', 'sarah.w@university.edu', 'Computer Science', '2015-08-15'),
        ('Dr. Michael', 'Brown', 'michael.b@university.edu', 'Computer Science', '2018-01-10'),
        ('Prof. Linda', 'Davis', 'linda.d@university.edu', 'Mathematics', '2012-09-01'),
        ('Dr. Robert', 'Wilson', 'robert.w@university.edu', 'Business', '2017-06-20'),
        ('Prof. Jennifer', 'Taylor', 'jennifer.t@university.edu', 'Engineering', '2014-03-15')
    ]
    
    cursor.executemany(
        'INSERT INTO professors (first_name, last_name, email, department, hire_date) VALUES (?, ?, ?, ?, ?)',
        professors
    )
    
    enrollments = [
        (1, 1, 'Fall', 2024, 'A'),
        (1, 2, 'Fall', 2024, 'A-'),
        (2, 1, 'Fall', 2024, 'B+'),
        (2, 2, 'Fall', 2024, 'B'),
        (3, 5, 'Fall', 2024, 'A'),
        (4, 1, 'Fall', 2024, 'A'),
        (4, 4, 'Fall', 2024, 'A'),
        (5, 6, 'Fall', 2024, 'B+')
    ]
    
    cursor.executemany(
        'INSERT INTO enrollments (student_id, course_id, semester, year, grade) VALUES (?, ?, ?, ?, ?)',
        enrollments
    )
    
    sections = [
        (1, 1, 'Fall', 2024, 'A-101', 30, 25),
        (2, 2, 'Fall', 2024, 'A-102', 25, 20),
        (3, 2, 'Fall', 2024, 'A-103', 30, 22),
        (4, 3, 'Fall', 2024, 'B-201', 35, 28),
        (5, 4, 'Fall', 2024, 'C-101', 25, 18),
        (6, 5, 'Fall', 2024, 'D-101', 30, 24)
    ]
    
    cursor.executemany(
        'INSERT INTO course_sections (course_id, professor_id, semester, year, room, capacity, enrolled_count) VALUES (?, ?, ?, ?, ?, ?, ?)',
        sections
    )
    
    conn.commit()
    conn.close()
    print(f'✓ Created university.db with {len(students)} students and {len(courses)} courses')


def create_simple_test_database():
    """Create a simple test database for quick testing"""
    db_path = 'sqlite-data/test.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            published BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    users = [
        ('admin', 'admin@test.com'),
        ('john_doe', 'john@test.com'),
        ('jane_smith', 'jane@test.com')
    ]
    
    cursor.executemany(
        'INSERT INTO users (username, email) VALUES (?, ?)',
        users
    )
    
    posts = [
        (1, 'First Post', 'This is my first post!', 1),
        (1, 'Second Post', 'Another interesting post', 1),
        (2, 'Hello World', 'My introduction post', 1),
        (3, 'Draft Post', 'This is still a draft', 0)
    ]
    
    cursor.executemany(
        'INSERT INTO posts (user_id, title, content, published) VALUES (?, ?, ?, ?)',
        posts
    )
    
    conn.commit()
    conn.close()
    print(f'✓ Created test.db with {len(users)} users and {len(posts)} posts')


def main():
    print('\n' + '='*60)
    print('  SQLite Sample Database Generator for DatabaseAI')
    print('='*60 + '\n')
    
    try:
        create_simple_test_database()
        create_employees_database()
        create_products_database()
        create_university_database()
        
        print('\n' + '='*60)
        print('  ✓ All SQLite databases created successfully!')
        print('='*60)
        print('\nCreated databases in ./sqlite-data/:')
        print('  1. test.db          - Simple test database (users & posts)')
        print('  2. employees.db     - Employee management (10 employees, 5 projects)')
        print('  3. products.db      - E-commerce (10 products, 6 orders)')
        print('  4. university.db    - University system (5 students, 6 courses)')
        print('\n' + '='*60)
        print('  How to connect from DatabaseAI:')
        print('='*60)
        print('  Database Type: SQLite')
        print('  Database File: /app/sqlite-data/test.db')
        print('  (or employees.db, products.db, university.db)')
        print('\n  Note: Use absolute path within container: /app/sqlite-data/<filename>')
        print('='*60 + '\n')
        
    except Exception as e:
        print(f'\n✗ Error creating databases: {e}')
        raise


if __name__ == '__main__':
    main()
