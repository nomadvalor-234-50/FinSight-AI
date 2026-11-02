"""Tests for T18 low-balance event detection."""

import unittest

try:
    from .low_balance_detection import detect_low_balance
except ImportError:
    from low_balance_detection import detect_low_balance


class LowBalanceTests(unittest.TestCase):
    def test_groups_consecutive_low_days_into_one_warning(self):
        prediction = {"daily_balances": [
            {"date": "2026-11-01", "expected_balance": 1200},
            {"date": "2026-11-02", "expected_balance": 900},
            {"date": "2026-11-03", "expected_balance": 800},
            {"date": "2026-11-04", "expected_balance": 1200},
        ]}
        result = detect_low_balance(prediction, minimum_balance=1000)
        self.assertEqual(result["warning_count"], 1)
        self.assertEqual(len(result["warnings"][0]["affected_dates"]), 2)
        self.assertEqual(result["warnings"][0]["lowest_predicted_balance"], 800)

    def test_separated_low_periods_make_distinct_events(self):
        prediction = {"daily_balances": [
            {"date": "2026-11-01", "expected_balance": 900},
            {"date": "2026-11-02", "expected_balance": 1200},
            {"date": "2026-11-03", "expected_balance": 800},
        ]}
        self.assertEqual(detect_low_balance(prediction, 1000)["warning_count"], 2)

    def test_duplicate_dates_do_not_duplicate_alerts(self):
        prediction = {"daily_balances": [
            {"date": "2026-11-01", "expected_balance": 900},
            {"date": "2026-11-01", "expected_balance": 850},
        ]}
        result = detect_low_balance(prediction, 1000)
        self.assertEqual(result["warning_count"], 1)
        self.assertEqual(len(result["warnings"][0]["affected_dates"]), 1)
        self.assertEqual(result["warnings"][0]["lowest_predicted_balance"], 850)

    def test_invalid_rows_are_skipped_and_threshold_validated(self):
        result = detect_low_balance({"daily_balances": [
            {"date": "bad-date", "expected_balance": 100},
            {"date": "2026-11-01", "expected_balance": "bad"},
        ]}, 1000)
        self.assertEqual(result["warnings"], [])
        with self.assertRaises(ValueError):
            detect_low_balance({"daily_balances": []}, float("inf"))


if __name__ == "__main__":
    unittest.main()
