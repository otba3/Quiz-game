"""Store quiz scores and one-time purchase-point claims in SQLite.

Quiz points are awarded per RFID card, category, and calendar day. Purchase
points are issued as pending claims, one point per complete QAR 10.
The database is one file: data/visitor_scores.db (created automatically).
Try it without the Pi or the reader:  python3 game/visitor_score_storage.py
"""
import hashlib
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


# data/ folder at the project root, next to the question CSVs.
DB_PATH = Path(__file__).parent.parent / "data" / "visitor_scores.db"
PURCHASE_QR_PREFIX = "qm-points:"
PURCHASE_CLAIM_PREFIX = "qm-claim:"


class PurchaseReferenceAlreadyUsed(ValueError):
    """Raised when a paid receipt has already been issued as a points claim."""


def create_table():
    """Create the score, feedback, and purchase-claim tables; keep existing data."""
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
                    rating           INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    language         TEXT NOT NULL,
                    score_saved      INTEGER NOT NULL CHECK (score_saved IN (0, 1)),
                    duration_seconds INTEGER NOT NULL,
                    created_at       TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS purchase_points_accounts (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    qr_token_hash TEXT NOT NULL UNIQUE,
                    created_at    TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS purchase_points_transactions (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id        INTEGER NOT NULL
                                      REFERENCES purchase_points_accounts(id),
                    purchase_reference TEXT NOT NULL UNIQUE,
                    amount_minor      INTEGER NOT NULL CHECK (amount_minor > 0),
                    points            INTEGER NOT NULL CHECK (points >= 0),
                    created_at        TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS purchase_point_claims (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_reference TEXT NOT NULL UNIQUE,
                    claim_token_hash   TEXT UNIQUE,
                    amount_minor       INTEGER NOT NULL CHECK (amount_minor > 0),
                    points             INTEGER NOT NULL CHECK (points >= 0),
                    status             TEXT NOT NULL
                                       CHECK (status IN ('pending', 'claimed', 'not_eligible')),
                    created_at         TEXT NOT NULL,
                    claimed_at         TEXT,
                    claimed_by         TEXT
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


def _purchase_qr_hash(qr_code):
    """Validate a purchase-points QR payload and return its stored token hash."""
    if not isinstance(qr_code, str) or not qr_code.startswith(PURCHASE_QR_PREFIX):
        raise ValueError("Invalid purchase-points QR code")
    token = qr_code[len(PURCHASE_QR_PREFIX):]
    if not token:
        raise ValueError("Invalid purchase-points QR code")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_purchase_points_account():
    """Create a QR-backed purchase-points account and return its QR payload."""
    token = secrets.token_urlsafe(32)
    qr_code = PURCHASE_QR_PREFIX + token
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute(
                """INSERT INTO purchase_points_accounts
                   (qr_token_hash, created_at) VALUES (?, ?)""",
                (hashlib.sha256(token.encode("utf-8")).hexdigest(), created_at),
            )
    return {"qr_code": qr_code, "created_at": created_at}


def earn_purchase_points(qr_code, amount_minor, purchase_reference):
    """Credit whole points for a paid amount in dirhams; retries are idempotent."""
    if type(amount_minor) is not int or not 0 < amount_minor <= 2**63 - 1:
        raise ValueError("Purchase amount must be positive whole dirhams")
    if not isinstance(purchase_reference, str) or not purchase_reference.strip():
        raise ValueError("Purchase reference is required")
    if len(purchase_reference) > 128:
        raise ValueError("Purchase reference is too long")

    token_hash = _purchase_qr_hash(qr_code)
    points = amount_minor // 1000
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            account = db.execute(
                """SELECT id FROM purchase_points_accounts
                   WHERE qr_token_hash = ?""",
                (token_hash,),
            ).fetchone()
            if account is None:
                raise ValueError("Unknown purchase-points QR code")
            account_id = account[0]
            previous = db.execute(
                """SELECT account_id, amount_minor, points, created_at
                   FROM purchase_points_transactions
                   WHERE purchase_reference = ?""",
                (purchase_reference,),
            ).fetchone()
            if previous is not None:
                if previous[0] != account_id or previous[1] != amount_minor:
                    raise ValueError("Purchase reference was already used")
                return {
                    "points_earned": previous[2],
                    "points_balance": _purchase_points_balance(db, account_id),
                    "created_at": previous[3],
                    "already_processed": True,
                }

            db.execute(
                """INSERT INTO purchase_points_transactions
                   (account_id, purchase_reference, amount_minor, points, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (account_id, purchase_reference, amount_minor, points, created_at),
            )
            return {
                "points_earned": points,
                "points_balance": _purchase_points_balance(db, account_id),
                "created_at": created_at,
                "already_processed": False,
            }


def _purchase_points_balance(db, account_id):
    return db.execute(
        """SELECT COALESCE(SUM(points), 0)
           FROM purchase_points_transactions WHERE account_id = ?""",
        (account_id,),
    ).fetchone()[0]


def get_purchase_points_balance(qr_code):
    """Return a QR account's purchase-points balance."""
    token_hash = _purchase_qr_hash(qr_code)
    with closing(sqlite3.connect(DB_PATH)) as db:
        account = db.execute(
            """SELECT id FROM purchase_points_accounts
               WHERE qr_token_hash = ?""",
            (token_hash,),
        ).fetchone()
        if account is None:
            raise ValueError("Unknown purchase-points QR code")
        return _purchase_points_balance(db, account[0])


def create_purchase_point_claim(amount_minor, purchase_reference):
    """Issue a one-time QR claim for the points earned on a paid purchase."""
    if type(amount_minor) is not int or not 0 < amount_minor <= 2**63 - 1:
        raise ValueError("Purchase amount must be positive whole dirhams")
    if not isinstance(purchase_reference, str) or not purchase_reference.strip():
        raise ValueError("Purchase reference is required")
    if len(purchase_reference) > 128:
        raise ValueError("Purchase reference is too long")

    points = amount_minor // 1000
    created_at = datetime.now().isoformat(timespec="seconds")
    claim_code = (
        PURCHASE_CLAIM_PREFIX + secrets.token_urlsafe(32) if points else None
    )
    token_hash = None
    if claim_code:
        token = claim_code[len(PURCHASE_CLAIM_PREFIX):]
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    status = "pending" if claim_code else "not_eligible"

    with closing(sqlite3.connect(DB_PATH)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                """SELECT id FROM purchase_point_claims
                   WHERE purchase_reference = ?""",
                (purchase_reference,),
            ).fetchone()
            if previous is not None:
                raise PurchaseReferenceAlreadyUsed(
                    "Purchase reference has already been processed"
                )
            db.execute(
                """INSERT INTO purchase_point_claims
                   (purchase_reference, claim_token_hash, amount_minor, points,
                    status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (purchase_reference, token_hash, amount_minor, points, status, created_at),
            )
    return {
        "claim_code": claim_code,
        "points_earned": points,
        "status": status,
        "created_at": created_at,
    }


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
