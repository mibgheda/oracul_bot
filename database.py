import sqlite3
from contextlib import contextmanager
from typing import Optional

from config import DB_PATH

SCHEDULE_OPTIONS = ["07:00", "10:00", "14:00", "18:00"]


def init_db() -> None:
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id        INTEGER PRIMARY KEY,
                username       TEXT,
                first_name     TEXT,
                consent_given  INTEGER NOT NULL DEFAULT 0,
                disclaimer_ok  INTEGER NOT NULL DEFAULT 0,
                gender         TEXT,
                utc_offset     INTEGER,
                welcomed       INTEGER NOT NULL DEFAULT 0,
                schedule_time  TEXT,
                schedule_set   INTEGER NOT NULL DEFAULT 0,
                last_pred_date TEXT,
                is_deleted     INTEGER NOT NULL DEFAULT 0,
                created_at     TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_thread_variants (
                user_id       INTEGER NOT NULL,
                thread_name   TEXT NOT NULL,
                variant_index INTEGER NOT NULL,
                received_date TEXT NOT NULL,
                PRIMARY KEY (user_id, thread_name, variant_index)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_knots (
                user_id     INTEGER NOT NULL,
                knot_id     TEXT NOT NULL,
                knot_type   TEXT NOT NULL,
                knot_name   TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                PRIMARY KEY (user_id, knot_id)
            )
        """)
        for col, definition in [
            ("utc_offset", "INTEGER"),
            ("gender", "TEXT"),
            ("welcomed", "INTEGER DEFAULT 0"),
            ("display_name", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            except Exception:
                pass


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_or_create_user(user_id: int, username: str, first_name: str) -> sqlite3.Row:
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if user is None:
            conn.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username or "", first_name or ""),
            )
        else:
            conn.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (username or "", first_name or "", user_id),
            )
    return get_user(user_id)


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()


def set_consent(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET consent_given = 1, is_deleted = 0 WHERE user_id = ?",
            (user_id,),
        )


def set_disclaimer_ok(user_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE users SET disclaimer_ok = 1 WHERE user_id = ?", (user_id,))


def set_gender(user_id: int, gender: str) -> None:
    with get_db() as conn:
        conn.execute("UPDATE users SET gender = ? WHERE user_id = ?", (gender, user_id))


def set_timezone(user_id: int, utc_offset_minutes: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET utc_offset = ? WHERE user_id = ?",
            (utc_offset_minutes, user_id),
        )


def set_display_name(user_id: int, name: str) -> None:
    with get_db() as conn:
        conn.execute("UPDATE users SET display_name = ? WHERE user_id = ?", (name, user_id))


def set_welcomed(user_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE users SET welcomed = 1 WHERE user_id = ?", (user_id,))


def set_schedule(user_id: int, schedule_time: Optional[str]) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET schedule_time = ?, schedule_set = 1 WHERE user_id = ?",
            (schedule_time, user_id),
        )


def record_prediction(user_id: int, date_str: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_pred_date = ? WHERE user_id = ?",
            (date_str, user_id),
        )


def delete_user(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            """UPDATE users SET
               is_deleted = 1,
               consent_given = 0,
               disclaimer_ok = 0,
               gender = NULL,
               utc_offset = NULL,
               welcomed = 0,
               schedule_time = NULL,
               schedule_set = 0
               WHERE user_id = ?""",
            (user_id,),
        )


def get_all_scheduled_users() -> list:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE schedule_time IS NOT NULL AND is_deleted = 0"
        ).fetchall()


def get_all_active_users() -> list:
    with get_db() as conn:
        return conn.execute(
            """SELECT * FROM users
               WHERE is_deleted = 0
                 AND consent_given = 1
                 AND disclaimer_ok = 1""",
        ).fetchall()


def get_stats() -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_deleted = 0 AND consent_given = 1"
        ).fetchone()[0]
        deleted = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_deleted = 1"
        ).fetchone()[0]
        schedule_rows = conn.execute(
            """SELECT schedule_time, COUNT(*) as cnt
               FROM users
               WHERE schedule_time IS NOT NULL AND is_deleted = 0
               GROUP BY schedule_time ORDER BY schedule_time"""
        ).fetchall()
        no_schedule = conn.execute(
            """SELECT COUNT(*) FROM users
               WHERE schedule_time IS NULL AND schedule_set = 1 AND is_deleted = 0"""
        ).fetchone()[0]

        from datetime import date
        today = date.today().isoformat()
        predictions_today = conn.execute(
            "SELECT COUNT(*) FROM users WHERE last_pred_date = ?", (today,)
        ).fetchone()[0]

    return {
        "total": total,
        "active": active,
        "deleted": deleted,
        "schedule_breakdown": {row["schedule_time"]: row["cnt"] for row in schedule_rows},
        "no_schedule": no_schedule,
        "predictions_today": predictions_today,
    }


# ─── Thread variant tracking ──────────────────────────────────────────────────

def get_user_variants(user_id: int) -> dict:
    """Return {thread_name: [variant_index, ...]} for all received variants."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT thread_name, variant_index FROM user_thread_variants WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    result: dict = {}
    for row in rows:
        result.setdefault(row["thread_name"], []).append(row["variant_index"])
    return result


def record_thread_variant(user_id: int, thread_name: str, variant_index: int, date: str) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO user_thread_variants
               (user_id, thread_name, variant_index, received_date) VALUES (?, ?, ?, ?)""",
            (user_id, thread_name, variant_index, date),
        )


# ─── Knot tracking ────────────────────────────────────────────────────────────

def get_user_knots(user_id: int) -> list:
    with get_db() as conn:
        return conn.execute(
            "SELECT knot_id, knot_type, knot_name FROM user_knots WHERE user_id = ? ORDER BY unlocked_at",
            (user_id,),
        ).fetchall()


def record_knot(user_id: int, knot_id: str, knot_type: str, knot_name: str, date: str) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO user_knots
               (user_id, knot_id, knot_type, knot_name, unlocked_at) VALUES (?, ?, ?, ?, ?)""",
            (user_id, knot_id, knot_type, knot_name, date),
        )
