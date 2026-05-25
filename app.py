import os
import multiprocessing
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from mapreduce import run_mapreduce

load_dotenv()

app = Flask(__name__)

# ---------------- SECURITY FIX (MOBILE + SESSION) ----------------
app.secret_key = os.environ.get("SECRET_KEY", "default-secret")

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True


UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
        file = request.files["logfile"]

        if file and file.filename.endswith(".log"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            results = run_mapreduce(filepath)

            conn = get_db()
            cur = conn.cursor()

            for key, value in results.items():
                cur.execute(
                    "INSERT INTO results (filename, key, value) VALUES (%s, %s, %s)",
                    (file.filename, key, value)
                )

            conn.commit()
            cur.close()
            conn.close()

            return render_template("results.html", results=results, filename=file.filename)

    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- RAILWAY ENTRY POINT ----------------
if __name__ == "__main__":
    multiprocessing.freeze_support()

    try:
        if os.environ.get("DATABASE_URL"):
            init_db()
    except Exception as e:
        print("DB init error:", e)

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )