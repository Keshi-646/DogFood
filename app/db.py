import os, sqlite3
from pathlib import Path
from flask import current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 email TEXT UNIQUE NOT NULL,
 password TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('participant','judge','organizer','admin'))
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 slug TEXT UNIQUE NOT NULL,
 status TEXT NOT NULL DEFAULT 'draft'
);
CREATE TABLE IF NOT EXISTS teams (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id INTEGER NOT NULL,
 name TEXT NOT NULL,
 captain_id INTEGER NOT NULL,
 FOREIGN KEY(event_id) REFERENCES events(id),
 FOREIGN KEY(captain_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS team_members (
 team_id INTEGER NOT NULL,
 user_id INTEGER NOT NULL,
 PRIMARY KEY(team_id,user_id),
 FOREIGN KEY(team_id) REFERENCES teams(id),
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS submissions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id INTEGER NOT NULL,
 team_id INTEGER NOT NULL,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 repo_url TEXT,
 demo_url TEXT,
 status TEXT NOT NULL DEFAULT 'submitted',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(event_id) REFERENCES events(id),
 FOREIGN KEY(team_id) REFERENCES teams(id)
);
CREATE TABLE IF NOT EXISTS rubric_criteria (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id INTEGER NOT NULL,
 name TEXT NOT NULL,
 weight REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 submission_id INTEGER NOT NULL,
 judge_id INTEGER NOT NULL,
 UNIQUE(submission_id,judge_id),
 FOREIGN KEY(submission_id) REFERENCES submissions(id),
 FOREIGN KEY(judge_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS scores (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 assignment_id INTEGER NOT NULL,
 criterion_id INTEGER NOT NULL,
 score REAL NOT NULL,
 UNIQUE(assignment_id,criterion_id),
 FOREIGN KEY(assignment_id) REFERENCES assignments(id),
 FOREIGN KEY(criterion_id) REFERENCES rubric_criteria(id)
);
CREATE TABLE IF NOT EXISTS normalized_results (
 submission_id INTEGER PRIMARY KEY,
 raw_score REAL NOT NULL,
 normalized_score REAL NOT NULL,
 rank INTEGER,
 FOREIGN KEY(submission_id) REFERENCES submissions(id)
);
"""

def db_path():
    return current_app.config["DATABASE_URL"]

def get_db():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    Path(db_path()).parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return
    users = [
        ("Alice Participant","alice@example.com","alice123","participant"),
        ("Bob Participant","bob@example.com","bob123","participant"),
        ("Judge One","judge1@example.com","judge123","judge"),
        ("Judge Two","judge2@example.com","judge123","judge"),
        ("Organizer","organizer@example.com","organizer123","organizer"),
        ("Admin","admin@example.com","admin123","admin"),
    ]
    conn.executemany("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)", users)
    conn.execute("INSERT INTO events(name,slug,status) VALUES(?,?,?)",
                 ("HackForge Dogfood 2026","hackforge-2026","open"))
    event_id = conn.execute("SELECT id FROM events").fetchone()[0]
    criteria = [("Technical Quality",40),("Impact & Innovation",30),("UX & Completeness",30)]
    conn.executemany("INSERT INTO rubric_criteria(event_id,name,weight) VALUES(?,?,?)",
                     [(event_id,n,w) for n,w in criteria])
    alice = conn.execute("SELECT id FROM users WHERE email='alice@example.com'").fetchone()[0]
    judge1 = conn.execute("SELECT id FROM users WHERE email='judge1@example.com'").fetchone()[0]
    team_id = conn.execute("INSERT INTO teams(event_id,name,captain_id) VALUES(?,?,?)",
                           (event_id,"Seed Team",alice)).lastrowid
    conn.execute("INSERT INTO team_members(team_id,user_id) VALUES(?,?)",(team_id,alice))
    sub_id = conn.execute(
        "INSERT INTO submissions(event_id,team_id,title,description,repo_url,demo_url) VALUES(?,?,?,?,?,?)",
        (event_id,team_id,"Seed Portal","Seeded end-to-end submission",
         "https://github.com/example/hackforge","https://example.com/demo")).lastrowid
    conn.execute("INSERT INTO assignments(submission_id,judge_id) VALUES(?,?)",(sub_id,judge1))
    conn.commit()
    conn.close()
