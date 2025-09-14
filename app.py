from db import init_db, get_db
from pass_valid import validate_password, hash_password, verify_password
from auth import create_jwt, jwt_required
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
import os, datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"),static_folder=os.path.join(BASE_DIR, "static"))

app.secret_key = "supersecret"

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

#Route protection
def login_required_page(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("home_page") + "#login")
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("home_page") + "#login")
        if session.get("role") != "admin":
            flash("Unauthorized access")
            return redirect(url_for("home_page"))
        return f(*args, **kwargs)
    return wrapper


#register-login routes

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "username, email and password required"}), 400

    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"error": msg}), 400

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE email=?", (email,))
            if cur.fetchone():
                return jsonify({"error": "Email already exists"}), 400

            cur.execute(
                "INSERT INTO users(username, email, password) VALUES(?, ?, ?)",
                (username, email, hash_password(password))
            )

        return jsonify({"message": "registered"}), 201

    except Exception as e:
        print("ERROR in /register:", e)
        return jsonify({"error": "Server error"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, password, role, resume_path FROM users WHERE email=?", (email,))
        row = cur.fetchone()

    if not row:
        return jsonify({"error": "User not registered", "redirect": "register"}), 401
    if not verify_password(password, row[2]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_jwt(row[0], row[3], hours_valid=24*7)
    session["user_id"] = row[0]
    session["username"] = row[1]
    session["role"] = row[3]
    session["resume_uploaded"] = bool(row[4])

    return jsonify({"token": token, "role": row[3], "message": "logged_in"})


#jobs page route
@app.route("/jobs_page", methods=["GET"])
def jobs_page():
    role_filter = request.args.get("role", "").strip()
    location_filter = request.args.get("location", "").strip()

    with get_db() as conn:
        cur = conn.cursor()
        query = """
            SELECT id, company, title, description, salary, location, experience, status, posted_on
            FROM jobs
            WHERE 1=1
        """
        params = []

        if role_filter:
            query += " AND title LIKE ?"
            params.append(f"%{role_filter}%")
        if location_filter:
            query += " AND location LIKE ?"
            params.append(f"%{location_filter}%")

        query += " ORDER BY id DESC"
        cur.execute(query, params)
        rows = cur.fetchall()

        jobs_list = []
        for r in rows:
            job ={
                "id": r[0],
                "company": r[1],
                "title": r[2],
                "description": r[3],
                "salary": r[4],
                "location": r[5],
                "experience": r[6],
                "status": r[7],
                "posted_on": r[8],
                "applied": False
                }

            if session.get("user_id"):
                    cur.execute("SELECT 1 FROM applications WHERE user_id=? AND job_id=?", 
                                (session["user_id"], job["id"]))
                    if cur.fetchone():
                        job["applied"] = True

            jobs_list.append(job)

    return render_template("jobs.html", jobs=jobs_list, role=role_filter, location=location_filter)



#job details page route
@app.route("/job/<int:job_id>")
def job_details(job_id):
    applied = False
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, company, title, description, salary, location,experience, posted_on FROM jobs WHERE id=?", (job_id,))
        r = cur.fetchone()
        if not r:
            return "Job not found", 404
        job = {
            "id": r[0],
            "company": r[1],
            "title": r[2],
            "description": r[3],
            "salary": r[4],
            "location": r[5],
            "experience": r[6],
            "posted_on": r[7],
        }

        if session.get("user_id"):
            cur.execute("SELECT 1 FROM applications WHERE user_id=? AND job_id=?", 
                        (session["user_id"], job_id))
            if cur.fetchone():
                applied = True

    return render_template("job_details.html", job=job, applied=applied)

#apply job route

@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
@login_required_page
def apply_job(job_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, company, title FROM jobs WHERE id=?", (job_id,))
        job = cur.fetchone()
        if not job:
            return "Job not found", 404
        job_obj = {"id": job[0], "company": job[1], "title": job[2]}


        cur.execute("SELECT 1 FROM applications WHERE user_id=? AND job_id=?", 
                    (session["user_id"], job_id))
        if cur.fetchone():
            flash("You have already applied for this job.", "warning")
            return redirect(url_for("jobs_page"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            batch = request.form.get("batch", "").strip()
            role = request.form.get("role", "").strip()
            relocate = request.form.get("relocate", "").strip()
            cover_letter = request.form.get("coverLetter", "").strip()
            file = request.files.get("resume")

            if not all([name, email, phone, batch, role, relocate, file]):
                return jsonify({"success": False, "error": "All fields including resume are required"}), 400

            if file and file.filename.endswith(".pdf"):
                filename = f"resume_{session['user_id']}_{int(datetime.datetime.now().timestamp())}.pdf"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
            else:
                return jsonify({"success": False, "error": "Only PDF resumes allowed"}), 400

            cur.execute(
                """INSERT INTO applications
                   (user_id, job_id, name, email, phone, batch, role, relocate, cover_letter, resume_path, date_applied)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session["user_id"], job_id, name, email, phone, batch, role, relocate,
                 cover_letter, filename, datetime.date.today().isoformat())
            )
            conn.commit()

            return jsonify({"success": True, "message": "Application submitted successfully!", "resume_url": url_for("uploaded_resume", filename=filename)})


        return render_template("apply.html", job=job_obj, user={
            "username": session.get("username"),
            "email": "",
            "phone": "",
            "batch": ""
        })



#admin dashboard route
@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin.html")

#admin users page route
@app.route("/admin/users")
@admin_required
def admin_users():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email FROM users  WHERE username != 'admin' ORDER BY id DESC")
        users = [{"id": r[0], "username": r[1], "email": r[2]} for r in cur.fetchall()]

        for user in users:
            cur.execute("""
                SELECT j.title
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.user_id=?
            """, (user["id"],))
            jobs = [r[0] for r in cur.fetchall()]
            user["applied_jobs"] = jobs

    return render_template("admin_users.html", users=users)


#admin jobs page route
@app.route("/admin/jobs")
@admin_required
def admin_jobs():
    return render_template("admin_jobs.html")


@app.route("/admin/jobs_json", methods=["GET"])
@admin_required
def admin_jobs_json():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, company, title, description, salary, location, experience, status, posted_on
            FROM jobs ORDER BY id DESC
        """)
        rows = cur.fetchall()
    jobs = [
        {
            "id": r[0],
            "company": r[1],
            "title": r[2],
            "description": r[3],
            "salary": r[4],
            "location": r[5],
            "experience": r[6],
            "status": r[7],
            "posted_on": r[8],
        }
        for r in rows
    ]
    return jsonify(jobs)



@app.route("/admin/add_job", methods=["POST"])
@admin_required
def add_job():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    company = data.get("company", "").strip()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    salary = data.get("salary")
    location = data.get("location", "").strip()
    experience = data.get("experience", "").strip()
    status = data.get("status", "open").strip().lower()

    if not all([company, title, description, salary, location, experience]):
        return jsonify({"error": "All fields are required"}), 400

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO jobs(company, title, description, salary, location, experience, status, posted_on) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (company, title, description, salary, location, experience, status, datetime.date.today().isoformat())
        )
        conn.commit()

    return jsonify({"message": "Job added successfully!"}), 201


@app.route("/admin/edit_job/<int:job_id>", methods=["PUT"])
@admin_required
def edit_job(job_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    company = data.get("company", "").strip()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    salary = data.get("salary")
    location = data.get("location", "").strip()
    experience = data.get("experience", "").strip()
    status = data.get("status", "").strip()

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""UPDATE jobs 
                       SET title=?, description=?, salary=?, location=?, company=?, experience=?, status=? 
                       WHERE id=?""",
                    (title, description, salary, location, company, experience, status, job_id))
        conn.commit()

    return jsonify({"message": "Job updated successfully!"})


@app.route("/admin/delete_job/<int:job_id>", methods=["DELETE"])
@admin_required
def delete_job(job_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()

    return jsonify({"message": "Job deleted successfully!"})

#application page for admin
@app.route("/admin/applications_page")
@admin_required
def admin_applications_page():
    return render_template("admin_applications.html")

#applications page route
@app.route("/admin/applications", methods=["GET"])
@admin_required
def admin_applications():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.name, a.email, a.phone, a.batch, a.role, a.relocate,
                   j.title, a.cover_letter, a.date_applied, a.resume_path
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.id DESC
        """)
        rows = cur.fetchall()

    apps = [ {
        "id": r[0],
        "name": r[1],
        "email": r[2],
        "phone": r[3],
        "batch": r[4],
        "role": r[5],
        "relocate": r[6],
        "job_title": r[7],
        "cover_letter": r[8],
        "date_applied": r[9],
        "resume_path": r[10]
    } for r in rows]

    return jsonify(apps)


#Resume upload 

@app.route("/upload_resume", methods=["POST"])
@jwt_required
def upload_resume(current_user):
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and file.mimetype in ["application/pdf", "application/msword"]:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > 1 * 1024 * 1024:
            return jsonify({"error": "File exceeds 1MB"}), 400

        filename = f"user_{current_user['user_id']}_{file.filename}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET resume_path=? WHERE id=?", (filename, current_user["user_id"]))
            conn.commit()
        session["resume_uploaded"] = True

        return jsonify({"message": "Resume uploaded successfully!", "resume_url": url_for("uploaded_resume", filename=filename)})

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/uploads/resumes/<filename>")
def uploaded_resume(filename):
    full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(full_path):
        return "File not found on server", 404
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/")
def home_page():
    user = None
    applied_jobs = []

    if session.get("user_id"):
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT username, email, resume_path FROM users WHERE id=?", (session["user_id"],))
            row = cur.fetchone()
            if row:
                user = {
                    "username": row[0],
                    "email": row[1],
                    "resume": row[2]
                }
            cur.execute("""
                SELECT j.title, j.company, a.date_applied
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.user_id=?
                ORDER BY a.date_applied DESC
            """, (session["user_id"],))
            applied_jobs = [{"title": r[0], "company": r[1], "date": r[2]} for r in cur.fetchall()]

    return render_template("index.html", user=user, applied_jobs=applied_jobs)


@app.route("/session-info")
def session_info():
    if "user_id" not in session:
        return jsonify({"role": None})
    return jsonify({"user_id": session["user_id"], "username": session["username"], "role": session["role"]})


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("home_page"))

if __name__ == "__main__":
    import webbrowser
    import threading

    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    app.run(host="0.0.0.0", port=5000, debug=True)

