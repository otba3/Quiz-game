import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import visitor_score_storage as storage


class AccountCodeStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "accounts.db"
        self.db_path_patch = patch.object(storage, "DB_PATH", self.database)
        self.db_path_patch.start()
        storage.create_table()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_code_maps_to_a_stable_identity_and_saves_scores(self):
        identity = storage.get_or_create_account_identity("  visitor-123  ")
        repeated_identity = storage.get_or_create_account_identity("visitor-123")

        self.assertLess(identity, 0)
        self.assertEqual(repeated_identity, identity)
        storage.save_score(identity, "year", 2, ["year-1", "year-2"])
        self.assertEqual(storage.get_scores(identity, "year"), [2])

        with closing(sqlite3.connect(self.database)) as db:
            account = db.execute(
                "SELECT account_code FROM quiz_accounts WHERE id = ?",
                (-identity,),
            ).fetchone()
        self.assertEqual(account[0], "visitor-123")

    def test_different_codes_receive_separate_identities(self):
        first = storage.get_or_create_account_identity("visitor-1")
        second = storage.get_or_create_account_identity("visitor-2")

        self.assertNotEqual(first, second)

    def test_code_must_be_nonempty_and_at_most_128_characters(self):
        for invalid_code in ("", "  ", "x" * 129):
            with self.subTest(code=invalid_code):
                with self.assertRaises(ValueError):
                    storage.get_or_create_account_identity(invalid_code)


if __name__ == "__main__":
    unittest.main()
