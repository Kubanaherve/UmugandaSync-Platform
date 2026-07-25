"""UmugandaSync tests — reports helpers (Marvella)."""
import unittest


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
