# Library Management System

A complete full-stack Library Management System built with HTML, CSS, JavaScript, Flask, and MySQL.

## Features

- Admin and student login
- Admin book CRUD
- Searchable book cards
- Issue and return system
- Fine calculation at `₹5` per overdue day
- Reports for issued, returned, and overdue books
- Responsive animated UI with a custom book logo

## Folder Structure

```text
backend/
  app.py
  db.py
templates/
  login.html
  admin_dashboard.html
  student_dashboard.html
static/
  css/styles.css
  js/app.js
database/
  schema.sql
requirements.txt
README.md
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup MySQL

Login to MySQL and run the schema:

```bash
mysql -u root -p < database/schema.sql
```

The schema creates the `library_management` database, tables, Indian-style users, and generic books.

For an existing database, add forgot-password support:

```powershell
Get-Content .\database\add_forgot_password.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

### 4. Configure database credentials

Set environment variables if your MySQL credentials are different from the defaults.

Windows PowerShell:

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DB="library_management"
```

Configure SMTP for forgot-password emails:

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="your_email@gmail.com"
$env:SMTP_PASSWORD="your_app_password"
$env:SMTP_FROM="your_email@gmail.com"
```

For Gmail, use an app password, not your normal account password.

macOS/Linux:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=library_management
```

### 5. Run the Flask app

```bash
python backend/app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demo Logins

Admin:

```text
Username: Chandu
Password: chandu123
Role: Admin
```

Students:

```text
Username: Ratna
Password: ratna123
Role: Student

Username: Pannu
Password: pannu123
Role: Student

Username: Karuna
Password: karuna123
Role: Student

Username: Satya
Password: satya123
Role: Student
```

## Notes

- This project uses MySQL only.
- This project does not use React, Node.js, SQLite, or frontend frameworks.
- Book names are generic and user names are Indian-style as required.
