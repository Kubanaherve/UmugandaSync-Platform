# tests.py
# Production test suite for UmugandaSync
# Run: python3 -m pytest tests.py -v  OR  python3 tests.py

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import date


class TestNationalIdValidation(unittest.TestCase):
    """Test Rwanda National ID validation."""

    def setUp(self):
        import search
        self.validate = search.validate_national_id

    def test_valid_16_digit_id(self):
        """Valid 16-digit numeric ID should pass."""
        valid, result = self.validate("1199780123456789")
        self.assertTrue(valid)
        self.assertEqual(result, "1199780123456789")

    def test_none_input(self):
        """None input should fail."""
        valid, msg = self.validate(None)
        self.assertFalse(valid)

    def test_empty_string(self):
        """Empty string should fail."""
        valid, msg = self.validate("")
        self.assertFalse(valid)

    def test_too_short(self):
        """ID shorter than 16 digits should fail."""
        valid, msg = self.validate("12345")
        self.assertFalse(valid)

    def test_too_long(self):
        """ID longer than 16 digits should fail."""
        valid, msg = self.validate("12345678901234567")
        self.assertFalse(valid)

    def test_contains_letters(self):
        """ID with letters should fail."""
        valid, msg = self.validate("119978012345678A")
        self.assertFalse(valid)

    def test_contains_spaces(self):
        """ID with spaces should fail."""
        valid, msg = self.validate("1199 7801 2345 67")
        self.assertFalse(valid)

    def test_special_characters(self):
        """ID with special characters should fail."""
        valid, msg = self.validate("1199780123456-89")
        self.assertFalse(valid)

    def test_whitespace_trimming(self):
        """Leading/trailing whitespace should be trimmed."""
        valid, result = self.validate("  1199780123456789  ")
        self.assertTrue(valid)
        self.assertEqual(result, "1199780123456789")

    def test_all_zeros(self):
        """All zeros (16 digits) should be valid format."""
        valid, result = self.validate("0000000000000000")
        # It's 16 digits, so format is valid even if content is unusual
        self.assertTrue(valid)

    def test_integer_input(self):
        """Integer input should be converted and validated."""
        valid, result = self.validate(1199780123456789)
        self.assertTrue(valid)


class TestConfigConstants(unittest.TestCase):
    """Test configuration constants are properly set."""

    def test_app_name(self):
        import config
        self.assertEqual(config.APP_NAME, "UmugandaSync")

    def test_national_id_length(self):
        import config
        self.assertEqual(config.NATIONAL_ID_LENGTH, 16)

    def test_csv_encoding(self):
        import config
        self.assertEqual(config.CSV_ENCODING, "utf-8-sig")

    def test_csv_export_dir(self):
        import config
        self.assertIsInstance(config.CSV_EXPORT_DIR, str)
        self.assertTrue(len(config.CSV_EXPORT_DIR) > 0)

    def test_db_settings_exist(self):
        import config
        self.assertTrue(hasattr(config, "DB_HOST"))
        self.assertTrue(hasattr(config, "DB_USER"))
        self.assertTrue(hasattr(config, "DB_NAME"))


class TestLanguageSystem(unittest.TestCase):
    """Test the language translation system."""

    def setUp(self):
        import languages
        self.languages = languages
        self.languages.current_language = "en"

    def test_english_key_exists(self):
        """Known key should return English text."""
        result = self.languages.t("app_title")
        self.assertIn("UmugandaSync", result)

    def test_missing_key_returns_key(self):
        """Missing key should return the key itself."""
        result = self.languages.t("this_key_does_not_exist_xyz")
        self.assertEqual(result, "this_key_does_not_exist_xyz")

    def test_french_translation(self):
        """Setting French should return French text."""
        self.languages.current_language = "fr"
        result = self.languages.t("goodbye")
        self.assertIn("Au revoir", result)

    def test_kinyarwanda_translation(self):
        """Setting Kinyarwanda should return Kinyarwanda text."""
        self.languages.current_language = "rw"
        result = self.languages.t("goodbye")
        self.assertIn("Murabeho", result)

    def test_set_language_valid(self):
        """Setting a valid language should return True."""
        result = self.languages.set_language("fr")
        self.assertTrue(result)
        self.assertEqual(self.languages.current_language, "fr")

    def test_set_language_invalid(self):
        """Setting an invalid language should return False."""
        result = self.languages.set_language("xx")
        self.assertFalse(result)

    def test_fallback_to_english(self):
        """If key missing in current lang, should fall back to English."""
        self.languages.current_language = "rw"
        # If a key exists in en but not in rw, it should fallback
        en_keys = set(self.languages.TEXTS["en"].keys())
        rw_keys = set(self.languages.TEXTS["rw"].keys())
        missing = en_keys - rw_keys
        if missing:
            key = list(missing)[0]
            result = self.languages.t(key)
            self.assertEqual(result, self.languages.TEXTS["en"][key])

    def tearDown(self):
        self.languages.current_language = "en"


