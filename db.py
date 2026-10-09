"""
Lightweight persistence for consultations.

Every check is logged (anonymized -- no name/contact info is ever collected)
so the app can double as a small analytics project: severity distribution,
language usage, state-level trends. SQLite keeps this dependency-free for a
portfolio project; swapping in Postgres later is a one-line change via the
DB_PATH/connection string.
"""

import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager

DB_PATH = "consultations.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                state TEXT NOT NULL,
                language TEXT NOT NULL,
                symptom_text_english TEXT NOT NULL,
                severity TEXT NOT NULL,
                emergency INTEGER NOT NULL
            )
        """)
        conn.commit()


def log_consultation(state: str, language: str, symptom_text_english: str,
                      severity: str, emergency: bool):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO consultations
               (timestamp, state, language, symptom_text_english, severity, emergency)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                state,
                language,
                symptom_text_english,
                severity,
                int(emergency),
            ),
        )
        conn.commit()


def fetch_all_consultations():
    """Returns rows as a list of dicts, newest first. Used by the analytics view."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM consultations ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(r) for r in rows]
