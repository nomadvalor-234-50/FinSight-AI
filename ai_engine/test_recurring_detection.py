"""Tests for the recurring payment detection prototype."""

import unittest

import pandas as pd

try:  # Support both ``python -m unittest ai_engine.test_recurring_detection``
    from .recurring_detection import detect_recurring_payments
except ImportError:  # and ``python -m unittest test_recurring_detection`` in ai_engine/
    from recurring_detection import detect_recurring_payments


class RecurringDetectionTests(unittest.TestCase):
    def test_detects_monthly_payment_and_estimates_next_date(self):
        transactions = pd.DataFrame({
            "date": ["2026-08-05", "2026-09-05", "2026-10-05"],
            "description": ["Netflix", "Netflix subscription", "Netflix"],
            "amount": [649, 649, 649],
            "type": ["debit", "debit", "debit"],
        })
        detected = detect_recurring_payments(transactions)
        netflix = next(item for item in detected if "Netflix" in item["description"])
        self.assertEqual(netflix["frequency"], "Monthly")
        self.assertEqual(netflix["occurrences"], 3)
        self.assertEqual(netflix["average_amount"], 649)
        self.assertEqual(netflix["recurrence_interval_days"], 30.5)
        self.assertEqual(netflix["next_payment_date"], "2026-11-05")
        self.assertTrue(netflix["is_recurring"])

    def test_supports_weekly_yearly_and_variable_bill_amounts(self):
        transactions = pd.DataFrame([
            ("2026-09-01", "Weekly transfer", 200, "debit"),
            ("2026-09-08", "Weekly transfer", 200, "debit"),
            ("2026-09-15", "Weekly transfer", 200, "debit"),
            ("2024-03-01", "Cloud plan", 999, "debit"),
            ("2025-03-01", "Cloud plan", 999, "debit"),
            ("2026-03-01", "Cloud plan", 999, "debit"),
            ("2026-08-07", "Water utility", 1000, "debit"),
            ("2026-09-07", "Water utility", 1100, "debit"),
            ("2026-10-07", "Water utility", 1050, "debit"),
        ], columns=["date", "description", "amount", "type"])
        detected = detect_recurring_payments(transactions)
        by_name = {item["description"]: item for item in detected}
        self.assertEqual(by_name["Weekly transfer"]["frequency"], "Weekly")
        self.assertEqual(by_name["Cloud plan"]["frequency"], "Yearly")
        self.assertEqual(by_name["Water utility"]["frequency"], "Monthly")
        self.assertEqual(by_name["Water utility"]["average_amount"], 1050)

    def test_required_weekly_dates_have_seven_day_average(self):
        transactions = pd.DataFrame({
            "date": ["2026-08-01", "2026-08-08", "2026-08-15"],
            "description": ["Weekly transfer"] * 3,
            "amount": [200] * 3,
        })
        result = detect_recurring_payments(transactions)[0]
        self.assertEqual(result["frequency"], "Weekly")
        self.assertEqual(result["recurrence_interval_days"], 7.0)

    def test_required_yearly_dates_have_365_5_day_average(self):
        transactions = pd.DataFrame({
            "date": ["2024-01-10", "2025-01-10", "2026-01-10"],
            "description": ["Annual membership"] * 3,
            "amount": [1200] * 3,
        })
        result = detect_recurring_payments(transactions)[0]
        self.assertEqual(result["frequency"], "Yearly")
        self.assertEqual(result["recurrence_interval_days"], 365.5)

    def test_irregular_three_occurrence_pattern_is_reported_as_irregular(self):
        transactions = pd.DataFrame({
            "date": ["2026-08-01", "2026-08-10", "2026-10-05"],
            "description": ["Variable payment"] * 3,
            "amount": [500] * 3,
        })
        result = detect_recurring_payments(transactions)[0]
        self.assertEqual(result["frequency"], "Irregular")
        self.assertEqual(result["recurrence_interval_days"], 32.5)
        self.assertIsNone(result["next_payment_date"])
        self.assertFalse(result["is_recurring"])

    def test_one_time_transaction_is_not_reported(self):
        transaction = pd.DataFrame({
            "date": ["2026-08-01"],
            "description": ["Netflix"],
            "amount": [649],
        })
        self.assertEqual(detect_recurring_payments(transaction), [])

    def test_duplicate_transactions_do_not_inflate_occurrences(self):
        transactions = pd.DataFrame({
            "date": ["2026-08-05", "2026-08-05", "2026-09-05", "2026-10-05"],
            "description": ["Netflix"] * 4,
            "amount": [649] * 4,
        })
        result = detect_recurring_payments(transactions)[0]
        self.assertEqual(result["occurrences"], 3)
        self.assertEqual(result["average_amount"], 649)

    def test_positive_and_negative_infinite_amounts_are_skipped(self):
        transactions = pd.DataFrame([
            ("2026-08-05", "Gym membership", 100, "debit"),
            ("2026-09-05", "Gym membership", 100, "debit"),
            ("2026-10-05", "Gym membership", 100, "debit"),
            ("2026-11-05", "Gym membership", float("inf"), "debit"),
            ("2026-12-05", "Gym membership", float("-inf"), "debit"),
        ], columns=["date", "description", "amount", "type"])
        result = detect_recurring_payments(transactions)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["occurrences"], 3)
        self.assertEqual(result[0]["average_amount"], 100)
        self.assertEqual(result[0]["next_payment_date"], "2026-11-05")

    def test_ignores_one_time_invalid_and_income_rows(self):
        transactions = pd.DataFrame([
            ("2026-10-01", "One-time purchase", 500, "debit"),
            ("not-a-date", "Netflix", 649, "debit"),
            ("2026-08-05", "Salary", 30000, "credit"),
            ("2026-09-05", "Salary", 30000, "credit"),
            ("2026-10-05", "Salary", 30000, "credit"),
            (None, None, None, "debit"),
        ], columns=["date", "description", "amount", "type"])
        self.assertEqual(detect_recurring_payments(transactions), [])


if __name__ == "__main__":
    unittest.main()
