import os
import multiprocessing
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from mapreduce import run_mapreduce
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)

# ---------------- SECURITY ----------------
app.secret_key = os.environ.get("SECRET_KEY", "default-secret")

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

# ---------------- FOLDERS ----------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# IMPORTANT FIX: ensure uploads folder exists (Railway safe)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ADMIN_USER = "taimoor"
ADMIN_PASS = "0000"


# ---------------- DATABASE ----------------
def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not found")
    return psycopg2.connect(db_url)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            key TEXT,
            value INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Wrong username or password")

    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("logfile")

        if not file or file.filename == "":
            return "No file selected"

        if not file.filename.endswith(".log"):
            return "Only .log files allowed"

        # Safe filename handling
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)

        # ---------------- MAPREDUCE SAFETY ----------------
        try:
            results = run_mapreduce(filepath)
        except Exception as e:
            return f"MapReduce Error: {str(e)}"

        if not isinstance(results, dict):
            return "Invalid MapReduce output (must be dict)"

        # ---------------- DATABASE SAVE ----------------
        try:
            conn = get_db()
            cur = conn.cursor()

            for key, value in results.items():
                cur.execute(
                    "INSERT INTO results (filename, key, value) VALUES (%s, %s, %s)",
                    (filename, key, value)
                )

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            return f"Database Error: {str(e)}"

        return render_template("results.html", results=results, filename=filename)

    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- RAILWAY ENTRY ----------------
if __name__ == "__main__":
    multiprocessing.freeze_support()

    try:
        if os.environ.get("DATABASE_URL"):
            init_db()
    except Exception as e:
        print("DB init error:", e)

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )