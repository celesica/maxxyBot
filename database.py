"""
database.py
All SQLite access for Maxxy lives here. Nothing in cogs/ should write raw SQL directly —
everything goes through these functions so the schema only has to be understood in one place.
"""

import sqlite3
import datetime
from contextlib import contextmanager

DB_PATH = "maxxy.db"


def init_db():
    """Create tables if they don't already exist. Safe to call every time the bot starts."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                discord_id   TEXT PRIMARY KEY,
                username     TEXT NOT NULL,
                goal_counter INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS goals (
                goal_id                TEXT PRIMARY KEY,
                discord_id              TEXT NOT NULL,
                title                   TEXT NOT NULL,
                description             TEXT NOT NULL,
                timeline                TEXT,
                status                  TEXT NOT NULL DEFAULT 'active',
                created_at              TEXT NOT NULL,
                last_checkin_at         TEXT,
                last_reminder_threshold INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (discord_id) REFERENCES users (discord_id)
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id         TEXT NOT NULL,
                discord_id      TEXT NOT NULL,
                event_type      TEXT NOT NULL,
                update_text     TEXT,
                attachment_url  TEXT,
                posted_at       TEXT NOT NULL,
                related_admin_id TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
            );

            CREATE INDEX IF NOT EXISTS idx_goals_status ON goals (status);
            CREATE INDEX IF NOT EXISTS idx_events_goal_id ON events (goal_id);
            """
        )


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


# ---------- users ----------

def ensure_user(discord_id: str, username: str):
    """Insert the user if they don't exist yet; keep username fresh if they do."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (discord_id, username, goal_counter)
            VALUES (?, ?, 0)
            ON CONFLICT(discord_id) DO UPDATE SET username = excluded.username
            """,
            (discord_id, username),
        )


def next_goal_number(discord_id: str) -> int:
    """Increment and return this user's goal counter (used to build goal_id)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET goal_counter = goal_counter + 1 WHERE discord_id = ?",
            (discord_id,),
        )
        row = conn.execute(
            "SELECT goal_counter FROM users WHERE discord_id = ?", (discord_id,)
        ).fetchone()
        return row["goal_counter"]


# ---------- goals ----------

def create_goal(goal_id, discord_id, title, description, timeline):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO goals (goal_id, discord_id, title, description, timeline,
                                status, created_at, last_checkin_at, last_reminder_threshold)
            VALUES (?, ?, ?, ?, ?, 'active', ?, NULL, 0)
            """,
            (goal_id, discord_id, title, description, timeline, ts),
        )
        conn.execute(
            """
            INSERT INTO events (goal_id, discord_id, event_type, posted_at)
            VALUES (?, ?, 'started', ?)
            """,
            (goal_id, discord_id, ts),
        )


def get_goal(goal_id: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM goals WHERE goal_id = ?", (goal_id,)
        ).fetchone()


def get_user_goals(discord_id: str, status: str = None):
    with get_conn() as conn:
        if status:
            return conn.execute(
                "SELECT * FROM goals WHERE discord_id = ? AND status = ? ORDER BY created_at",
                (discord_id, status),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM goals WHERE discord_id = ? ORDER BY created_at",
            (discord_id,),
        ).fetchall()


def get_all_active_goals():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM goals WHERE status = 'active' ORDER BY discord_id, created_at"
        ).fetchall()


def add_checkin(goal_id, discord_id, update_text, attachment_url):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO events (goal_id, discord_id, event_type, update_text,
                                 attachment_url, posted_at)
            VALUES (?, ?, 'checkin', ?, ?, ?)
            """,
            (goal_id, discord_id, update_text, attachment_url, ts),
        )
        # reset the clock: fresh check-in means no reminder is owed
        conn.execute(
            """
            UPDATE goals
            SET last_checkin_at = ?, last_reminder_threshold = 0
            WHERE goal_id = ?
            """,
            (ts, goal_id),
        )
    return ts


def mark_verified(goal_id, admin_discord_id):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO events (goal_id, discord_id, event_type, posted_at, related_admin_id)
            VALUES (?, (SELECT discord_id FROM goals WHERE goal_id = ?), 'verified', ?, ?)
            """,
            (goal_id, goal_id, ts, admin_discord_id),
        )


def mark_achieved(goal_id, admin_discord_id):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute("UPDATE goals SET status = 'achieved' WHERE goal_id = ?", (goal_id,))
        conn.execute(
            """
            INSERT INTO events (goal_id, discord_id, event_type, posted_at, related_admin_id)
            VALUES (?, (SELECT discord_id FROM goals WHERE goal_id = ?), 'achieved', ?, ?)
            """,
            (goal_id, goal_id, ts, admin_discord_id),
        )


def set_status(goal_id, discord_id, new_status, event_type):
    """Used for pause / resume / abandon. event_type should match new_status's verb form."""
    ts = now_iso()
    with get_conn() as conn:
        conn.execute("UPDATE goals SET status = ? WHERE goal_id = ?", (new_status, goal_id))
        if new_status == "active":  # resuming clears the clock, same as a fresh check-in
            conn.execute(
                "UPDATE goals SET last_reminder_threshold = 0, last_checkin_at = ? WHERE goal_id = ?",
                (ts, goal_id),
            )
        conn.execute(
            """
            INSERT INTO events (goal_id, discord_id, event_type, posted_at)
            VALUES (?, ?, ?, ?)
            """,
            (goal_id, discord_id, event_type, ts),
        )


def log_reminder(goal_id, discord_id, threshold):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE goals SET last_reminder_threshold = ? WHERE goal_id = ?",
            (threshold, goal_id),
        )
        conn.execute(
            """
            INSERT INTO events (goal_id, discord_id, event_type, update_text, posted_at)
            VALUES (?, ?, 'reminder_sent', ?, ?)
            """,
            (goal_id, discord_id, f"threshold={threshold}", ts),
        )


def get_goal_timeline(goal_id: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM events WHERE goal_id = ? ORDER BY posted_at", (goal_id,)
        ).fetchall()
