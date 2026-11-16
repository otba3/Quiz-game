import re
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

    def test_created_account_code_maps_to_a_stable_identity_and_saves_scores(self):
        identity, account_code, display_name = storage.create_account("  Sam  ")
        repeated_identity = storage.get_account_identity(account_code.lower())

        self.assertRegex(account_code, re.compile(r"^[A-Z0-9]{6}$"))
        self.assertLess(identity, 0)
        self.assertEqual(repeated_identity, identity)
        self.assertEqual(display_name, "Sam")
        storage.save_score(identity, "year", 2, ["year-1", "year-2"])
        self.assertEqual(storage.get_scores(identity, "year"), [2])

        with closing(sqlite3.connect(self.database)) as db:
            account = db.execute(
                "SELECT account_code, display_name FROM quiz_accounts WHERE id = ?",
                (-identity,),
            ).fetchone()
        self.assertEqual(account, (account_code, "Sam"))

    def test_different_codes_receive_separate_identities(self):
        first, _, _ = storage.create_account("First")
        second, _, _ = storage.create_account("Second")

        self.assertNotEqual(first, second)

    def test_display_names_are_unique_case_insensitively_after_trimming(self):
        storage.create_account("Sam")

        with self.assertRaisesRegex(ValueError, "already in use"):
            storage.create_account("  sam  ")

        with closing(sqlite3.connect(self.database)) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM quiz_accounts"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_unknown_codes_do_not_create_accounts(self):
        with self.assertRaisesRegex(ValueError, "was not found"):
            storage.get_account_identity("ABC234")

        with closing(sqlite3.connect(self.database)) as db:
            count = db.execute("SELECT COUNT(*) FROM quiz_accounts").fetchone()[0]
        self.assertEqual(count, 0)

    def test_existing_visitor_code_cannot_be_used_as_admin_code(self):
        _, code, _ = storage.create_account("Visitor")
        with patch.object(storage, "ADMIN_ACCOUNT_CODE", code):
            with self.assertRaisesRegex(ValueError, "conflicts"):
                storage.create_table()
        self.assertLess(storage.get_account_identity(code), 0)

    def test_display_name_must_be_nonempty_and_at_most_40_characters(self):
        for invalid_name in ("", "  ", "x" * 41):
            with self.subTest(name=invalid_name):
                with self.assertRaises(ValueError):
                    storage.create_account(invalid_name)

    def test_legacy_account_codes_remain_usable(self):
        with closing(sqlite3.connect(self.database)) as db:
            db.execute(
                """INSERT INTO quiz_accounts
                   (account_code, created_at) VALUES (?, ?)""",
                ("visitor-123", "2026-01-01T00:00:00"),
            )
            db.commit()

        identity = storage.get_account_identity("visitor-123")
        self.assertLess(identity, 0)
        self.assertRegex(storage.visitor_label(identity), r"Visitor [0-9A-F]{8}")

    def test_schema_upgrade_preserves_existing_accounts(self):
        with closing(sqlite3.connect(self.database)) as db:
            db.execute("DROP TABLE quiz_accounts")
            db.execute("""
                CREATE TABLE quiz_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_code TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute(
                """INSERT INTO quiz_accounts (account_code, created_at)
                   VALUES (?, ?)""",
                ("old-code", "2026-01-01T00:00:00"),
            )
            db.commit()

        storage.create_table()

        self.assertLess(storage.get_account_identity("old-code"), 0)
        with closing(sqlite3.connect(self.database)) as db:
            account = db.execute(
                """SELECT account_code, display_name
                   FROM quiz_accounts WHERE account_code = ?""",
                ("old-code",),
            ).fetchone()
        self.assertEqual(account, ("old-code", ""))


if __name__ == "__main__":
    unittest.main()
