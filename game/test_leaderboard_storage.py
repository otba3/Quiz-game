import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import visitor_score_storage as storage


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 10, 12, 0, 0)


class LeaderboardStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "leaderboard.db"
        self.db_path_patch = patch.object(storage, "DB_PATH", self.database)
        self.db_path_patch.start()
        self.datetime_patch = patch.object(storage, "datetime", FixedDateTime)
        self.datetime_patch.start()
        storage.create_table()

    def tearDown(self):
        self.datetime_patch.stop()
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_daily_score_counts_distinct_correct_questions_once(self):
        first = storage.save_score(1001, "year", 2, ["year-1", "year-2"])
        repeated = storage.save_score(1001, "year", 2, ["year-2", "year-3"])

        self.assertEqual(first["leaderboard_points_earned"], 2)
        self.assertEqual(repeated["leaderboard_points_earned"], 1)
        self.assertEqual(repeated["leaderboard_score"], 3)
        self.assertEqual(
            storage.get_leaderboard("year", "daily")[0]["score"], 3
        )

    def test_daily_score_is_capped_at_twelve(self):
        first_questions = [f"q-{number}" for number in range(1, 7)]
        next_questions = [f"q-{number}" for number in range(7, 13)]
        overflow_questions = ["q-13", "q-14"]
        storage.save_score(1001, "origin", 6, first_questions)
        storage.save_score(1001, "origin", 6, next_questions)

        overflow = storage.save_score(
            1001, "origin", 2, overflow_questions
        )

        self.assertEqual(overflow["leaderboard_points_earned"], 0)
        self.assertEqual(overflow["leaderboard_score"], 12)

    def test_monthly_score_sums_quiz_scores_and_uses_anonymous_names(self):
        storage.save_score(1001, "year", 4)
        storage.save_score(1001, "year", 5)
        storage.save_score(1002, "year", 7)
        storage.save_score(1001, "origin", 11)

        entries = storage.get_leaderboard("year", "monthly")

        self.assertEqual([entry["score"] for entry in entries], [9, 7])
        self.assertTrue(
            all(
                re.fullmatch(r"Visitor [0-9A-F]{8}", entry["player"])
                for entry in entries
            )
        )

    def test_scores_from_another_month_are_excluded(self):
        storage.save_score(1001, "year", 8)
        with patch.object(FixedDateTime, "now", return_value=datetime(2026, 10, 31)):
            storage.save_score(1001, "year", 6)

        self.assertEqual(
            storage.get_leaderboard("year", "monthly")[0]["score"], 8
        )

    def test_leaderboard_returns_all_visitors_for_scrollable_rankings(self):
        for card_uid in range(1001, 1014):
            storage.save_score(card_uid, "origin", 5)

        entries = storage.get_leaderboard("origin", "monthly")

        self.assertEqual(len(entries), 13)


if __name__ == "__main__":
    unittest.main()
