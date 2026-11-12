"""Store quiz scores and account identifiers in SQLite.

Quiz points are awarded per account, category, and calendar day.
The database is one file: data/visitor_scores.db (created automatically).
Try it without the Pi:  python3 game/visitor_score_storage.py
"""
import hashlib
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


# data/ folder at the project root, next to the question CSVs.
DB_PATH = Path(__file__).parent.parent / "data" / "visitor_scores.db"


def create_table():
    """Create the account, score, and feedback tables; keep existing data."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS quiz_accounts (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_code TEXT NOT NULL UNIQUE,
                    created_at   TEXT NOT NULL
                )
            """)
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


def get_or_create_account_identity(account_code):
    """Map a code to a stable negative ID, separate from positive RFID IDs."""
    if not isinstance(account_code, str):
        raise ValueError("Account code is required")
    account_code = account_code.strip()
    if not account_code:
        raise ValueError("Account code cannot be empty")
    if len(account_code) > 128:
        raise ValueError("Account code cannot exceed 128 characters")

    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT id FROM quiz_accounts WHERE account_code = ?",
                (account_code,),
            ).fetchone()
            if row is None:
                cursor = db.execute(
                    """INSERT INTO quiz_accounts (account_code, created_at)
                       VALUES (?, ?)""",
                    (account_code, created_at),
                )
                account_id = cursor.lastrowid
            else:
                account_id = row[0]
    return -account_id


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
                points_earned = score // 2
            else:
                points_earned = 0

            db.execute(
                """INSERT INTO quiz_sessions
                   (card_uid, category, score, session_date, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (card_uid, category, score, session_date, now),
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
    return {
        "attempt": attempt,
        "first_score": first_score,
        "points_earned": points_earned,
        "quizzes_today": quizzes_today,
        "leaderboard_points_earned": leaderboard_points_earned,
        "leaderboard_score": leaderboard_score,
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
    """Return a stable public label without exposing the RFID card UID."""
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
