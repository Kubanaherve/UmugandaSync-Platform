"""
UmugandaSync tests — pure function tests (no DB required).

Run:  python -m pytest tests.py -v
Or:   python tests.py
"""

import unittest
from unittest.mock import MagicMock, patch


class TestConfig(unittest.TestCase):
    """Configuration constants and defaults."""

    def test_app_name(self):
        import config
        self.assertEqual(config.APP_NAME, "UmugandaSync")

    def test_db_defaults(self):
        import config
        self.assertEqual(config.DB_HOST, "localhost")
        self.assertEqual(config.DB_PORT, 3306)
        self.assertEqual(config.DB_USER, "root")
        self.assertEqual(config.DB_NAME, "umuganda_sync")

    def test_constants(self):
        import config
        self.assertEqual(config.MAX_LOGIN_ATTEMPTS, 3)
        self.assertEqual(config.NATIONAL_ID_LENGTH, 16)


class TestReportsHelpers(unittest.TestCase):
    """Reports pure helpers must tolerate None DB aggregates."""

    def test_safe_num_none(self):
        import reports
        self.assertEqual(reports.safe_num(None), 0)

    def test_safe_num_values(self):
        import reports
        self.assertEqual(reports.safe_num(0), 0)
        self.assertEqual(reports.safe_num(12), 12)

    def test_safe_row_none_row(self):
        import reports
        self.assertEqual(reports.safe_row(None, "total"), 0)

    def test_safe_row_none_value(self):
        import reports
        self.assertEqual(reports.safe_row({"total": None}, "total"), 0)

    def test_safe_row_present(self):
        import reports
        self.assertEqual(reports.safe_row({"total": 4}, "total"), 4)

    def test_safe_row_missing_key_default(self):
        import reports
        self.assertEqual(reports.safe_row({"total": 4}, "missing", default=9), 9)


