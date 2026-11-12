import unittest
from unittest.mock import patch

import app as server


class LeaderboardApiTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_demo_mode_adds_five_ranked_users_without_saving_them(self):
        real_entries = [{"player": "Real Visitor", "score": 4}]
        with (
            patch.object(server, "get_leaderboard", return_value=real_entries),
            patch.object(server, "LEADERBOARD_DEMO_MODE", True),
        ):
            response = self.client.get(
                "/api/leaderboard?category=year&period=daily"
            )

        entries = response.get_json()["entries"]
        self.assertEqual(len(entries), 6)
        self.assertEqual([entry["score"] for entry in entries], [11, 9, 7, 5, 4, 3])
        self.assertEqual(
            sum(entry["player"].startswith("Demo Visitor ") for entry in entries),
            5,
        )
        self.assertEqual(real_entries, [{"player": "Real Visitor", "score": 4}])

    def test_demo_mode_can_be_disabled(self):
        real_entries = [{"player": "Real Visitor", "score": 4}]
        with (
            patch.object(server, "get_leaderboard", return_value=real_entries),
            patch.object(server, "LEADERBOARD_DEMO_MODE", False),
        ):
            response = self.client.get(
                "/api/leaderboard?category=year&period=daily"
            )

        self.assertEqual(response.get_json()["entries"], real_entries)

    def test_saved_quiz_response_uses_the_supplied_account_code(self):
        account_identity = -7
        with (
            patch.object(
                server, "get_or_create_account_identity",
                return_value=account_identity,
            ),
            patch.object(server, "save_score", return_value={"attempt": 1}),
            patch.object(server, "get_points_balance", return_value=0),
            patch.object(server, "get_points_history", return_value=[]),
        ):
            response = self.client.post(
                "/api/account/save",
                json={
                    "account_code": "VISITOR-123",
                    "category": "year",
                    "score": 1,
                    "correct_question_ids": ["year-question"],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["visitor"], server.visitor_label(account_identity)
        )

    def test_account_score_rejects_empty_account_code(self):
        with patch.object(
            server,
            "get_or_create_account_identity",
            side_effect=ValueError("Account code cannot be empty"),
        ) as get_identity:
            response = self.client.post(
                "/api/account/save",
                json={
                    "account_code": "  ",
                    "category": "year",
                    "score": 0,
                    "correct_question_ids": [],
                },
            )

        self.assertEqual(response.status_code, 400)
        get_identity.assert_called_once_with("  ")

    def test_qr_cashier_page_and_purchase_endpoint_are_removed(self):
        cashier_response = self.client.get("/cashier")
        purchase_response = self.client.post("/api/purchase/earn", json={})

        self.assertEqual(cashier_response.status_code, 404)
        self.assertEqual(purchase_response.status_code, 404)

    def test_rfid_score_endpoint_is_removed(self):
        response = self.client.post("/api/card/save", json={})

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