class TestDateCalculations(unittest.TestCase):
    """Test Umuganda date calculations."""

    def setUp(self):
        import helpers
        self.helpers = helpers

    def test_last_saturday_march_2026(self):
        """Last Saturday of March 2026 should be 2026-03-28."""
        result = self.helpers.get_last_saturday(2026, 3)
        self.assertEqual(result, date(2026, 3, 28))

    def test_last_saturday_april_2026(self):
        """Last Saturday of April 2026 should be 2026-04-25."""
        result = self.helpers.get_last_saturday(2026, 4)
        self.assertEqual(result, date(2026, 4, 25))

    def test_last_saturday_december(self):
        """December edge case (year boundary)."""
        result = self.helpers.get_last_saturday(2026, 12)
        self.assertEqual(result, date(2026, 12, 26))

    def test_last_saturday_january(self):
        """January should work correctly."""
        result = self.helpers.get_last_saturday(2026, 1)
        self.assertEqual(result, date(2026, 1, 31))

    def test_result_is_saturday(self):
        """Result should always be a Saturday (weekday=5)."""
        for month in range(1, 13):
            result = self.helpers.get_last_saturday(2026, month)
            self.assertEqual(result.weekday(), 5,
                             f"Month {month}: {result} is not Saturday")

    def test_today_string_format(self):
        """today_string() should return YYYY-MM-DD format."""
        result = self.helpers.today_string()
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}$")


class TestHelperFunctions(unittest.TestCase):
    """Test helper utility functions."""

    def setUp(self):
        import helpers
        self.helpers = helpers

    def test_month_names_length(self):
        """MONTH_NAMES should have 13 entries (index 0 is empty)."""
        self.assertEqual(len(self.helpers.MONTH_NAMES), 13)
        self.assertEqual(self.helpers.MONTH_NAMES[0], "")
        self.assertEqual(self.helpers.MONTH_NAMES[1], "January")
        self.assertEqual(self.helpers.MONTH_NAMES[12], "December")

    def test_umuganda_activities_not_empty(self):
        """Activity list should not be empty."""
        self.assertTrue(len(self.helpers.UMUGANDA_ACTIVITIES) > 0)

    def test_success_output(self):
        """success() should print message with checkmark."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.helpers.success("Test message")
        output = f.getvalue()
        self.assertIn("\u2713", output)
        self.assertIn("Test message", output)

    def test_error_output(self):
        """error() should print message with X mark."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.helpers.error("Error message")
        output = f.getvalue()
        self.assertIn("\u2717", output)
        self.assertIn("Error message", output)

    def test_info_output(self):
        """info() should print message with info symbol."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.helpers.info("Info message")
        output = f.getvalue()
        self.assertIn("Info message", output)

    def test_warning_output(self):
        """warning() should print message with warning symbol."""
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.helpers.warning("Warning message")
        output = f.getvalue()
        self.assertIn("Warning message", output)


class TestCSVExportPaths(unittest.TestCase):
    """Test CSV export path generation."""

    def test_export_path_includes_timestamp(self):
        """Generated paths should include timestamp."""
        import csv_export
        path = csv_export._get_export_path("test.csv")
        self.assertIn("test_", path)
        self.assertTrue(path.endswith(".csv"))

    def test_export_path_in_export_dir(self):
        """Path should be in the exports directory."""
        import csv_export
        path = csv_export._get_export_path("members.csv")
        self.assertIn("exports", path)

    def test_ensure_export_dir_creates_dir(self):
        """ensure_export_dir should create the directory."""
        import csv_export
        csv_export.ensure_export_dir()
        self.assertTrue(os.path.exists(csv_export.EXPORT_DIR))


class TestDatabaseModule(unittest.TestCase):
    """Test database module with mocked connections."""

    @patch('database.mysql.connector.connect')
    def test_connect_db_success(self, mock_connect):
        """Successful connection should return connection object."""
        import database
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        result = database.connect_db()
        self.assertIsNotNone(result)

    @patch('database.mysql.connector.connect')
    def test_connect_db_failure(self, mock_connect):
        """Failed connection should return None."""
        import database
        from mysql.connector import Error
        mock_connect.side_effect = Error("Connection failed")
        result = database.connect_db()
        self.assertIsNone(result)

    def test_close_db_none_values(self):
        """close_db should handle None gracefully."""
        import database
        # Should not raise any exception
        database.close_db(None, None)


if __name__ == "__main__":
    print("=" * 60)
    print("UmugandaSync Test Suite")
    print("=" * 60)
    unittest.main(verbosity=2)
