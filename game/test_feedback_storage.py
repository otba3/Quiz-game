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
            "origin", 4, 6, 5, "ar", False, 93,
        )

        with closing(sqlite3.connect(self.database)) as db:
            row = db.execute(
                """SELECT category, score, question_count, rating, language,
                          score_saved, duration_seconds, created_at
                   FROM game_feedback WHERE id = ?""",
                (result["id"],),
            ).fetchone()

        self.assertEqual(row[:7], ("origin", 4, 6, 5, "ar", 0, 93))
        self.assertEqual(row[7], result["created_at"])
        self.assertTrue(result["created_at"])


if __name__ == "__main__":
    unittest.main()
