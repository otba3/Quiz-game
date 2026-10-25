"""Save visitors' quiz scores in a small SQLite database, linked to their RFID card UID.


Every attempt is kept. The first attempt is the "before" score; any later
attempt is compared with it to show what the visitor learned.
The database is one file: data/visitor_scores.db (created automatically).
Try it without the Pi or the reader:  python3 game/visitor_score_storage.py
"""
import sqlite3
from datetime import datetime
from pathlib import Path


# data/ folder at the project root, next to the question CSVs.
DB_PATH = Path(__file__).parent.parent / "data" / "visitor_scores.db"




def create_table():
    """Create the scores table the first time; does nothing if it already exists."""
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                card_uid   INTEGER,
                attempt    INTEGER,
                category   TEXT,
                score      INTEGER,
                scanned_at TEXT
            )
        """)




def get_scores(card_uid):
    """All saved scores for one card, oldest first, e.g. [5, 9]."""
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT score FROM scores WHERE card_uid = ? ORDER BY attempt",
            (card_uid,),
        ).fetchall()
    return [row[0] for row in rows]  # each row is a tuple like (5,)




def save_score(card_uid, category, score):
    """Save one attempt and return its number (1 = first visit, 2 = second, ...)."""
    attempt = len(get_scores(card_uid)) + 1
    now = datetime.now().isoformat(timespec="seconds")  # e.g. "2026-10-25T14:03:12"
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO scores (card_uid, attempt, category, score, scanned_at) VALUES (?, ?, ?, ?, ?)",
            (card_uid, attempt, category, score, now),
        )
    return attempt




if __name__ == "__main__":
    # Demo with a made-up UID: run it twice and watch the attempt number go up.
    create_table()
    fake_uid = 3528472013
    attempt = save_score(fake_uid, "title", 7)
    scores = get_scores(fake_uid)
    if attempt == 1:
        print(f"First attempt saved: {scores[0]}/12")
    else:
        print(f"Before: {scores[0]}/12 -> Now: {scores[-1]}/12 (attempt {attempt})")



