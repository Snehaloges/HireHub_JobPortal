from contextlib import contextmanager
import sqlite3
from pass_valid import hash_password  

DB_NAME = "jobs.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,             
                        username TEXT,
                        email TEXT UNIQUE, 
                        password TEXT,
                        role TEXT DEFAULT 'user',
                        resume_path TEXT  
    )""")


    cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        company TEXT,
        title TEXT, 
        description TEXT, 
        salary REAL,
        location TEXT,
        experience TEXT,
        status TEXT DEFAULT 'open',
        posted_on TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS applications(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        job_id INTEGER, 
                        name TEXT,
                        email TEXT,
                        phone TEXT,
                        batch TEXT,
                        role TEXT,
                        relocate TEXT,
                        cover_letter TEXT,
                        resume_path TEXT,  
                        status TEXT DEFAULT 'Applied', 
                        date_applied TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )""")

    cur.execute("SELECT * FROM users WHERE role='admin'")
    admin = cur.fetchone()
    if not admin:
        hashed_pw = hash_password("admin123")
        cur.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
                    ("admin", "admin@mail.com", hashed_pw, "admin"))
        print("Default admin created -> email: admin@mail.com | password: admin123")

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
