"""Save visitors' quiz scores in a small SQLite database, linked to their RFID card UID.


Points are awarded per card, category, and calendar day: the first quiz banks
its score, the second awards both scores, and the third awards half its score.
The fourth and later quizzes that day earn no points.
The database is one file: data/visitor_scores.db (created automatically).
Try it without the Pi or the reader:  python3 game/visitor_score_storage.py
"""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


# data/ folder at the project root, next to the question CSVs.
DB_PATH = Path(__file__).parent.parent / "data" / "visitor_scores.db"




def create_table():
    """Create the score and points tables the first time; keep existing data."""
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
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
                CREATE TABLE IF NOT EXISTS game_feedback (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    category         TEXT NOT NULL,
                    score            INTEGER NOT NULL,
                    question_count   INTEGER NOT NULL,
                    rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    language         TEXT NOT NULL,
                    score_saved      INTEGER NOT NULL CHECK (score_saved IN (0, 1)),
                    duration_seconds INTEGER NOT NULL,
                    created_at       TEXT NOT NULL
                )
            """)


def save_game_feedback(category, score, question_count, rating, language,
                       score_saved, duration_seconds):
    """Save an anonymous game rating and the context needed to interpret it."""
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            cursor = db.execute(
                """INSERT INTO game_feedback
                   (category, score, question_count, rating, language,
                    score_saved, duration_seconds, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (category, score, question_count, rating, language,
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




def save_score(card_uid, category, score):
    """Save a quiz score and return its attempt and points awarded."""
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
    return {
        "attempt": attempt,
        "first_score": first_score,
        "points_earned": points_earned,
        "quizzes_today": quizzes_today,
    }


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
