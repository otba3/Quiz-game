import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as server
import visitor_score_storage as storage


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

    def test_daily_average_endpoint_returns_account_scores_only(self):
        average = {"average_score": 3.5, "visitor_count": 2}
        with patch.object(server, "get_daily_average_score", return_value=average):
            response = self.client.get("/api/average/today")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), average)

    def test_saved_quiz_response_uses_the_supplied_account_code(self):
        account_identity = -7
        with (
            patch.object(
                server, "get_account_identity",
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
            "get_account_identity",
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

    def test_account_creation_returns_the_generated_code_and_display_name(self):
        with (
            patch.object(
                server,
                "create_account",
                return_value=(-7, "AB234C", "Sam"),
            ),
            patch.object(server, "visitor_label", return_value="Sam"),
        ):
            response = self.client.post(
                "/api/account/create", json={"display_name": "Sam"}
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json(),
            {
                "created": True,
                "account_code": "AB234C",
                "display_name": "Sam",
                "visitor": "Sam",
            },
        )

    def test_account_login_does_not_create_unknown_codes(self):
        with patch.object(
            server,
            "get_account_identity",
            side_effect=ValueError("Account code was not found"),
        ):
            response = self.client.post(
                "/api/account/login", json={"account_code": "ABC234"}
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Account code was not found"})

    def test_admin_code_logs_in_with_admin_role_without_creating_a_visitor(self):
        with (
            patch.object(server, "ADMIN_ACCOUNT_CODE", "ADMIN1"),
            patch.object(server, "ADMIN_DISPLAY_NAME", "Museum Admin"),
        ):
            response = self.client.post(
                "/api/account/login", json={"account_code": "admin1"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"valid": True, "role": "admin", "visitor": "Museum Admin"},
        )

    def test_non_ascii_account_code_does_not_cause_a_server_error(self):
        response = self.client.post(
            "/api/account/login", json={"account_code": "اختبار"}
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_dashboard_requires_the_configured_admin_code(self):
        statistics = {
            "total_feedback": 5,
            "players_since_beginning": 12,
            "players_today": 2,
            "average_score": 4.5,
            "average_feedback_rating": 4.2,
        }
        with (
            patch.object(server, "ADMIN_ACCOUNT_CODE", "ADMIN1"),
            patch.object(server, "get_dashboard_statistics", return_value=statistics),
        ):
            denied = self.client.get("/api/admin/dashboard")
            allowed = self.client.get(
                "/api/admin/dashboard", headers={"X-Admin-Code": "admin1"}
            )

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.get_json(), statistics)

    def test_dashboard_detail_endpoints_require_admin_and_return_only_details(self):
        cases = [
            ("/api/admin/score-comparisons", "get_score_comparisons", "entries",
             [{"first_score": 1, "second_score": 4}]),
            ("/api/admin/feedback-ratings", "get_feedback_rating_counts", "ratings",
             [{"rating": 1, "count": 0}]),
        ]
        with patch.object(server, "ADMIN_ACCOUNT_CODE", "ADMIN1"):
            for path, function, key, values in cases:
                with self.subTest(path=path):
                    with patch.object(server, function, return_value=values) as query:
                        self.assertEqual(self.client.get(path).status_code, 403)
                        self.assertEqual(
                            self.client.get(
                                path, headers={"X-Admin-Code": "visitor"}
                            ).status_code,
                            403,
                        )
                        query.assert_not_called()
                        response = self.client.get(
                            path, headers={"X-Admin-Code": "admin1"}
                        )
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.get_json(), {key: values})
                        query.assert_called_once_with()

    def test_completed_play_endpoint_records_one_quiz(self):
        play = {"id": 3, "created_at": "2026-11-15T10:00:00"}
        with patch.object(server, "record_visitor_play", return_value=play) as record:
            response = self.client.post(
                "/api/play-session", json={"category": "year", "score": 4}
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"saved": True, **play})
        record.assert_called_once_with("year", 4)

    def test_created_account_code_connects_scores_and_leaderboard_name(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        database = Path(temp_dir.name) / "accounts.db"
        with (
            patch.object(storage, "DB_PATH", database),
            patch.object(server, "LEADERBOARD_DEMO_MODE", False),
        ):
            storage.create_table()
            created = self.client.post(
                "/api/account/create", json={"display_name": "Nora"}
            )
            account_code = created.get_json()["account_code"]
            login = self.client.post(
                "/api/account/login",
                json={"account_code": account_code.lower()},
            )
            saved = self.client.post(
                "/api/account/save",
                json={
                    "account_code": account_code,
                    "category": "year",
                    "score": 1,
                    "correct_question_ids": ["year-question"],
                },
            )
            leaderboard = self.client.get(
                "/api/leaderboard?category=year&period=monthly"
            )

        self.assertEqual(created.status_code, 201)
        self.assertEqual(login.status_code, 200)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.get_json()["points_balance"], 0)
        self.assertEqual(
            leaderboard.get_json()["entries"],
            [{"player": "Nora", "score": 1}],
        )

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
