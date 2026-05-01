# Library Management System

A complete full-stack Library Management System built with HTML, CSS, JavaScript, Flask, and MySQL.

## Features

- Admin and student login
- Admin-only student account creation
- Admin book CRUD
- Searchable book cards
- Issue and return system
- Existing student catalog, self-issue, return, and dashboard workflows remain available
- Forgot-password flow with email reset code
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

On Railway, add the same SMTP variables in the service variables. Without these values, password reset requests cannot send email.

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

## Deployment Flow

Recommended workflow:

```text
Make changes locally
Run and test locally
Commit changes
Push to GitHub
Railway auto-deploys the connected branch
Verify the live Railway URL
```

Commands:

```bash
git status
git add .
git commit -m "Add admin student creation and RBAC updates"
git push origin main
```

After pushing, open Railway, check the latest deployment logs, and confirm that the deployment finished successfully. Then hard-refresh the Railway URL or open it in an incognito window to verify UI changes.

### Railway Database Synchronization

Since the Railway database is independent of your local environment, you must manually sync the database schema when structural changes are made.

1. **Run Sync Script**: Go to your Railway MySQL service and execute the contents of `database/railway_sync.sql`.
2. **Set Variables**: Ensure all environment variables from `.env` (like `DB_PASSWORD`, `SECRET_KEY`, and `SMTP` settings) are added to the Railway Service **Variables** tab.

## Validation Checklist

- Admin can log in and create a student from the Admin Dashboard.
- The new student appears in the Student Accounts list and in the Issue Book student selector.
- The created student can log in using the temporary password.
- Student dashboard keeps the existing catalog, self-issue, return, issued-books, and fine workflows.
- Student cannot call admin-only APIs such as `POST /students`, `POST /books`, `PUT /books/<id>`, `DELETE /books/<id>`, or `/reports`.
- Student issue and return APIs are still allowed only for the logged-in student's own records.
- Forgot Password sends an email code, accepts the code, updates the password, and allows login with the new password.
