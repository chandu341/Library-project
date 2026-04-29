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
            if user["role"] != role:
                return json_error("You do not have permission for this action.", 403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def fetch_one(cursor, query, values=None):
    cursor.execute(query, values or ())
    return cursor.fetchone()


def fetch_all(cursor, query, values=None):
    cursor.execute(query, values or ())
    return cursor.fetchall()


def calculate_fine(due_date, return_date=None):
    returned = return_date or date.today()
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
            os.getenv("SMTP_HOST"),
            os.getenv("SMTP_USERNAME"),
            os.getenv("SMTP_PASSWORD"),
            os.getenv("SMTP_FROM"),
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

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

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
        return False, f"Email could not be sent: {exc}"


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
    return render_template("login.html")


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
            WHERE (username = %s OR email = %s) AND role = %s
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
        return json_error("Role and username/email are required.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            """
            SELECT id, name, username, email
            FROM users
            WHERE (username = %s OR email = %s) AND role = %s
            """,
            (identifier, identifier, role),
        )

        if not user:
            return json_ok("If the account exists, a reset code has been sent.")
        if not user.get("email"):
            return json_error("No email address is linked to this account.")

        code = str(random.SystemRandom().randint(100000, 999999))
        sent, message = send_reset_email(user["email"], user["name"], code)
        if not sent:
            return json_error(message, 500)

        cursor.execute(
            "UPDATE password_resets SET used = TRUE WHERE user_id = %s AND used = FALSE",
            (user["id"],),
        )
        cursor.execute(
            """
            INSERT INTO password_resets (user_id, code_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (
                user["id"],
                generate_password_hash(code),
                datetime.now() + timedelta(minutes=RESET_CODE_MINUTES),
            ),
        )
        conn.commit()
        return json_ok("Reset code sent to the registered email.")
    except Error as exc:
        if "conn" in locals():
            conn.rollback()
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

    if not identifier or role not in {"admin", "student"} or not code or not new_password:
        return json_error("Role, username/email, code, and new password are required.")
    if len(new_password) < 6:
        return json_error("Password must be at least 6 characters.")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        user = fetch_one(
            cursor,
            """
            SELECT id
            FROM users
            WHERE (username = %s OR email = %s) AND role = %s
            """,
            (identifier, identifier, role),
        )
        if not user:
            return json_error("Invalid reset details.", 400)

        reset = fetch_one(
            cursor,
            """
            SELECT id, code_hash, expires_at
            FROM password_resets
            WHERE user_id = %s AND used = FALSE
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"],),
        )
        if not reset:
            return json_error("Reset code not found. Please request a new code.")
        if reset["expires_at"] < datetime.now():
            return json_error("Reset code has expired. Please request a new code.")
        if not check_password_hash(reset["code_hash"], code):
            return json_error("Invalid reset code.")

        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (generate_password_hash(new_password), user["id"]),
        )
        cursor.execute(
            "UPDATE password_resets SET used = TRUE WHERE id = %s",
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
@login_required
def admin_dashboard():
    if current_user()["role"] != "admin":
        return redirect(url_for("student_dashboard"))
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
            "SELECT id, name, username FROM users WHERE role = 'student' ORDER BY name",
        )
        return json_ok("Students loaded.", students=students)
    except Error as exc:
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
    cover_url = (data.get("cover_url") or "").strip()
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
            (title, author, category, total_quantity, total_quantity, shelf, cover_url),
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
        cover_url = (data.get("cover_url") or "").strip()
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
            (title, author, category, total_quantity, available_quantity, shelf, cover_url, book_id),
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


@app.route("/issue", methods=["POST"])
@login_required
def issue_api():
    user = current_user()
    data = request.get_json(silent=True) or {}
    book_id = to_int(data.get("book_id"))
    user_id = to_int(data.get("user_id"), user["id"])

    if user["role"] == "student":
        user_id = user["id"]

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

        issue_date = date.today()
        due_date = issue_date + timedelta(days=ISSUE_DAYS)
        cursor.execute(
            """
            INSERT INTO transactions (user_id, book_id, issue_date, due_date, status)
            VALUES (%s, %s, %s, %s, 'issued')
            """,
            (user_id, book_id, issue_date, due_date),
        )
        transaction_id = cursor.lastrowid
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity - 1 WHERE id = %s",
            (book_id,),
        )
        conn.commit()
        return json_ok("Book issued.", transaction_id=transaction_id, due_date=due_date.isoformat())
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
        owner_clause = ""
        if user["role"] == "student":
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

        return_date = date.today()
        fine = calculate_fine(transaction["due_date"], return_date)
        cursor.execute(
            """
            UPDATE transactions
            SET return_date = %s, fine_amount = %s, status = 'returned'
            WHERE id = %s
            """,
            (return_date, fine, transaction_id),
        )
        cursor.execute(
            "UPDATE books SET available_quantity = available_quantity + 1 WHERE id = %s",
            (transaction["book_id"],),
        )
        conn.commit()
        return json_ok("Book returned.", fine=fine, return_date=return_date.isoformat())
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
            SELECT t.id, t.issue_date, t.due_date, t.return_date, t.status, t.fine_amount,
                   u.name AS student_name, b.title AS book_title
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            {where_sql}
            ORDER BY t.id DESC
            """,
            tuple(params),
        )
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
    today = date.today()
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        stats = fetch_one(
            cursor,
            """
            SELECT
              SUM(status = 'issued') AS issued,
              SUM(status = 'returned') AS returned,
              SUM(status = 'issued' AND due_date < CURDATE()) AS overdue,
              COALESCE(SUM(fine_amount), 0) AS fine_total
            FROM transactions
            """,
        )
        issued = fetch_all(
            cursor,
            """
            SELECT t.id, u.name AS student_name, b.title AS book_title, t.issue_date, t.due_date
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
            SELECT t.id, u.name AS student_name, b.title AS book_title, t.return_date, t.fine_amount
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
            SELECT t.id, u.name AS student_name, b.title AS book_title, t.due_date,
                   DATEDIFF(%s, t.due_date) * %s AS current_fine
            FROM transactions t
            JOIN users u ON u.id = t.user_id
            JOIN books b ON b.id = t.book_id
            WHERE t.status = 'issued' AND t.due_date < %s
            ORDER BY t.due_date ASC
            """,
            (today, FINE_PER_DAY, today),
        )
        return json_ok("Reports loaded.", stats=stats, issued=issued, returned=returned, overdue=overdue)
    except Error as exc:
        return json_error(f"Database error: {exc}", 500)
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "5000")), debug=True, use_reloader=False)
