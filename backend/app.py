from dotenv import load_dotenv
load_dotenv()
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from functools import wraps
import os
from pathlib import Path
import random
import smtplib
import ssl

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

# from db import get_connection
from backend.db import get_connection

from datetime import date, datetime, timedelta, timezone

def get_ist_now():
    # Indian Standard Time (UTC + 5:30)
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=5, minutes=30)

def get_ist_date():
    return get_ist_now().date()

def get_mysql_format():
    return "%%b %%d, %%h:%%i %%p IST"

def get_python_format():
    return "%b %d, %I:%M %p IST"



BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
# app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")


FINE_PER_DAY = 5
ISSUE_DAYS = 14
RESET_CODE_MINUTES = 10


def json_ok(message, **payload):
    return jsonify({"success": True, "message": message, **payload})


def json_error(message, status=400):
    return jsonify({"success": False, "message": message}), status


def current_user():
    if "user" not in session:
        return None
    return session["user"]


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            if request.path.startswith("/api") or request.is_json:
                return json_error("Please login first.", 401)
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)

    return wrapper


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return json_error("Please login first.", 401)
            if user["role"].lower() != role.lower():
                return json_error("You do not have permission for this action.", 403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    with open("error_log.txt", "a") as f:
        f.write(f"\n--- {get_ist_now()} ---\n")
        f.write(traceback.format_exc())
    return json_error(f"Internal Server Error: {str(e)}", 500)


def fetch_one(cursor, query, values=None):
    cursor.execute(query, values or ())
    return cursor.fetchone()


def fetch_all(cursor, query, values=None):
    cursor.execute(query, values or ())
    return cursor.fetchall()

def ensure_schema():
    """Self-healing: Automatically create missing tables/columns in production."""
    try:
        from mysql.connector import Error
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Create book_requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                book_id INT NOT NULL,
                student_id INT NOT NULL,
                request_time DATETIME NOT NULL,
                status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
                rejection_reason VARCHAR(255),
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # 2. Add raw_password column to users if it doesn't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN raw_password VARCHAR(255)")
        except:
            pass # Already exists or couldn't add
            
        # 3. Create password_reset_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                email VARCHAR(160) NOT NULL,
                otp_code VARCHAR(255) NOT NULL,
                expiry_time DATETIME NOT NULL,
                is_used BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_password_reset_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Schema synchronization completed successfully.")
    except Exception as e:
        print(f"Schema synchronization warning: {e}")


def calculate_fine(due_date, return_date=None):
    returned = return_date or get_ist_now()
    days_late = max((returned - due_date).days, 0)
    return days_late * FINE_PER_DAY


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def smtp_configured():
    return all(
        [
            os.getenv("SMTP_HOST", "").strip(),
            os.getenv("SMTP_USERNAME", "").strip(),
            os.getenv("SMTP_PASSWORD", "").strip(),
            os.getenv("SMTP_FROM", "").strip(),
        ]
    )


def send_reset_email(to_email, name, code):
    if not smtp_configured():
        return False, "Email service is not configured. Please set SMTP environment variables."

    message = EmailMessage()
    message["Subject"] = "Library Management System password reset"
    message["From"] = os.getenv("SMTP_FROM")
    message["To"] = to_email
    message.set_content(
        f"Hello {name},\n\n"
        f"Your password reset code is {code}.\n"
        f"This code expires in {RESET_CODE_MINUTES} minutes.\n\n"
        "If you did not request this, please ignore this email."
    )

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip())
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() == "true"

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(username, password)
                server.send_message(message)
        return True, "Reset code sent."
    except Exception as exc:
        return False, f"Email could not be sent. Primary failed: {exc}. To fix: change SMTP_PORT to 587 and SMTP_USE_SSL to false in Railway."


def send_email(to_email, subject, body):
    if not smtp_configured():
        return False, "Email service is not configured. Please set SMTP environment variables."

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.getenv("SMTP_FROM")
    message["To"] = to_email
    message.set_content(body)

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip())
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() == "true"

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(username, password)
                server.send_message(message)
        return True, "Email sent."
    except Exception as exc:
        return False, f"Email could not be sent. Primary failed: {exc}. To fix: change SMTP_PORT to 587 and SMTP_USE_SSL to false in Railway."


