import sqlite3
import os

database_path = os.path.join(os.getcwd(), "app", "data", "jobs.db")
os.makedirs(os.path.dirname(database_path), exist_ok=True)  # ensure folder exists

# Create table if not exists
with sqlite3.connect(database_path) as con:
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT
        )
    ''')
    con.commit()


def save_job(job_id: str, status: str):
    with sqlite3.connect(database_path) as con:
        cur = con.cursor()  # create cursor for this connection!
        cur.execute("INSERT OR REPLACE INTO jobs (id, status) VALUES (?, ?)", (job_id, status))
        con.commit()


def load_job(job_id: str):
    with sqlite3.connect(database_path) as con:
        cur = con.cursor()  # create cursor for this connection!
        cur.execute("SELECT status FROM jobs WHERE id=?", (job_id,))
        row = cur.fetchone()
        return row[0] if row else None
