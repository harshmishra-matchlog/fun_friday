# ============================================================
# database.py — SQLite persistence layer
# ============================================================
import sqlite3
import json
import random
from datetime import date, datetime
from contextlib import contextmanager
from config import DB_PATH, MASTER_WORD_POOL, DEFAULT_WORDS_PER_PUZZLE
from puzzle_engine import generate_grid, grid_to_json, placements_to_json


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────
def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS puzzles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            week_date   TEXT UNIQUE,          -- ISO date of the Friday
            words       TEXT,                 -- JSON list of words
            grid        TEXT,                 -- JSON 2-D array
            placements  TEXT,                 -- JSON {word: [[r,c],...]}
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id   INTEGER REFERENCES puzzles(id),
            player_name TEXT,
            player_email TEXT,
            department  TEXT,
            start_time  TEXT,
            end_time    TEXT,
            found_words TEXT DEFAULT '[]',    -- JSON list
            score       INTEGER DEFAULT 0,
            time_taken  INTEGER DEFAULT 0,    -- seconds
            submitted   INTEGER DEFAULT 0     -- 0/1
        );

        CREATE TABLE IF NOT EXISTS admin_word_lists (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            week_date   TEXT UNIQUE,
            words       TEXT,
            added_by    TEXT,
            added_at    TEXT DEFAULT (datetime('now'))
        );
        """)


# ── Puzzle helpers ────────────────────────────────────────────
def _next_friday() -> str:
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7   # 4 = Friday
    if days_ahead == 0:
        days_ahead = 0                        # today IS Friday
    friday = today if days_ahead == 0 else __import__('datetime').date(
        today.year, today.month, today.day)
    from datetime import timedelta
    friday = today + timedelta(days=days_ahead)
    return friday.isoformat()


def get_or_create_puzzle(week_date: str | None = None) -> dict:
    """Return the puzzle for the given Friday (or today's Friday)."""
    if week_date is None:
        week_date = _next_friday()

    with get_conn() as conn:
        # ── FORCE DELETE old puzzle so new snake-engine runs ──
        # Remove this block after one successful deploy
        conn.execute("DELETE FROM puzzles WHERE week_date = ?", (week_date,))

        # Check if admin uploaded custom words for this week
        admin_row = conn.execute(
            "SELECT words FROM admin_word_lists WHERE week_date = ?", (week_date,)
        ).fetchone()

        if admin_row:
            words = json.loads(admin_row["words"])
        else:
            words = random.sample(MASTER_WORD_POOL, DEFAULT_WORDS_PER_PUZZLE)

        # Filter words that fit in grid
        from config import GRID_SIZE
        words = [w for w in words if len(w) <= GRID_SIZE][:DEFAULT_WORDS_PER_PUZZLE]

        grid, placements = generate_grid(words)

        conn.execute(
            """INSERT INTO puzzles (week_date, words, grid, placements)
               VALUES (?, ?, ?, ?)""",
            (week_date, json.dumps(words), grid_to_json(grid),
             placements_to_json(placements))
        )

        row = conn.execute(
            "SELECT * FROM puzzles WHERE week_date = ?", (week_date,)
        ).fetchone()
        return dict(row)


# ── Session helpers ───────────────────────────────────────────
def create_session(puzzle_id: int, name: str, email: str, dept: str) -> int:
    now = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO sessions
               (puzzle_id, player_name, player_email, department, start_time)
               VALUES (?, ?, ?, ?, ?)""",
            (puzzle_id, name, email, dept, now)
        )
        return cur.lastrowid


def get_session(session_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None


def update_found_words(session_id: int, found_words: list[str]):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET found_words = ?, score = ? WHERE id = ?",
            (json.dumps(found_words), len(found_words), session_id)
        )


def submit_session(session_id: int, found_words: list[str]):
    now = datetime.now().isoformat()
    sess = get_session(session_id)
    if not sess:
        return
    start = datetime.fromisoformat(sess["start_time"])
    time_taken = int((datetime.now() - start).total_seconds())
    with get_conn() as conn:
        conn.execute(
            """UPDATE sessions
               SET end_time=?, found_words=?, score=?, time_taken=?, submitted=1
               WHERE id=?""",
            (now, json.dumps(found_words), len(found_words), time_taken, session_id)
        )


def already_played(puzzle_id: int, email: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM sessions WHERE puzzle_id=? AND player_email=? AND submitted=1",
            (puzzle_id, email)
        ).fetchone()
        return row is not None


# ── Leaderboard ───────────────────────────────────────────────
def get_leaderboard(puzzle_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT player_name, player_email, department,
                      score, time_taken, end_time
               FROM sessions
               WHERE puzzle_id=? AND submitted=1
               ORDER BY score DESC, time_taken ASC""",
            (puzzle_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_puzzles() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM puzzles ORDER BY week_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_sessions(puzzle_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE puzzle_id=? AND submitted=1",
            (puzzle_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Admin: upload custom word list ───────────────────────────
def save_admin_word_list(week_date: str, words: list[str], admin_email: str):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO admin_word_lists (week_date, words, added_by)
               VALUES (?, ?, ?)
               ON CONFLICT(week_date) DO UPDATE
               SET words=excluded.words, added_by=excluded.added_by,
                   added_at=datetime('now')""",
            (week_date, json.dumps(words), admin_email)
        )
        # Also delete existing puzzle so it gets regenerated
        conn.execute("DELETE FROM puzzles WHERE week_date=?", (week_date,))


def regenerate_puzzle(week_date: str, admin_email: str) -> dict:
    with get_conn() as conn:
        conn.execute("DELETE FROM puzzles WHERE week_date=?", (week_date,))
    return get_or_create_puzzle(week_date)