@app.route("/api/test-network", methods=["GET", "POST"])
def test_network_api():
    """Diagnostic route to check outbound network connectivity."""
    import socket
    host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    port = to_int(os.getenv("SMTP_PORT", "465").strip(), 465)
    
    results = {
        "configured_host": host,
        "configured_port": port,
        "dns_resolve": None,
        "ipv4_connection": None,
        "alt_port_587": None
    }
    
    try:
        results["dns_resolve"] = socket.gethostbyname(host)
        # Try primary port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        s.close()
        results["ipv4_connection"] = "Success"
        
        # Try alternate port 587
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.settimeout(5)
        try:
            s2.connect((host, 587))
            results["alt_port_587"] = "Success"
        except:
            results["alt_port_587"] = "Failed"
        finally:
            s2.close()

        return jsonify({"success": True, "message": "Network check passed.", "details": results})
    except Exception as e:
        results["ipv4_connection"] = f"Failed: {str(e)}"
        return jsonify({"success": False, "message": "Network check failed.", "details": results})

@app.route("/api/debug-db")
def debug_db_api():
    """Diagnostic route to see database contents."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, email, role FROM users")
        users = cursor.fetchall()
        cursor.execute("SELECT count(*) as count FROM books")
        books_count = cursor.fetchone()["count"]
        return jsonify({"success": True, "users": users, "books_count": books_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/admin-force-reset")
def force_reset_admin_api():
    """Emergency route to reset Chandu and Ratna passwords."""
    from werkzeug.security import generate_password_hash
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Reset Admin (Chandu)
        admin_hash = generate_password_hash("chandu123")
        cursor.execute("UPDATE users SET password_hash = %s WHERE LOWER(username) = 'chandu'", (admin_hash,))
        
        # Reset Student (Ratna)
        student_hash = generate_password_hash("ratna123")
        cursor.execute("UPDATE users SET password_hash = %s WHERE LOWER(username) = 'ratna'", (student_hash,))
        
        conn.commit()
        return jsonify({
            "success": True, 
            "message": "Passwords reset: Chandu -> chandu123, Ratna -> ratna123. You can now login."
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Reset failed: {str(e)}"})

def get_library_stats():
    """Fetch real-time library statistics for the landing page."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # General stats
        cursor.execute("SELECT COALESCE(SUM(total_quantity), 0) as total_books FROM books")
        total_books = cursor.fetchone()["total_books"]
        
        cursor.execute("SELECT COUNT(*) as total_students FROM users WHERE role = 'student'")
        total_students = cursor.fetchone()["total_students"]
        
        cursor.execute("SELECT COUNT(*) as books_issued FROM transactions WHERE status = 'issued'")
        books_issued = cursor.fetchone()["books_issued"]
        
        cursor.execute("SELECT COUNT(*) as overdue_books FROM transactions WHERE status = 'issued' AND due_date < CURDATE()")
        overdue_books = cursor.fetchone()["overdue_books"]
        
        # Today's stats
        cursor.execute("SELECT COUNT(*) as today_issued FROM transactions WHERE issue_date = CURDATE()")
        today_issued = cursor.fetchone()["today_issued"]
        
        cursor.execute("SELECT COUNT(*) as today_returned FROM transactions WHERE return_date = CURDATE() AND status = 'returned'")
        today_returned = cursor.fetchone()["today_returned"]
        
        # Recent activities
        cursor.execute("""
            SELECT t.status, u.name as student_name, b.title as book_title, t.due_date, t.return_date, t.issue_date
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            ORDER BY t.created_at DESC
            LIMIT 3
        """)
        recent_transactions = cursor.fetchall()
        
        activities = []
        for t in recent_transactions:
            if t["status"] == "issued":
                activities.append({
                    "type": "issued",
                    "title": "Book issued",
                    "description": f"{t['student_name']} received {t['book_title']}",
                    "status": "On time" if t["due_date"].date() >= get_ist_date() else "Overdue"
                })
            else:
                activities.append({
                    "type": "returned",
                    "title": "Book returned",
                    "description": f"{t['student_name']} returned {t['book_title']}",
                    "status": "Closed"
                })
        
        return {
            "total_books": total_books,
            "total_students": total_students,
            "books_issued": books_issued,
            "overdue_books": overdue_books,
            "today_issued": today_issued,
            "today_returned": today_returned,
            "activities": activities
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {
            "total_books": 0, "total_students": 0, "books_issued": 0, "overdue_books": 0,
            "today_issued": 0, "today_returned": 0, "activities": []
        }
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()


@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("login_page"))
    return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "student_dashboard"))


