import json
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "cv_data.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    linkedin TEXT,
    website TEXT,
    summary TEXT,
    career_goals TEXT
);

CREATE TABLE IF NOT EXISTS experiences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    location TEXT,
    start_date TEXT,
    end_date TEXT,
    bullets TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT NOT NULL,
    degree TEXT,
    field TEXT,
    start_date TEXT,
    end_date TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    bullets TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    issuer TEXT,
    date TEXT
);
"""


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def set_profile(conn, full_name, email=None, phone=None, address=None,
                 linkedin=None, website=None, summary=None, career_goals=None):
    conn.execute(
        """
        INSERT INTO profile (id, full_name, email, phone, address, linkedin, website, summary, career_goals)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            full_name=excluded.full_name,
            email=COALESCE(excluded.email, profile.email),
            phone=COALESCE(excluded.phone, profile.phone),
            address=COALESCE(excluded.address, profile.address),
            linkedin=COALESCE(excluded.linkedin, profile.linkedin),
            website=COALESCE(excluded.website, profile.website),
            summary=COALESCE(excluded.summary, profile.summary),
            career_goals=COALESCE(excluded.career_goals, profile.career_goals)
        """,
        (full_name, email, phone, address, linkedin, website, summary, career_goals),
    )
    conn.commit()


def get_profile(conn) -> dict | None:
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return dict(row) if row else None


def add_experience(conn, company, role, location=None, start_date=None,
                    end_date=None, bullets=None) -> int:
    cur = conn.execute(
        """
        INSERT INTO experiences (company, role, location, start_date, end_date, bullets)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (company, role, location, start_date, end_date, json.dumps(bullets or [])),
    )
    conn.commit()
    return cur.lastrowid


def list_experiences(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM experiences ORDER BY start_date DESC"
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["bullets"] = json.loads(item["bullets"])
        result.append(item)
    return result


def add_education(conn, institution, degree=None, field=None, start_date=None,
                   end_date=None, details=None) -> int:
    cur = conn.execute(
        """
        INSERT INTO education (institution, degree, field, start_date, end_date, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (institution, degree, field, start_date, end_date, details),
    )
    conn.commit()
    return cur.lastrowid


def list_education(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM education ORDER BY start_date DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def add_skill(conn, name, category=None) -> int:
    cur = conn.execute(
        "INSERT INTO skills (name, category) VALUES (?, ?)",
        (name, category),
    )
    conn.commit()
    return cur.lastrowid


def list_skills(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM skills ORDER BY category, name").fetchall()
    return [dict(row) for row in rows]


def add_project(conn, name, url=None, bullets=None) -> int:
    cur = conn.execute(
        "INSERT INTO projects (name, url, bullets) VALUES (?, ?, ?)",
        (name, url, json.dumps(bullets or [])),
    )
    conn.commit()
    return cur.lastrowid


def list_projects(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM projects ORDER BY id").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["bullets"] = json.loads(item["bullets"])
        result.append(item)
    return result


def add_certification(conn, name, issuer=None, date=None) -> int:
    cur = conn.execute(
        "INSERT INTO certifications (name, issuer, date) VALUES (?, ?, ?)",
        (name, issuer, date),
    )
    conn.commit()
    return cur.lastrowid


def list_certifications(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM certifications ORDER BY date DESC"
    ).fetchall()
    return [dict(row) for row in rows]
