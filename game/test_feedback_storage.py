import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import visitor_score_storage as storage


class GameFeedbackStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "feedback.db"
        self.db_path_patch = patch.object(storage, "DB_PATH", self.database)
        self.db_path_patch.start()
        storage.create_table()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_saves_rating_with_game_context_and_timestamp(self):
        result = storage.save_game_feedback(
            "origin", 4, 5, "ar", False, 93,
        )

        with closing(sqlite3.connect(self.database)) as db:
            row = db.execute(
                """SELECT category, score, rating, language, score_saved,
                          duration_seconds, created_at
                   FROM game_feedback WHERE id = ?""",
                (result["id"],),
            ).fetchone()

        self.assertEqual(row[:6], ("origin", 4, 5, "ar", 0, 93))
        self.assertEqual(row[6], result["created_at"])
        self.assertTrue(result["created_at"])

    def test_removes_question_count_from_existing_table(self):
        with closing(sqlite3.connect(self.database)) as db:
            with db:
                db.execute("DROP TABLE game_feedback")
                db.execute("""
                    CREATE TABLE game_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        question_count INTEGER NOT NULL,
                        rating INTEGER NOT NULL,
                        language TEXT NOT NULL,
                        score_saved INTEGER NOT NULL,
                        duration_seconds INTEGER NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                db.execute(
                    """INSERT INTO game_feedback
                       (category, score, question_count, rating, language,
                        score_saved, duration_seconds, created_at)
                       VALUES ('year', 3, 6, 4, 'en', 1, 87,
                               '2026-11-08T10:00:00')"""
                )

        storage.create_table()

        with closing(sqlite3.connect(self.database)) as db:
            columns = {
                row[1] for row in db.execute("PRAGMA table_info(game_feedback)")
            }
            row = db.execute(
                """SELECT category, score, rating, language, score_saved,
                          duration_seconds, created_at
                   FROM game_feedback"""
            ).fetchone()

        self.assertNotIn("question_count", columns)
        self.assertEqual(
            row, ("year", 3, 4, "en", 1, 87, "2026-11-08T10:00:00")
        )


if __name__ == "__main__":
    unittest.main()
