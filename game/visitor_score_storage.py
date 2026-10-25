"""
Save visitor quiz scores in SQLite.

Scores are separated by:
- RFID card UID
- quiz category

Database:
    data/visitor_scores.db
"""

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "visitor_scores.db"
)

# Create the data folder if it does not exist.
DB_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


def get_connection():
    """Open the SQLite database."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def create_table():
    """Create the scores table if it does not already exist."""

    with get_connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                card_uid   INTEGER NOT NULL,
                attempt    INTEGER NOT NULL,
                category   TEXT NOT NULL,
                score      INTEGER NOT NULL,
                scanned_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_scores_card_category
            ON scores (card_uid, category)
            """
        )

        db.commit()


def get_scores(card_uid, category):
    """
    Return scores for one RFID card and one category.

    Results are ordered from oldest to newest.
    """

    with get_connection() as db:
        rows = db.execute(
            """
            SELECT
                rowid,
                card_uid,
                attempt,
                category,
                score,
                scanned_at
            FROM scores
            WHERE card_uid = ?
              AND category = ?
            ORDER BY attempt ASC, rowid ASC
            """,
            (
                int(card_uid),
                str(category),
            ),
        ).fetchall()

    return [dict(row) for row in rows]


def get_latest_score(card_uid, category):
    """
    Return the latest saved result for one card and category.

    Call this before saving the current score to retrieve
    the latest previous score.
    """

    with get_connection() as db:
        row = db.execute(
            """
            SELECT
                rowid,
                card_uid,
                attempt,
                category,
                score,
                scanned_at
            FROM scores
            WHERE card_uid = ?
              AND category = ?
            ORDER BY attempt DESC, rowid DESC
            LIMIT 1
            """,
            (
                int(card_uid),
                str(category),
            ),
        ).fetchone()

    return dict(row) if row else None


def save_score(card_uid, category, score):
    """
    Save a score.

    Attempt numbers are counted separately for each category.
    """

    previous_scores = get_scores(
        card_uid,
        category
    )

    attempt = len(previous_scores) + 1

    scanned_at = (
        datetime.now()
        .astimezone()
        .isoformat(timespec="seconds")
    )

    with get_connection() as db:
        cursor = db.execute(
            """
            INSERT INTO scores (
                card_uid,
                attempt,
                category,
                score,
                scanned_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(card_uid),
                attempt,
                str(category),
                int(score),
                scanned_at,
            ),
        )

        db.commit()

    return {
        "rowid": cursor.lastrowid,
        "card_uid": int(card_uid),
        "attempt": attempt,
        "category": str(category),
        "score": int(score),
        "scanned_at": scanned_at,
    }


create_table()


if __name__ == "__main__":
    fake_uid = 3528472013
    test_category = "title"

    previous_result = get_latest_score(
        fake_uid,
        test_category
    )

    current_result = save_score(
        fake_uid,
        test_category,
        4
    )

    print("Previous result:", previous_result)
    print("Current result:", current_result)
