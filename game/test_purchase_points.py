import base64
import importlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import visitor_score_storage as storage


class PurchasePointsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path_patch = patch.object(
            storage, "DB_PATH", Path(cls.temp_dir.name) / "purchase-points.db",
        )
        cls.db_path_patch.start()
        storage.create_table()
        cls.app_module = importlib.import_module("app")
        cls.client = cls.app_module.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.db_path_patch.stop()
        cls.temp_dir.cleanup()

    def setUp(self):
        storage.create_table()

    def test_paid_purchase_issues_qr_claim_for_each_complete_ten_qar(self):
        result = storage.create_purchase_point_claim(3999, "receipt-001")

        self.assertEqual(result["points_earned"], 3)
        self.assertEqual(result["status"], "pending")
        self.assertTrue(result["claim_code"].startswith(storage.PURCHASE_CLAIM_PREFIX))
        with closing(sqlite3.connect(storage.DB_PATH)) as db:
            row = db.execute(
                """SELECT claim_token_hash, amount_minor, points, status
                   FROM purchase_point_claims WHERE purchase_reference = ?""",
                ("receipt-001",),
            ).fetchone()
        self.assertNotEqual(row[0], result["claim_code"])
        self.assertEqual(row[1:], (3999, 3, "pending"))

    def test_purchase_under_ten_qar_creates_no_claim_code(self):
        result = storage.create_purchase_point_claim(999, "receipt-002")

        self.assertEqual(result["points_earned"], 0)
        self.assertIsNone(result["claim_code"])
        self.assertEqual(result["status"], "not_eligible")

    def test_purchase_reference_cannot_issue_more_than_one_claim(self):
        storage.create_purchase_point_claim(2500, "receipt-003")

        with self.assertRaises(storage.PurchaseReferenceAlreadyUsed):
            storage.create_purchase_point_claim(3000, "receipt-003")

        with closing(sqlite3.connect(storage.DB_PATH)) as db:
            count = db.execute(
                """SELECT COUNT(*) FROM purchase_point_claims
                   WHERE purchase_reference = ?""",
                ("receipt-003",),
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_staff_api_creates_qr_claim_from_paid_purchase(self):
        with patch.dict("os.environ", {"PURCHASE_POINTS_STAFF_TOKEN": "test-secret"}):
            response = self.client.post(
                "/api/purchase/earn",
                json={
                    "amount_qar": "39.99",
                    "purchase_reference": "receipt-004",
                    "paid": True,
                },
                headers={"X-Staff-Token": "test-secret"},
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["points_earned"], 3)
        self.assertEqual(result["status"], "pending")
        self.assertTrue(
            result["claim_code"].startswith(storage.PURCHASE_CLAIM_PREFIX)
        )
        self.assertTrue(result["qr_image"].startswith("data:image/png;base64,"))
        image_bytes = base64.b64decode(result["qr_image"].split(",", 1)[1])
        with Image.open(BytesIO(image_bytes)) as qr_image:
            self.assertEqual(qr_image.format, "PNG")
            self.assertGreater(qr_image.width, 0)

    def test_staff_api_does_not_issue_claim_when_purchase_is_not_paid(self):
        with patch.dict("os.environ", {"PURCHASE_POINTS_STAFF_TOKEN": "test-secret"}):
            response = self.client.post(
                "/api/purchase/earn",
                json={
                    "amount_qar": "39.99",
                    "purchase_reference": "receipt-unpaid",
                    "paid": False,
                },
                headers={"X-Staff-Token": "test-secret"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Payment must be confirmed", response.get_json()["error"])
        with closing(sqlite3.connect(storage.DB_PATH)) as db:
            count = db.execute(
                """SELECT COUNT(*) FROM purchase_point_claims
                   WHERE purchase_reference = ?""",
                ("receipt-unpaid",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_staff_api_requires_configured_staff_token(self):
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.post("/api/purchase/earn")

        self.assertEqual(response.status_code, 503)

    def test_staff_api_rejects_invalid_staff_token(self):
        with patch.dict("os.environ", {"PURCHASE_POINTS_STAFF_TOKEN": "test-secret"}):
            response = self.client.post(
                "/api/purchase/earn",
                headers={"X-Staff-Token": "wrong-token"},
            )

        self.assertEqual(response.status_code, 401)

    def test_staff_api_rejects_amounts_that_are_not_qatari_riyal_values(self):
        with patch.dict("os.environ", {"PURCHASE_POINTS_STAFF_TOKEN": "test-secret"}):
            response = self.client.post(
                "/api/purchase/earn",
                json={
                    "amount_qar": "10.001",
                    "purchase_reference": "receipt-005",
                    "paid": True,
                },
                headers={"X-Staff-Token": "test-secret"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("amount_qar", response.get_json()["error"])

    def test_cashier_page_is_served(self):
        response = self.client.get("/cashier")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Has the customer paid?", response.data)
        self.assertIn(b"Staff access token", response.data)
        self.assertIn(b'value="presentation-test"', response.data)
        response.close()

    def test_staff_api_rejects_duplicate_purchase_reference(self):
        payload = {
            "amount_qar": "20.00",
            "purchase_reference": "receipt-006",
            "paid": True,
        }
        headers = {"X-Staff-Token": "test-secret"}
        with patch.dict("os.environ", {"PURCHASE_POINTS_STAFF_TOKEN": "test-secret"}):
            first = self.client.post("/api/purchase/earn", json=payload, headers=headers)
            duplicate = self.client.post(
                "/api/purchase/earn", json=payload, headers=headers,
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(duplicate.status_code, 409)


if __name__ == "__main__":
    unittest.main()
