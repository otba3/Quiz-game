"""Store quiz scores and account identifiers in SQLite.

Quiz points are awarded per account, category, and calendar day.
The database is one file: data/visitor_scores.db (created automatically).
Try it without the Pi:  python3 game/visitor_score_storage.py
"""
import hashlib
import os
import secrets
import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime
from pathlib import Path


# data/ folder at the project root, next to the question CSVs.
DB_PATH = Path(__file__).parent.parent / "data" / "visitor_scores.db"
ACCOUNT_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ACCOUNT_CODE_LENGTH = 6
MAX_DISPLAY_NAME_LENGTH = 40
ADMIN_ACCOUNT_CODE = os.environ.get("ADMIN_ACCOUNT_CODE", "adm1n1").strip().upper()
ADMIN_DISPLAY_NAME = os.environ.get("ADMIN_DISPLAY_NAME", "Admin").strip() or "Admin"

if (
    len(ADMIN_ACCOUNT_CODE) != ACCOUNT_CODE_LENGTH
    or not ADMIN_ACCOUNT_CODE.isascii()
    or not ADMIN_ACCOUNT_CODE.isalnum()
):
    raise ValueError("ADMIN_ACCOUNT_CODE must contain exactly six letters or digits")


def create_table():
    """Create the account, score, and feedback tables; keep existing data."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS quiz_accounts (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_code TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL DEFAULT '',
                    created_at   TEXT NOT NULL
                )
            """)
            account_columns = {
                row[1] for row in db.execute("PRAGMA table_info(quiz_accounts)")
            }
            if "display_name" not in account_columns:
                db.execute(
                    "ALTER TABLE quiz_accounts "
                    "ADD COLUMN display_name TEXT NOT NULL DEFAULT ''"
                )
            if db.execute(
                "SELECT 1 FROM quiz_accounts WHERE upper(account_code) = ?",
                (ADMIN_ACCOUNT_CODE,),
            ).fetchone():
                raise ValueError(
                    "ADMIN_ACCOUNT_CODE conflicts with an existing visitor account"
                )
            db.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    card_uid   INTEGER,
                    attempt    INTEGER,
                    category   TEXT,
                    score      INTEGER,
                    scanned_at TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS point_transactions (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_uid   INTEGER NOT NULL,
                    points     INTEGER NOT NULL,
                    category   TEXT NOT NULL,
                    kind       TEXT NOT NULL CHECK (kind IN ('earned', 'redeemed')),
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS quiz_sessions (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_uid     INTEGER NOT NULL,
                    category     TEXT NOT NULL,
                    score        INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    created_at   TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS daily_question_scores (
                    card_uid   INTEGER NOT NULL,
                    category   TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    session_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (card_uid, category, question_id, session_date)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS game_feedback (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    category         TEXT NOT NULL,
                    score            INTEGER NOT NULL,
                    rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    language         TEXT NOT NULL,
                    score_saved      INTEGER NOT NULL CHECK (score_saved IN (0, 1)),
                    duration_seconds INTEGER NOT NULL,
                    created_at       TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS visitor_play_sessions (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    category          TEXT NOT NULL,
                    score             INTEGER NOT NULL,
                    created_at        TEXT NOT NULL,
                    legacy_session_id INTEGER UNIQUE
                )
            """)
            play_session_columns = {
                row[1] for row in db.execute(
                    "PRAGMA table_info(visitor_play_sessions)"
                )
            }
            if "legacy_session_id" not in play_session_columns:
                db.execute(
                    "ALTER TABLE visitor_play_sessions "
                    "ADD COLUMN legacy_session_id INTEGER"
                )
            db.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    visitor_play_legacy_session_id
                ON visitor_play_sessions (legacy_session_id)
            """)
            db.execute("""
                INSERT OR IGNORE INTO visitor_play_sessions
                    (category, score, created_at, legacy_session_id)
                SELECT category, score, created_at, id
                FROM quiz_sessions
            """)
            columns = {
                row[1] for row in db.execute("PRAGMA table_info(game_feedback)")
            }
            if "question_count" in columns:
                db.execute("""
                    CREATE TABLE game_feedback_new (
                        id               INTEGER PRIMARY KEY AUTOINCREMENT,
                        category         TEXT NOT NULL,
                        score            INTEGER NOT NULL,
                        rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                        language         TEXT NOT NULL,
                        score_saved      INTEGER NOT NULL CHECK (score_saved IN (0, 1)),
                        duration_seconds INTEGER NOT NULL,
                        created_at       TEXT NOT NULL
                    )
                """)
                db.execute("""
                    INSERT INTO game_feedback_new
                    (id, category, score, rating, language, score_saved,
                     duration_seconds, created_at)
                    SELECT id, category, score, rating, language, score_saved,
                           duration_seconds, created_at
                    FROM game_feedback
                """)
                db.execute("DROP TABLE game_feedback")
                db.execute(
                    "ALTER TABLE game_feedback_new RENAME TO game_feedback"
                )


def create_account(display_name):
    """Create a named account with a unique, six-character entry code."""
    if not isinstance(display_name, str):
        raise ValueError("Display name is required")
    display_name = display_name.strip()
    if not display_name:
        raise ValueError("Display name cannot be empty")
    if len(display_name) > MAX_DISPLAY_NAME_LENGTH:
        raise ValueError(
            f"Display name cannot exceed {MAX_DISPLAY_NAME_LENGTH} characters"
        )
    if any(ord(character) < 32 or ord(character) == 127 for character in display_name):
        raise ValueError("Display name cannot contain control characters")

    created_at = datetime.now().isoformat(timespec="seconds")
    normalized_name = unicodedata.normalize("NFKC", display_name).casefold()
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            existing_names = db.execute(
                "SELECT display_name FROM quiz_accounts"
            ).fetchall()
            if any(
                unicodedata.normalize("NFKC", existing_name or "").casefold()
                == normalized_name
                for (existing_name,) in existing_names
            ):
                raise ValueError("Display name is already in use")
            for _ in range(100):
                account_code = "".join(
                    secrets.choice(ACCOUNT_CODE_ALPHABET)
                    for _ in range(ACCOUNT_CODE_LENGTH)
                )
                if account_code == ADMIN_ACCOUNT_CODE:
                    continue
                exists = db.execute(
                    "SELECT 1 FROM quiz_accounts WHERE upper(account_code) = ?",
                    (account_code,),
                ).fetchone()
                if exists:
                    continue
                cursor = db.execute(
                    """INSERT INTO quiz_accounts
                       (account_code, display_name, created_at)
                       VALUES (?, ?, ?)""",
                    (account_code, display_name, created_at),
                )
                return -cursor.lastrowid, account_code, display_name
    raise RuntimeError("Could not generate a unique account code")


def get_account_identity(account_code):
    """Look up an existing account code without creating an account."""
    if not isinstance(account_code, str):
        raise ValueError("Account code is required")
    account_code = account_code.strip()
    if not account_code:
        raise ValueError("Account code cannot be empty")
    if len(account_code) > 128:
        raise ValueError("Account code cannot exceed 128 characters")

    with closing(sqlite3.connect(DB_PATH)) as db:
        row = db.execute(
            """SELECT id FROM quiz_accounts
               WHERE account_code = ? OR
                     (length(account_code) = ? AND upper(account_code) = ?)
               ORDER BY CASE WHEN account_code = ? THEN 0 ELSE 1 END
               LIMIT 1""",
            (
                account_code,
                ACCOUNT_CODE_LENGTH,
                account_code.upper(),
                account_code,
            ),
        ).fetchone()
    if row is None:
        raise ValueError("Account code was not found")
    return -row[0]


def get_account_display_name(account_identity):
    """Return a stored display name for a local account identity."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        row = db.execute(
            "SELECT display_name FROM quiz_accounts WHERE id = ?",
            (-account_identity,),
        ).fetchone()
    return row[0] if row else ""


def save_game_feedback(category, score, rating, language, score_saved,
                       duration_seconds):
    """Save an anonymous game rating and the context needed to interpret it."""
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            cursor = db.execute(
                """INSERT INTO game_feedback
                   (category, score, rating, language, score_saved,
                    duration_seconds, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (category, score, rating, language,
                 int(score_saved), duration_seconds, created_at),
            )
            feedback_id = cursor.lastrowid
    return {"id": feedback_id, "created_at": created_at}


def record_visitor_play(category, score):
    """Record one completed quiz, including guest games, for kiosk statistics."""
    if category not in ("year", "origin"):
        raise ValueError("Invalid category")
    if type(score) is not int or not 0 <= score <= 6:
        raise ValueError("Score must be between 0 and 6")
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            cursor = db.execute(
                """INSERT INTO visitor_play_sessions
                   (category, score, created_at) VALUES (?, ?, ?)""",
                (category, score, created_at),
            )
    return {"id": cursor.lastrowid, "created_at": created_at}


def get_dashboard_statistics():
    """Return totals for completed quizzes, feedback, and their averages."""
    today = datetime.now().date().isoformat()
    with closing(sqlite3.connect(DB_PATH)) as db:
        feedback_count, average_rating = db.execute(
            """SELECT COUNT(*), AVG(rating) FROM game_feedback"""
        ).fetchone()
        player_count, players_today, average_score = db.execute(
            """SELECT COUNT(*),
                      SUM(CASE WHEN substr(created_at, 1, 10) = ? THEN 1 ELSE 0 END),
                      AVG(CASE WHEN score BETWEEN 0 AND 6 THEN score END)
               FROM visitor_play_sessions""",
            (today,),
        ).fetchone()
    return {
        "total_feedback": feedback_count,
        "players_since_beginning": player_count,
        "players_today": players_today or 0,
        "average_score": round(average_score, 1) if average_score is not None else None,
        "average_feedback_rating": (
            round(average_rating, 1) if average_rating is not None else None
        ),
    }


def get_score_comparisons():
    """Return anonymous first and second account attempts per category and day."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("""
            WITH ranked AS (
                SELECT s.category, s.session_date, s.score, s.created_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY s.card_uid, s.category, s.session_date
                           ORDER BY s.id
                       ) AS attempt, s.card_uid
                FROM quiz_sessions s
                JOIN quiz_accounts a ON a.id = -s.card_uid
            )
            SELECT category, session_date,
                   MAX(CASE WHEN attempt = 1 THEN score END) AS first_score,
                   MAX(CASE WHEN attempt = 2 THEN score END) AS second_score,
                   MAX(CASE WHEN attempt = 1 THEN created_at END) AS first_time,
                   MAX(CASE WHEN attempt = 2 THEN created_at END) AS second_time
            FROM ranked
            WHERE attempt <= 2
            GROUP BY card_uid, category, session_date
            ORDER BY session_date DESC, first_time DESC, category
        """).fetchall()
    return [dict(row) for row in rows]


def get_feedback_rating_counts():
    """Return the count for every rating, including ratings with no responses."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        rows = db.execute(
            "SELECT rating, COUNT(*) FROM game_feedback GROUP BY rating"
        ).fetchall()
    counts = dict(rows)
    return [{"rating": rating, "count": counts.get(rating, 0)}
            for rating in range(1, 6)]




MAX_ATTEMPTS = 2  # before + after the exhibition


def get_scores(card_uid, category):
    """Saved scores for one card in one category, oldest first, e.g. [5, 9]."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        rows = db.execute(
            "SELECT score FROM scores WHERE card_uid = ? AND category = ? ORDER BY attempt",
            (card_uid, category),
        ).fetchall()
    return [row[0] for row in rows]  # each row is a tuple like (5,)




def save_score(card_uid, category, score, correct_question_ids=()):
    """Save a quiz score and daily leaderboard points."""
    if not isinstance(correct_question_ids, (list, tuple)):
        raise ValueError("Correct question IDs must be a list")
    if len(correct_question_ids) > 12:
        raise ValueError("A quiz cannot have more than 12 correct questions")
    if any(
        not isinstance(question_id, str)
        or not question_id
        or len(question_id) > 200
        for question_id in correct_question_ids
    ):
        raise ValueError("Invalid correct question ID")
    question_ids = list(dict.fromkeys(correct_question_ids))
    current_time = datetime.now()
    now = current_time.isoformat(timespec="seconds")  # e.g. "2026-10-25T14:03:12"
    session_date = current_time.date().isoformat()
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            today_scores = db.execute(
                """SELECT score FROM quiz_sessions
                   WHERE card_uid = ? AND category = ? AND session_date = ?
                   ORDER BY id""",
                (card_uid, category, session_date),
            ).fetchall()
            daily_score = db.execute(
                """SELECT COUNT(*) FROM daily_question_scores
                   WHERE card_uid = ? AND category = ? AND session_date = ?""",
                (card_uid, category, session_date),
            ).fetchone()[0]
            remaining_daily_points = max(0, 12 - daily_score)
            leaderboard_points_earned = 0
            for question_id in question_ids:
                if remaining_daily_points == 0:
                    break
                cursor = db.execute(
                    """INSERT INTO daily_question_scores
                       (card_uid, category, question_id, session_date, created_at)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT (card_uid, category, question_id, session_date)
                       DO NOTHING""",
                    (card_uid, category, question_id, session_date, now),
                )
                if cursor.rowcount:
                    leaderboard_points_earned += 1
                    remaining_daily_points -= 1

            quizzes_today = len(today_scores) + 1
            if quizzes_today == 1:
                points_earned = 0
            elif quizzes_today == 2:
                points_earned = today_scores[0][0] + score
            elif quizzes_today == 3:
                points_earned = 0
            elif quizzes_today == 4:
                points_earned = (today_scores[2][0] + score) // 2
            else:
                points_earned = 0

            session_cursor = db.execute(
                """INSERT INTO quiz_sessions
                   (card_uid, category, score, session_date, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (card_uid, category, score, session_date, now),
            )
            db.execute(
                """INSERT INTO visitor_play_sessions
                   (category, score, created_at, legacy_session_id)
                   VALUES (?, ?, ?, ?)""",
                (category, score, now, session_cursor.lastrowid),
            )

            previous_scores = db.execute(
                "SELECT COUNT(*) FROM scores WHERE card_uid = ? AND category = ?",
                (card_uid, category),
            ).fetchone()[0]
            attempt = previous_scores + 1
            if attempt > MAX_ATTEMPTS:
                db.execute(
                    "DELETE FROM scores WHERE card_uid = ? AND category = ?",
                    (card_uid, category),
                )
                attempt = 1
            db.execute(
                "INSERT INTO scores (card_uid, attempt, category, score, scanned_at) VALUES (?, ?, ?, ?, ?)",
                (card_uid, attempt, category, score, now),
            )
            if points_earned:
                db.execute(
                    """INSERT INTO point_transactions
                       (card_uid, points, category, kind, created_at)
                       VALUES (?, ?, ?, 'earned', ?)""",
                    (card_uid, points_earned, category, now),
                )
            first_score = today_scores[0][0] if today_scores else score
            leaderboard_score = db.execute(
                """SELECT COUNT(*) FROM daily_question_scores
                   WHERE card_uid = ? AND category = ? AND session_date = ?""",
                (card_uid, category, session_date),
            ).fetchone()[0]
            average_score = db.execute(
                """SELECT AVG(score) * 2 FROM quiz_sessions
                   WHERE session_date = ?""",
                (session_date,),
            ).fetchone()[0]
    return {
        "attempt": attempt,
        "first_score": first_score,
        "points_earned": points_earned,
        "quizzes_today": quizzes_today,
        "leaderboard_points_earned": leaderboard_points_earned,
        "leaderboard_score": leaderboard_score,
        "average_score": average_score,
    }


def get_daily_average_score():
    """Return today's average across account-linked quiz attempts."""
    today = datetime.now().date().isoformat()
    with closing(sqlite3.connect(DB_PATH)) as db:
        average_score, visitor_count = db.execute(
            """SELECT AVG(score) * 2, COUNT(*) FROM quiz_sessions
               WHERE session_date = ?""",
            (today,),
        ).fetchone()
    return {
        "average_score": average_score,
        "visitor_count": visitor_count,
    }


def get_leaderboard(category, period):
    """Return anonymous scores for all visitors on today's or this month's board."""
    now = datetime.now()
    if period == "daily":
        with closing(sqlite3.connect(DB_PATH)) as db:
            rows = db.execute(
                """SELECT card_uid, COUNT(*) AS score
                   FROM daily_question_scores
                   WHERE category = ? AND session_date = ?
                   GROUP BY card_uid
                   ORDER BY score DESC, card_uid""",
                (category, now.date().isoformat()),
            ).fetchall()
    elif period == "monthly":
        with closing(sqlite3.connect(DB_PATH)) as db:
            rows = db.execute(
                """SELECT card_uid, SUM(score) AS score
                   FROM quiz_sessions
                   WHERE category = ? AND substr(session_date, 1, 7) = ?
                   GROUP BY card_uid
                   ORDER BY score DESC, card_uid""",
                (category, now.strftime("%Y-%m")),
            ).fetchall()
    else:
        raise ValueError("Invalid leaderboard period")

    return [
        {
            "player": visitor_label(card_uid),
            "score": score,
        }
        for card_uid, score in rows
    ]


def visitor_label(card_uid):
    """Return an account name or stable anonymous label without exposing its ID."""
    if card_uid < 0:
        display_name = get_account_display_name(card_uid)
        if display_name:
            return display_name
    return "Visitor " + hashlib.sha256(
        str(card_uid).encode("utf-8")
    ).hexdigest()[:8].upper()


def get_points_balance(card_uid):
    """Return the card's current points balance, including any redemptions."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        row = db.execute(
            "SELECT COALESCE(SUM(points), 0) FROM point_transactions WHERE card_uid = ?",
            (card_uid,),
        ).fetchone()
    return row[0]


def get_points_history(card_uid):
    """Return one card's point transactions, newest first."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            """SELECT points, category, kind, created_at
               FROM point_transactions WHERE card_uid = ?
               ORDER BY id DESC""",
            (card_uid,),
        ).fetchall()
    return [dict(row) for row in rows]




if __name__ == "__main__":
    # Demo with a made-up UID: run it 3 times and watch the attempt go 1, 2, then back to 1.
    create_table()
    fake_uid = 3528472013
    result = save_score(fake_uid, "title", 7)
    scores = get_scores(fake_uid, "title")
    if result["attempt"] == 1:
        print(f"First attempt saved: {scores[0]}/12")
    else:
        print(
            f"Before: {scores[0]}/12 -> Now: {scores[-1]}/12 "
            f"(attempt {result['attempt']})"
        )