class TestProjectsValidation(unittest.TestCase):
    """Project validation rules (no DB needed)."""

    def test_validate_name_valid(self):
        import projects
        self.assertEqual(projects.validate_project_name("Road Repair"), "Road Repair")

    def test_validate_name_too_short(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_project_name("A")

    def test_validate_name_none(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_project_name(None)

    def test_validate_name_max_length(self):
        import projects
        long_name = "A" * 101
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_project_name(long_name)

    def test_validate_location_valid(self):
        import projects
        self.assertEqual(projects.validate_location("Kigali"), "Kigali")

    def test_validate_location_empty(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_location("")

    def test_validate_location_none(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_location(None)

    def test_validate_description_none(self):
        import projects
        self.assertIsNone(projects.validate_description(None))

    def test_validate_description_empty(self):
        import projects
        self.assertIsNone(projects.validate_description(""))

    def test_validate_percent_valid(self):
        import projects
        self.assertEqual(projects.validate_percent_complete(50), 50)
        self.assertEqual(projects.validate_percent_complete(0), 0)
        self.assertEqual(projects.validate_percent_complete(100), 100)

    def test_validate_percent_invalid(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_percent_complete(-1)
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_percent_complete(101)

    def test_validate_percent_not_int(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_percent_complete("abc")

    def test_validate_status_valid(self):
        import projects
        for s in ("Pending", "Ongoing", "Completed", "Cancelled"):
            self.assertEqual(projects.validate_status(s), s)

    def test_validate_status_invalid(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_status("Unknown")

    def test_validate_date_string_valid(self):
        import projects
        self.assertEqual(projects.validate_date_string("2026-07-25"), "2026-07-25")

    def test_validate_date_string_invalid(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_date_string("not-a-date")

    def test_validate_date_string_empty(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_date_string("")

    def test_validate_date_string_none(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_date_string(None)

    def test_validate_date_range_valid(self):
        import projects
        projects.validate_date_range("2026-01-01", "2026-06-30")

    def test_validate_date_range_invalid(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_date_range("2026-06-30", "2026-01-01")

    def test_derive_status_100_percent(self):
        import projects
        self.assertEqual(projects.derive_status_from_progress("Ongoing", 100), "Completed")

    def test_derive_status_above_zero_pending(self):
        import projects
        self.assertEqual(projects.derive_status_from_progress("Pending", 50), "Ongoing")

    def test_derive_status_zero_pending(self):
        import projects
        self.assertEqual(projects.derive_status_from_progress("Pending", 0), "Pending")

    def test_derive_status_cancelled(self):
        import projects
        self.assertEqual(projects.derive_status_from_progress("Cancelled", 50), "Cancelled")

    def test_derive_status_completed_below_100(self):
        import projects
        self.assertEqual(projects.derive_status_from_progress("Completed", 80), "Ongoing")

    def test_validate_leader_id_valid(self):
        import projects
        self.assertEqual(projects.validate_leader_id(1), 1)

    def test_validate_leader_id_invalid(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_leader_id(0)
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_leader_id(-1)

    def test_validate_leader_id_not_int(self):
        import projects
        with self.assertRaises(projects.ProjectValidationError):
            projects.validate_leader_id("abc")


class TestProjectsDomainServices(unittest.TestCase):
    """Project domain logic: deadlines, labels (no DB)."""

    def test_days_until_deadline_future(self):
        import projects
        from datetime import date
        days = projects.days_until_deadline("2026-12-31", date(2026, 7, 25))
        self.assertEqual(days, 159)

    def test_days_until_deadline_past(self):
        import projects
        from datetime import date
        days = projects.days_until_deadline("2026-01-01", date(2026, 7, 25))
        self.assertEqual(days, -205)

    def test_days_until_deadline_today(self):
        import projects
        from datetime import date
        days = projects.days_until_deadline("2026-07-25", date(2026, 7, 25))
        self.assertEqual(days, 0)

    def test_deadline_label_overdue(self):
        import projects
        from datetime import date
        proj = {"status": "Pending", "expected_end_date": "2026-01-01"}
        self.assertEqual(projects.deadline_label(proj, date(2026, 7, 25)), "OVERDUE")

    def test_deadline_label_due_today(self):
        import projects
        from datetime import date
        proj = {"status": "Ongoing", "expected_end_date": "2026-07-25"}
        self.assertEqual(projects.deadline_label(proj, date(2026, 7, 25)), "DUE_TODAY")

    def test_deadline_label_due_soon(self):
        import projects
        from datetime import date
        proj = {"status": "Ongoing", "expected_end_date": "2026-07-30"}
        self.assertEqual(projects.deadline_label(proj, date(2026, 7, 25)), "DUE_SOON")

    def test_deadline_label_on_track(self):
        import projects
        from datetime import date
        proj = {"status": "Ongoing", "expected_end_date": "2026-12-31"}
        self.assertEqual(projects.deadline_label(proj, date(2026, 7, 25)), "ON_TRACK")

    def test_deadline_label_completed_na(self):
        import projects
        proj = {"status": "Completed", "expected_end_date": "2026-01-01"}
        self.assertEqual(projects.deadline_label(proj), "N/A")

    def test_deadline_label_cancelled_na(self):
        import projects
        proj = {"status": "Cancelled", "expected_end_date": "2026-01-01"}
        self.assertEqual(projects.deadline_label(proj), "N/A")

    def test_is_project_overdue_true(self):
        import projects
        from datetime import date
        proj = {"status": "Ongoing", "expected_end_date": "2026-01-01"}
        self.assertTrue(projects.is_project_overdue(proj, date(2026, 7, 25)))

    def test_is_project_overdue_false_future(self):
        import projects
        from datetime import date
        proj = {"status": "Ongoing", "expected_end_date": "2026-12-31"}
        self.assertFalse(projects.is_project_overdue(proj, date(2026, 7, 25)))

    def test_is_project_overdue_false_completed(self):
        import projects
        proj = {"status": "Completed", "expected_end_date": "2026-01-01"}
        self.assertFalse(projects.is_project_overdue(proj))


class TestMembersValidation(unittest.TestCase):
    """Member validation helpers (no DB)."""

    def test_validate_national_id_valid(self):
        import members
        self.assertEqual(members.validate_national_id("1199780123456789"), "1199780123456789")

    def test_validate_national_id_none(self):
        import members
        self.assertIsNone(members.validate_national_id(None))

    def test_validate_national_id_empty(self):
        import members
        self.assertIsNone(members.validate_national_id(""))

    def test_validate_national_id_too_short(self):
        import members
        with self.assertRaises(members.ValidationError):
            members.validate_national_id("12345")

    def test_validate_national_id_letters(self):
        import members
        with self.assertRaises(members.ValidationError):
            members.validate_national_id("ABCD123456789012")

    def test_validate_phone_valid(self):
        import members
        self.assertEqual(members.validate_phone("0788123456"), "0788123456")
        self.assertEqual(members.validate_phone("+250788123456"), "+250788123456")
        self.assertEqual(members.validate_phone("250788123456"), "250788123456")

    def test_validate_phone_none(self):
        import members
        with self.assertRaises(members.ValidationError):
            members.validate_phone(None)

    def test_validate_phone_invalid(self):
        import members
        with self.assertRaises(members.ValidationError):
            members.validate_phone("12345")

    def test_validate_email_valid(self):
        import members
        self.assertEqual(members.validate_email("test@example.com"), "test@example.com")

    def test_validate_email_none(self):
        import members
        self.assertIsNone(members.validate_email(None))

    def test_validate_email_empty(self):
        import members
        self.assertIsNone(members.validate_email(""))

    def test_validate_email_invalid(self):
        import members
        with self.assertRaises(members.ValidationError):
            members.validate_email("not-an-email")


class TestHelpers(unittest.TestCase):
    """Pure helper functions."""

    def test_today_string_format(self):
        import helpers
        from datetime import datetime
        today = helpers.today_string()
        datetime.strptime(today, "%Y-%m-%d")

    def test_format_date_str(self):
        import helpers
        self.assertEqual(helpers.format_date("2026-07-25"), "2026-07-25")

    def test_format_date_none(self):
        import helpers
        self.assertEqual(helpers.format_date(None), "")

    def test_sanitize_string_none(self):
        import helpers
        self.assertEqual(helpers.sanitize_string(None), "")

    def test_sanitize_string_truncated(self):
        import helpers
        import config
        long = "x" * (config.MAX_INPUT_LENGTH + 10)
        result = helpers.sanitize_string(long)
        self.assertEqual(len(result), config.MAX_INPUT_LENGTH)

    def test_validate_phone_07(self):
        import helpers
        self.assertEqual(helpers.validate_phone("0788123456"), "0788123456")

    def test_validate_phone_2507(self):
        import helpers
        self.assertEqual(helpers.validate_phone("+250788123456"), "+250788123456")

    def test_validate_phone_invalid(self):
        import helpers
        self.assertIsNone(helpers.validate_phone("12345"))

    def test_validate_phone_none(self):
        import helpers
        self.assertIsNone(helpers.validate_phone(None))

    def test_print_line(self):
        import helpers
        helpers.print_line("Test Title")
        helpers.print_line()

    def test_success(self):
        import helpers
        helpers.success("Test")

    def test_error(self):
        import helpers
        helpers.error("Test")

    def test_tip(self):
        import helpers
        helpers.tip("Test tip")


class TestLanguage(unittest.TestCase):
    """Language module tests."""

    def test_set_language_valid(self):
        import languages
        self.assertTrue(languages.set_language("en"))
        self.assertTrue(languages.set_language("fr"))
        self.assertTrue(languages.set_language("rw"))

    def test_set_language_invalid(self):
        import languages
        self.assertFalse(languages.set_language("de"))

    def test_t_existing_key(self):
        import languages
        languages.set_language("en")
        text = languages.t("app_title")
        self.assertIn("UmugandaSync", text)

    def test_t_missing_key_fallback(self):
        import languages
        text = languages.t("nonexistent_key", fallback="Fallback text")
        self.assertEqual(text, "Fallback text")

    def test_t_missing_key_no_fallback(self):
        import languages
        languages.set_language("en")
        text = languages.t("nonexistent_key")
        self.assertEqual(text, "nonexistent_key")

    def test_add_keys(self):
        import languages
        languages.add_keys("en", {"test_key": "Test Value"})
        self.assertEqual(languages.t("test_key"), "Test Value")

    def test_get_available_languages(self):
        import languages
        langs = languages.get_available_languages()
        self.assertIn("en", langs)
        self.assertIn("fr", langs)
        self.assertIn("rw", langs)


class TestDatabaseHelpers(unittest.TestCase):
    """Database helper module — CRUD helpers and connection logic."""

    @patch("database.connect_db")
    def test_run_query_select_one(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1, "name": "Test"}
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.run_query("SELECT * FROM test WHERE id = %s", (1,), fetch="one")
        self.assertEqual(result, {"id": 1, "name": "Test"})

    @patch("database.connect_db")
    def test_run_query_insert(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.run_query("INSERT INTO test (name) VALUES (%s)", ("Test",))
        self.assertEqual(result, 42)

    @patch("database.connect_db")
    def test_run_query_fetch_all(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.run_query("SELECT * FROM test", fetch="all")
        self.assertEqual(len(result), 2)

    @patch("database.connect_db")
    def test_insert_one(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 99
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.insert_one("members", {"first_name": "John", "last_name": "Doe"})
        self.assertEqual(result, 99)

    @patch("database.connect_db")
    def test_get_one(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1, "name": "Test"}
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.get_one("test", "id = %s", (1,))
        self.assertEqual(result["id"], 1)

    @patch("database.connect_db")
    def test_count(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 5}
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.count("members")
        self.assertEqual(result, 5)

    @patch("database.connect_db")
    def test_exists_true(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {1: 1}
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        self.assertTrue(database.exists("members", "member_id = %s", (1,)))

    @patch("database.connect_db")
    def test_exists_false(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        self.assertFalse(database.exists("members", "member_id = %s", (999,)))

    @patch("database.connect_db",
           return_value=None)
    def test_run_query_connection_failure(self, mock_connect):
        import database
        result = database.run_query("SELECT 1", fetch="one")
        self.assertIsNone(result)

    @patch("database.connect_db")
    def test_execute_many(self, mock_connect):
        import database
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = database.execute_many(
            "INSERT INTO test (col) VALUES (%s)",
            [("a",), ("b",), ("c",)],
        )
        self.assertEqual(result, 3)

    def test_test_connection_success(self):
        import database
        with patch.object(database, 'connect_db') as mock_connect:
            mock_connect.return_value = MagicMock()
            self.assertTrue(database.test_connection())

    def test_test_connection_failure(self):
        import database
        with patch.object(database, 'connect_db') as mock_connect:
            mock_connect.return_value = None
            self.assertFalse(database.test_connection())


class TestCSVExport(unittest.TestCase):
    """CSV export module tests."""

    @patch("csv_export.database.run_query")
    @patch("csv_export._write_csv")
    @patch("csv_export.helpers.pause")
    def test_export_members_no_data(self, mock_pause, mock_write, mock_query):
        import csv_export
        mock_query.return_value = None
        csv_export.export_members()
        mock_write.assert_not_called()

    @patch("csv_export.database.run_query")
    @patch("csv_export._write_csv")
    @patch("csv_export.helpers.pause")
    def test_export_members_with_data(self, mock_pause, mock_write, mock_query):
        import csv_export
        mock_query.return_value = [{"member_id": 1, "first_name": "John"}]
        mock_write.return_value = 1
        csv_export.export_members()
        mock_write.assert_called_once()

    @patch("csv_export.database.run_query")
    @patch("csv_export._write_csv")
    @patch("csv_export.helpers.pause")
    def test_export_attendance_no_data(self, mock_pause, mock_write, mock_query):
        import csv_export
        mock_query.return_value = None
        csv_export.export_attendance()
        mock_write.assert_not_called()


class TestMenu(unittest.TestCase):
    """Menu module tests."""

    def test_build_menu(self):
        import menu
        menu.build_menu("Test Menu", [("m1",)])

    def test_show_login_header(self):
        import menu
        menu.show_login_header()

    def test_show_main_menu(self):
        import menu
        menu.show_main_menu()


class TestNotifications(unittest.TestCase):
    """Notification module tests."""

    def test_register_and_get_handler(self):
        import search
        handler = search.get_search_handler("members")
        self.assertIsNotNone(handler)

    def test_search_handler_registration(self):
        import search
        def dummy():
            pass
        search.register_search_handler("test_handler", dummy)
        self.assertIsNotNone(search.get_search_handler("test_handler"))


class TestReportsBuilders(unittest.TestCase):
    """Report metric builders — tested with mocked DB."""

    @patch("reports._query")
    def test_build_community_metrics(self, mock_query):
        import reports
        mock_query.side_effect = [
            {"total": 10},
            {"total": 8},
            {"total": 5},
            {"total": 2},
            {"total": 1},
            {"total": 5},
            {"total": 15},
            {"total": 4},
        ]
        result = reports.build_community_metrics()
        self.assertEqual(result["total_members"], 10)
        self.assertEqual(result["active_members"], 8)
        self.assertEqual(result["total_projects"], 5)
        self.assertEqual(result["ongoing_projects"], 2)
        self.assertEqual(result["completed_projects"], 1)

    @patch("reports._query")
    def test_build_community_metrics_empty_db(self, mock_query):
        import reports
        mock_query.side_effect = [
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
        ]
        result = reports.build_community_metrics()
        self.assertEqual(result["total_members"], 0)
        self.assertEqual(result["completion_rate"], 0.0)

    @patch("reports._query")
    def test_build_member_breakdown(self, mock_query):
        import reports
        mock_query.side_effect = [
            [{"status": "Active", "total": 8}, {"status": "Inactive", "total": 2}],
            [{"village": "Kagugu", "total": 4}, {"village": "Kacyiru", "total": 3}],
        ]
        result = reports.build_member_breakdown()
        self.assertEqual(len(result["by_status"]), 2)
        self.assertEqual(len(result["by_village"]), 2)

    @patch("reports._query")
    def test_build_kpi_snapshot(self, mock_query):
        import reports
        mock_query.side_effect = [
            {"total": 10},
            {"total": 8},
            {"total": 5},
            {"total": 2},
            {"total": 1},
            {"total": 5},
            {"total": 15},
            {"total": 4},
            {"total": 5},
            {"total": 10},
            {"total": 3},
            [],
            [],
            [],
            [],
        ]
        result = reports.build_kpi_snapshot()
        self.assertIn("completion_rate", result)
        self.assertIn("active_members", result)
        self.assertIn("low_stock_items", result)


class TestSearchModule(unittest.TestCase):
    """Search module tests."""

    def test_quick_search_empty_term(self):
        import search
        result = search.quick_search("")
        self.assertEqual(result, {"members": [], "projects": [], "tools": []})

    @patch("search.database.run_query")
    def test_quick_search_with_term(self, mock_query):
        import search
        mock_query.return_value = []
        result = search.quick_search("test")
        self.assertIn("members", result)
        self.assertIn("projects", result)
        self.assertIn("tools", result)

    @patch("search.database.run_query")
    def test_search_member_by_national_id(self, mock_query):
        import search
        mock_query.return_value = {"member_id": 1, "first_name": "Jean"}
        result = search.search_member_by_national_id("1199780123456789")
        self.assertIsNotNone(result)

    def test_search_member_by_national_id_invalid(self):
        import search
        result = search.search_member_by_national_id("123")
        self.assertIsNone(result)


class TestLoginModule(unittest.TestCase):
    """Login module tests."""

    @patch("login.database.run_query")
    def test_login_success(self, mock_query):
        import login
        mock_query.return_value = {"admin_id": 1, "username": "admin", "full_name": "Admin User"}
        with patch("login.helpers.get_non_empty") as mock_input:
            mock_input.side_effect = ["admin", "admin123"]
            with patch("login.helpers.pause"):
                result = login.login()
                self.assertIsNotNone(result)
                self.assertEqual(result["full_name"], "Admin User")

    @patch("login.database.run_query")
    def test_login_failure(self, mock_query):
        import login
        mock_query.return_value = None
        with patch("login.helpers.get_non_empty") as mock_input:
            mock_input.side_effect = ["admin", "wrong", "admin", "wrong", "admin", "wrong"]
            result = login.login()
            self.assertIsNone(result)

    @patch("login.database.run_query")
    def test_member_login_success(self, mock_query):
        import login
        mock_query.return_value = {
            "member_id": 1, "first_name": "Jean", "last_name": "Uwimana",
            "phone": "0788000001", "village": "Kagugu", "cell_name": "Nyarugunga",
            "status": "Active"
        }
        with patch("login.helpers.get_positive_int") as mock_id:
            mock_id.return_value = 1
            with patch("login.helpers.get_non_empty") as mock_phone:
                mock_phone.return_value = "0788000001"
                with patch("login.helpers.pause"):
                    result = login.member_login()
                    self.assertIsNotNone(result)

    @patch("login.database.run_query")
    def test_member_login_inactive(self, mock_query):
        import login
        mock_query.return_value = {
            "member_id": 1, "first_name": "Patrick", "last_name": "Habimana",
            "phone": "0788000005", "status": "Inactive"
        }
        with patch("login.helpers.get_positive_int") as mock_id:
            mock_id.return_value = 5
            with patch("login.helpers.get_non_empty") as mock_phone:
                mock_phone.return_value = "0788000005"
                with patch("login.helpers.pause"):
                    result = login.member_login()
                    self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