@app.route("/login", methods=["GET"])
def login_page():
    if current_user():
        return redirect(url_for("index"))
    stats = get_library_stats()
    return render_template("login.html", stats=stats)


@app.route("/login", methods=["POST"])
def login_api():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip().lower()

    if not username or not password or role not in {"admin", "student"}:
        return json_error("Username, password, and role are required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            """
            SELECT id, name, username, email, password_hash, role
            FROM users
            WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)) AND role = %s
            """,
            (username, username, role),
        )
    except Error as exc:
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return json_error("Invalid login details.", 401)

    session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "username": user["username"],
        "role": user["role"],
    }
    dashboard = url_for("admin_dashboard" if user["role"] == "admin" else "student_dashboard")
    return json_ok("Login successful.", user=session["user"], redirect=dashboard)


@app.route("/forgot-password", methods=["POST"])
def forgot_password_api():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or "").strip()
    role = (data.get("role") or "").strip().lower()

    if not identifier or role not in {"admin", "student"}:
        return json_error("Please provide a valid username/email and role.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            """
            SELECT id, name, username, email
            FROM users
            WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)) AND role = %s
            """,
            (identifier, identifier, role),
        )

        print(f"DEBUG: Searching for user with identifier='{identifier}' and role='{role}'")
        if not user:
            return json_error(f"No {role} account found with that username or email.", 404)
        if not user.get("email"):
            return json_error("No email address is linked to this account.")

        # Generate 6-digit OTP
        code = str(random.SystemRandom().randint(100000, 999999))
        # Invalidate old tokens
        cursor.execute(
            "UPDATE password_reset_tokens SET is_used = TRUE WHERE user_id = %s AND is_used = FALSE",
            (user["id"],),
        )
        
        # Store new token
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (user_id, email, otp_code, expiry_time)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user["id"],
                user["email"],
                generate_password_hash(code),
                datetime.now() + timedelta(minutes=RESET_CODE_MINUTES),
            ),
        )
        conn.commit()

        sent, message = send_reset_email(user["email"], user["name"], code)
        if not sent:
            print(f"--- EMERGENCY OTP FALLBACK ---")
            print(f"Could not send email to {user['email']} due to Railway restrictions.")
            print(f"Your OTP code is: {code}")
            print(f"------------------------------")
            return json_ok("Email blocked by Railway. Check Railway Deployment Logs for your OTP code to proceed.")

        return json_ok("Reset code sent to the registered email.")
    except Exception as exc:
        if "conn" in locals():
            conn.rollback()
        print(f"DEBUG Forgot Password Error: {exc}")
        return json_error(f"Error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/forgot-username", methods=["POST"])
def forgot_username_api():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()

    if not email:
        return json_error("Email is required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            "SELECT name, username, email FROM users WHERE LOWER(email) = LOWER(%s) AND role = %s",
            (email, 'admin'),
        )
        if not user:
            user = fetch_one(
                cursor,
                "SELECT name, username, email FROM users WHERE LOWER(email) = LOWER(%s)",
                (email,),
            )

        if not user:
            return json_ok("If the email is registered to an admin, the username has been sent.")

        subject = f"Your {user.get('role', 'Library') if 'role' in user else 'Library'} Username"
        body = f"Hello {user['name']},\n\nYour username is: {user['username']}\n\nYou can now login to the system."
        
        sent, message = send_email(user["email"], subject, body)
        if not sent:
            print(f"--- EMERGENCY USERNAME FALLBACK ---")
            print(f"Could not send email to {user['email']} due to Railway restrictions.")
            print(f"Your Username is: {user['username']}")
            print(f"-----------------------------------")
            return json_ok("Email blocked by Railway. Check Railway Deployment Logs for your username.")

        return json_ok("Username sent to your email.")
    except Exception as exc:
        return json_error(f"Error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/verify-otp", methods=["POST"])
def verify_otp_api():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or "").strip()
    role = (data.get("role") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not identifier or role not in {"admin", "student"} or not code:
        return json_error("Role, username/email, and code are required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            "SELECT id FROM users WHERE (username = %s OR email = %s) AND role = %s",
            (identifier, identifier, role),
        )
        if not user:
            return json_error("Invalid details.", 400)

        reset = fetch_one(
            cursor,
            """
            SELECT id, otp_code, expiry_time
            FROM password_reset_tokens
            WHERE user_id = %s AND is_used = FALSE
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"],),
        )
        if not reset:
            return json_error("Reset code not found. Please request a new code.")
        if reset["expiry_time"] < datetime.now():
            return json_error("Reset code has expired. Please request a new code.")
        if not check_password_hash(reset["otp_code"], code):
            return json_error("Invalid reset code.")

        return json_ok("OTP verified. You can now reset your password.")
    except Error as exc:
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/reset-password", methods=["POST"])
def reset_password_api():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or "").strip()
    role = (data.get("role") or "").strip().lower()
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not identifier or role not in {"admin", "student"} or not code or not new_password:
        return json_error("All fields are required.")
    if new_password != confirm_password:
        return json_error("Passwords do not match.")
    if len(new_password) < 6:
        return json_error("Password must be at least 6 characters.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            "SELECT id FROM users WHERE (username = %s OR email = %s) AND role = %s",
            (identifier, identifier, role),
        )
        if not user:
            return json_error("Invalid details.", 400)

        reset = fetch_one(
            cursor,
            """
            SELECT id, otp_code, expiry_time
            FROM password_reset_tokens
            WHERE user_id = %s AND is_used = FALSE
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"],),
        )
        if not reset or reset["expiry_time"] < datetime.now() or not check_password_hash(reset["otp_code"], code):
            return json_error("Invalid or expired session. Please start over.")

        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (generate_password_hash(new_password), user["id"]),
        )
        cursor.execute(
            "UPDATE password_reset_tokens SET is_used = TRUE WHERE id = %s",
            (reset["id"],),
        )
        conn.commit()
        return json_ok("Password updated. Please login with your new password.")
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", user=current_user())


@app.route("/student")
@login_required
def student_dashboard():
    if current_user()["role"] != "student":
        return redirect(url_for("admin_dashboard"))
    return render_template("student_dashboard.html", user=current_user())


@app.route("/session")
@login_required
def session_api():
    return json_ok("Session active.", user=current_user())


@app.route("/students")
@role_required("admin")
def students_api():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        students = fetch_all(
            cursor,
            "SELECT id, name, username, email, raw_password FROM users WHERE role = 'student' ORDER BY name",
        )
        return json_ok("Students loaded.", students=students)
    except Error as exc:
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/students", methods=["POST"])
@role_required("admin")
def create_student_api():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not username or not email:
        return json_error("Name, username, and email are required.")
    if not password:
        password = f"{username[:4].lower() or 'stud'}{random.SystemRandom().randint(1000, 9999)}"
    if len(password) < 6:
        return json_error("Password must be at least 6 characters.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO users (name, username, email, password_hash, raw_password, role)
            VALUES (%s, %s, %s, %s, %s, 'student')
            """,
            (name, username, email, generate_password_hash(password), password),
        )
        conn.commit()
        return json_ok(
            "Student created.",
            student={"id": cursor.lastrowid, "name": name, "username": username, "email": email}
        )
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        if getattr(exc, "errno", None) == 1062:
            return json_error("Username or email already exists.")
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/api/admin/reset-student-password", methods=["POST"])
@role_required("admin")
def reset_student_password_api():
    data = request.get_json(silent=True) or {}
    user_id = to_int(data.get("user_id"))
    password = data.get("password") or ""

    if user_id <= 0:
        return json_error("Student ID is required.")
    if not password or len(password) < 6:
        return json_error("Password must be at least 6 characters.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and is a student
        user = fetch_one(cursor, "SELECT id FROM users WHERE id = %s AND role = 'student'", (user_id,))
        if not user:
            return json_error("Student not found.", 404)

        cursor.execute(
            "UPDATE users SET password_hash = %s, raw_password = %s WHERE id = %s",
            (generate_password_hash(password), password, user_id),
        )
        conn.commit()
        return json_ok("Password updated successfully.")
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/students/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def delete_student_api(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if student exists
        student = fetch_one(cursor, "SELECT id FROM users WHERE id = %s AND role = 'student'", (user_id,))
        if not student:
            return json_error("Student not found.", 404)

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return json_ok("Student deleted successfully.")
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/books", methods=["GET", "POST"])
@login_required
def books_api():
    if request.method == "GET":
        q = (request.args.get("q") or "").strip()
        params = []
        where = ""
        if q:
            where = "WHERE title LIKE %s OR author LIKE %s OR category LIKE %s"
            pattern = f"%{q}%"
            params = [pattern, pattern, pattern]

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            books = fetch_all(
                cursor,
                f"""
                SELECT id, title, author, category, total_quantity, available_quantity,
                       shelf, cover_url, created_at, updated_at
                FROM books
                {where}
                ORDER BY id DESC
                """,
                tuple(params),
            )
            
            user = current_user()
            if user["role"] == "student":
                reqs = fetch_all(cursor, "SELECT book_id, status, rejection_reason FROM book_requests WHERE student_id = %s AND status != 'cancelled'", (user["id"],))
                req_map = {r["book_id"]: r for r in reqs}
                
                issued = fetch_all(cursor, "SELECT book_id FROM transactions WHERE user_id = %s AND status = 'issued'", (user["id"],))
                issued_book_ids = {i["book_id"] for i in issued}
                
                for b in books:
                    r = req_map.get(b["id"])
                    b["request_status"] = r["status"] if r else None
                    b["rejection_reason"] = r["rejection_reason"] if r else None
                    b["is_issued"] = b["id"] in issued_book_ids
            else:
                for b in books:
                    b["request_status"] = None
                    b["rejection_reason"] = None
                    b["is_issued"] = False
                    
            return json_ok("Books loaded.", books=books)
        except Error as exc:
            return json_error(f"Database error: {exc}", 500)
        finally:
            if "cursor" in locals():
                cursor.close()
            if "conn" in locals():
                conn.close()

    user = current_user()
    if user["role"] != "admin":
        return json_error("Only admin can add books.", 403)

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    category = (data.get("category") or "").strip()
    shelf = (data.get("shelf") or "").strip()
    total_quantity = to_int(data.get("total_quantity"))

    if not title or not author or not category or not shelf or total_quantity <= 0:
        return json_error("Title, author, category, shelf, and quantity are required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO books (title, author, category, total_quantity, available_quantity, shelf, cover_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (title, author, category, total_quantity, total_quantity, shelf, ""),
        )
        conn.commit()
        return json_ok("Book added.", book_id=cursor.lastrowid)
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/books/<int:book_id>", methods=["PUT", "DELETE"])
@role_required("admin")
def book_detail_api(book_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "DELETE":
            active = fetch_one(
                cursor,
                "SELECT COUNT(*) AS total FROM transactions WHERE book_id = %s AND status = 'issued'",
                (book_id,),
            )
            if active["total"] > 0:
                return json_error("Cannot delete a book that is currently issued.")
            cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return json_error("Book not found.", 404)
            return json_ok("Book deleted.")

        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        author = (data.get("author") or "").strip()
        category = (data.get("category") or "").strip()
        shelf = (data.get("shelf") or "").strip()
        total_quantity = to_int(data.get("total_quantity"))

        if not title or not author or not category or not shelf or total_quantity <= 0:
            return json_error("Title, author, category, shelf, and quantity are required.")

        active = fetch_one(
            cursor,
            "SELECT COUNT(*) AS total FROM transactions WHERE book_id = %s AND status = 'issued'",
            (book_id,),
        )
        if total_quantity < active["total"]:
            return json_error("Total quantity cannot be less than issued copies.")

        available_quantity = total_quantity - active["total"]
        cursor.execute(
            """
            UPDATE books
            SET title = %s, author = %s, category = %s, total_quantity = %s,
                available_quantity = %s, shelf = %s, cover_url = %s
            WHERE id = %s
            """,
            (title, author, category, total_quantity, available_quantity, shelf, "", book_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return json_error("Book not found.", 404)
        return json_ok("Book updated.")
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/get", methods=["POST"])
@role_required("admin")
def issue_api():
    data = request.get_json(silent=True) or {}
    book_id = to_int(data.get("book_id"))
    user_id = to_int(data.get("user_id"))

    if book_id <= 0:
        return json_error("Book is required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        book = fetch_one(cursor, "SELECT * FROM books WHERE id = %s FOR UPDATE", (book_id,))
        student = fetch_one(cursor, "SELECT id, role FROM users WHERE id = %s", (user_id,))

        if not book:
            return json_error("Book not found.", 404)
        if not student or student["role"] != "student":
            return json_error("Valid student is required.")
        if book["available_quantity"] <= 0:
            return json_error("Book is not available right now.")

        duplicate = fetch_one(
            cursor,
            """
            SELECT id FROM transactions
            WHERE user_id = %s AND book_id = %s AND status = 'issued'
            """,
            (user_id, book_id),
        )
        if duplicate:
            return json_error("This book is already issued to the selected student.")

        checkout_time = get_ist_now()
        due_time = checkout_time + timedelta(days=15)
        cursor.execute(
            """
            INSERT INTO transactions (user_id, book_id, issue_date, due_date, status)
            VALUES (%s, %s, %s, %s, 'issued')
            """,
            (user_id, book_id, checkout_time, due_time),
        )
        transaction_id = cursor.lastrowid
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity - 1 WHERE id = %s",
            (book_id,),
        )
        conn.commit()
        return json_ok("Book issued successfully.", transaction_id=transaction_id, due_date=due_time.strftime(get_python_format()))
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/return", methods=["POST"])
@login_required
def return_api():
    user = current_user()
    data = request.get_json(silent=True) or {}
    transaction_id = to_int(data.get("transaction_id"))

    if transaction_id <= 0:
        return json_error("Transaction is required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        params = [transaction_id]
        if user["role"] != "student":
            return json_error("Only students can return books directly. Please ask the student to click return from their dashboard.", 403)
        
        owner_clause = "AND user_id = %s"
        params.append(user["id"])

        transaction = fetch_one(
            cursor,
            f"""
            SELECT * FROM transactions
            WHERE id = %s AND status = 'issued' {owner_clause}
            FOR UPDATE
            """,
            tuple(params),
        )
        if not transaction:
            return json_error("Active transaction not found.", 404)

        return_time = get_ist_now()
        fine = calculate_fine(transaction["due_date"], return_time)
        cursor.execute(
            """
            UPDATE transactions
            SET return_date = %s, fine_amount = %s, status = 'returned'
            WHERE id = %s
            """,
            (return_time, fine, transaction_id),
        )
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity + 1 WHERE id = %s",
            (transaction["book_id"],),
        )
        conn.commit()
        return json_ok("Book returned.", fine=fine, return_date=return_time.strftime(get_python_format()))
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/transactions")
@login_required
def transactions_api():
    user = current_user()
    status = (request.args.get("status") or "").strip()
    where = []
    params = []

    if user["role"] == "student":
        where.append("t.user_id = %s")
        params.append(user["id"])
    if status in {"issued", "returned"}:
        where.append("t.status = %s")
        params.append(status)

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        transactions = fetch_all(
            cursor,
            f"""
            SELECT t.id, t.issue_date, t.due_date, t.return_date,
                   t.issue_date AS issue_date_raw,
                   t.due_date AS due_date_raw,
                   CASE 
                     WHEN t.status = 'issued' AND t.due_date < NOW() THEN 'overdue'
                     ELSE t.status 
                   END AS status,
                   t.fine_amount,
                   u.name AS student_name, b.title AS book_title
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            {where_sql}
            ORDER BY t.id DESC
            """,
            tuple(params),
        )
        
        # Format dates and cast Decimals for JSON serialization
        py_fmt = get_python_format()
        for t in transactions:
            if t["issue_date"]: t["issue_date"] = t["issue_date"].strftime(py_fmt)
            if t["due_date"]: t["due_date"] = t["due_date"].strftime(py_fmt)
            if t["return_date"]: t["return_date"] = t["return_date"].strftime(py_fmt)
            if t.get("fine_amount") is not None:
                t["fine_amount"] = float(t["fine_amount"])
        
        return json_ok("Transactions loaded.", transactions=transactions)
    except Error as exc:
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/reports")
@role_required("admin")
def reports_api():
    today = get_ist_date()
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        stats = fetch_one(
            cursor,
            """
            SELECT
              SUM(status = 'issued') AS issued_count,
              SUM(status = 'returned') AS returned,
              SUM(status = 'issued' AND due_date < CURDATE()) AS overdue,
              COALESCE(SUM(fine_amount), 0) AS fine_total,
              (SELECT SUM(total_quantity) FROM books) AS total_books,
              (SELECT COUNT(DISTINCT category) FROM books) AS total_subjects
            FROM transactions
            """,
        )
        issued = fetch_all(
            cursor,
            """
            SELECT t.id, u.name AS student_name, b.title AS book_title, 
                   t.issue_date, t.due_date
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            WHERE t.status = 'issued'
            ORDER BY t.due_date ASC
            """,
        )
        returned = fetch_all(
            cursor,
            """
            SELECT t.id, u.name AS student_name, b.title AS book_title, 
                   t.return_date, t.fine_amount
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            WHERE t.status = 'returned'
            ORDER BY t.return_date DESC
            """,
        )
        overdue = fetch_all(
            cursor,
            """
            SELECT t.id, u.name AS student_name, b.title AS book_title, 
                   t.due_date,
                   DATEDIFF(%s, t.due_date) * %s AS current_fine
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            WHERE t.status = 'issued' AND t.due_date < %s
            ORDER BY t.due_date ASC
            """,
            (get_ist_now(), FINE_PER_DAY, get_ist_now()),
        )
        
        # Format and cast for JSON serialization
        py_fmt = get_python_format()
        if stats and stats["fine_total"] is not None:
            stats["fine_total"] = float(stats["fine_total"])
        
        for item in issued:
            if item["issue_date"]: item["issue_date"] = item["issue_date"].strftime(py_fmt)
            if item["due_date"]: item["due_date"] = item["due_date"].strftime(py_fmt)
            
        for item in returned:
            if item["return_date"]: item["return_date"] = item["return_date"].strftime(py_fmt)
            if item.get("fine_amount") is not None:
                item["fine_amount"] = float(item["fine_amount"])
        
        for item in overdue:
            if item["due_date"]: item["due_date"] = item["due_date"].strftime(py_fmt)
            if item.get("current_fine") is not None:
                item["current_fine"] = float(item["current_fine"])

        if stats:
            stats["available_books"] = (stats["total_books"] or 0) - (stats["issued_count"] or 0)
            
        return json_ok("Reports loaded.", stats=stats, issued=issued, returned=returned, overdue=overdue)
    except Error as exc:
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/api/student/stats", methods=["GET"])
@role_required("student")
def student_stats_api():
    user = current_user()
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Total library stock (sum of all copies across all subjects)
        cursor.execute("SELECT SUM(total_quantity) as count FROM books")
        total_books = cursor.fetchone()["count"] or 0
        
        # 2. Total issued books globally (to calculate availability)
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE status = 'issued'")
        issued_global = cursor.fetchone()["count"] or 0
        available_books = total_books - issued_global
        
        # 3. Specific student's active issued books count
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE user_id = %s AND status = 'issued'", (user["id"],))
        student_issued = cursor.fetchone()["count"] or 0
        
        # 4. Total fine for this student
        cursor.execute("SELECT SUM(fine_amount) as fine FROM transactions WHERE user_id = %s", (user["id"],))
        total_fine = cursor.fetchone()["fine"] or 0.0
        
        # 5. Total unique subjects (using category field)
        cursor.execute("SELECT COUNT(DISTINCT category) as count FROM books")
        total_subjects = cursor.fetchone()["count"] or 0
        
        return json_ok("Stats loaded.", stats={
            "issued_books_count": int(student_issued),
            "total_books": int(total_books),
            "available_books": int(available_books),
            "total_subjects": int(total_subjects),
            "total_fine": float(total_fine)
        })
    except Exception as e:
        print(f"[DEBUG ERROR] {e}")
        return json_error(str(e))
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()


@app.route("/api/admin/update-profile", methods=["POST"])
@login_required
def update_admin_profile():
    user = current_user()
    if user["role"] != "admin":
        return json_error("Unauthorized.", 403)

    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    new_username = (data.get("username") or "").strip()

    if not new_name or not new_username:
        return json_error("Name and Username are required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if new username is taken by someone else
        duplicate = fetch_one(
            cursor,
            "SELECT id FROM users WHERE username = %s AND id != %s",
            (new_username, user["id"]),
        )
        if duplicate:
            return json_error("This username is already taken.")

        cursor.execute(
            "UPDATE users SET name = %s, username = %s WHERE id = %s",
            (new_name, new_username, user["id"]),
        )
        conn.commit()
        return json_ok("Profile updated successfully. Please note your new username.")
    except Exception as exc:
        if "conn" in locals():
            conn.rollback()
        return json_error(f"Error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


@app.route("/request-book", methods=["POST"])
@role_required("student")
def request_book_api():
    user = current_user()
    data = request.get_json(silent=True) or {}
    book_id = to_int(data.get("book_id"))
    
    if book_id <= 0:
        return json_error("Book is required.")
        
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        existing = fetch_one(cursor, 
            "SELECT id FROM book_requests WHERE book_id = %s AND student_id = %s AND status = 'pending'",
            (book_id, user["id"]))
        if existing:
            return json_error("You already have a pending request for this book.")
            
        issued = fetch_one(cursor, 
            "SELECT id FROM transactions WHERE book_id = %s AND user_id = %s AND status = 'issued'",
            (book_id, user["id"]))
        if issued:
            return json_error("You already have this book issued.")

        cursor.execute(
            "INSERT INTO book_requests (book_id, student_id, request_time, status) VALUES (%s, %s, %s, 'pending')",
            (book_id, user["id"], get_ist_now())
        )
        conn.commit()
        return json_ok("Request submitted successfully.")
    except Exception as e:
        return json_error(str(e))
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()

@app.route("/admin/requests")
@role_required("admin")
def get_requests_api():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        requests = fetch_all(cursor, """
            SELECT r.id, r.book_id, r.student_id, r.request_time, r.status,
                   u.name as student_name, b.title as book_title
            FROM book_requests r
            JOIN users u ON u.id = r.student_id
            JOIN books b ON b.id = r.book_id
            WHERE r.status IN ('pending', 'rejected')
            ORDER BY r.request_time DESC
        """)
        
        py_fmt = get_python_format()
        for r in requests:
            if r["request_time"]: r["request_time"] = r["request_time"].strftime(py_fmt)
            
        return json_ok("Requests loaded.", requests=requests)
    except Exception as e:
        return json_error(str(e))
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()

@app.route("/approve-request", methods=["POST"])
@role_required("admin")
def approve_request_api():
    data = request.get_json(silent=True) or {}
    request_id = to_int(data.get("request_id"))
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        req = fetch_one(cursor, "SELECT * FROM book_requests WHERE id = %s AND status = 'pending'", (request_id,))
        if not req:
            return json_error("Request not found or already processed.")
            
        book_id = req["book_id"]
        user_id = req["student_id"]
        
        book = fetch_one(cursor, "SELECT * FROM books WHERE id = %s FOR UPDATE", (book_id,))
        if not book or book["available_quantity"] <= 0:
            return json_error("Book no longer available.")
            
        checkout_time = get_ist_now()
        due_time = checkout_time + timedelta(days=15)
        
        cursor.execute(
            "INSERT INTO transactions (user_id, book_id, issue_date, due_date, status) VALUES (%s, %s, %s, %s, 'issued')",
            (user_id, book_id, checkout_time, due_time)
        )
        cursor.execute("UPDATE books SET available_quantity = available_quantity - 1 WHERE id = %s", (book_id,))
        cursor.execute("UPDATE book_requests SET status = 'approved' WHERE id = %s", (request_id,))
        
        conn.commit()
        return json_ok("Request approved and book issued.")
    except Exception as e:
        if "conn" in locals(): conn.rollback()
        return json_error(str(e))
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()

@app.route("/reject-request", methods=["POST"])
@role_required("admin")
def reject_request_api():
    data = request.get_json(silent=True) or {}
    request_id = to_int(data.get("request_id"))
    reason = (data.get("reason") or "Out of stock").strip()
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "UPDATE book_requests SET status = 'rejected', rejection_reason = %s WHERE id = %s",
            (reason, request_id)
        )
        conn.commit()
        return json_ok("Request rejected.")
    except Exception as e:
        return json_error(str(e))
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()

@app.route("/api/admin/requests/<int:request_id>/reset", methods=["POST"])
@role_required("admin")
def reset_request_api(request_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        # Verify it's rejected
        req = fetch_one(cursor, "SELECT * FROM book_requests WHERE id = %s AND status = 'rejected'", (request_id,))
        if not req:
            return json_error("Only rejected requests can be reset.")
            
        cursor.execute("UPDATE book_requests SET status = 'cancelled' WHERE id = %s", (request_id,))
        conn.commit()
        return json_ok("Request reset successfully.")
    except Exception as e:
        return json_error(str(e))
    finally:
        if "cursor" in locals(): cursor.close()
        if "conn" in locals(): conn.close()

# Ensure DB schema is up to date on startup
ensure_schema()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

