import os
import multiprocessing
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from mapreduce import run_mapreduce
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# ---------------- SECURITY ----------------
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    raise RuntimeError("SECRET_KEY is not set in Railway environment variables!")
app.secret_key = _secret

app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 1800

@app.before_request
def force_https_scheme():
    from flask import request
    if request.headers.get("X-Forwarded-Proto") == "https":
        request.environ["wsgi.url_scheme"] = "https"

# ---------------- FOLDERS ----------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

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


try:
    if os.environ.get("DATABASE_URL"):
        init_db()
except Exception as e:
    print("DB init error:", e)


# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("dashboard"))
        else:
            flash("Wrong username or password", "error")

    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("logfile")

        if not file or file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("dashboard"))

        # reject anything that is not strictly filename.log
        if not file.filename.endswith(".log") or file.filename.endswith(".log.text") or file.filename.endswith(".log.txt"):
            flash("Invalid file. Only .log files are allowed. Your file appears to be: " + file.filename, "error")
            return redirect(url_for("dashboard"))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # ---------------- MAPREDUCE ----------------
        try:
            results = run_mapreduce(filepath)
        except ValueError as e:
            # log format not recognized — show friendly message on dashboard
            flash(str(e), "error")
            return redirect(url_for("dashboard"))
        except Exception as e:
            # any other processing error
            flash(f"Processing error: {str(e)}", "error")
            return redirect(url_for("dashboard"))

        # ---------------- DATABASE SAVE ----------------
        try:
            conn = get_db()
            cur = conn.cursor()
            for key, value in results.items():
                cur.execute(
                    "INSERT INTO results (filename, key, value) VALUES (%s, %s, %s)",
                    (filename, key, int(value))
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
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )