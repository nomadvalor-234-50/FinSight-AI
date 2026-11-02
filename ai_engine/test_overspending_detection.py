"""Tests for T19 budget and unusual-spending detection."""

import unittest

import pandas as pd

try:
    from .overspending_detection import detect_overspending
except ImportError:
    from overspending_detection import detect_overspending


class OverspendingTests(unittest.TestCase):
    def test_reports_budget_overrun_amount_and_percentage(self):
        result = detect_overspending(
            {"Food": 1500, "Transport": 200},
            {"Food": 1000, "Transport": 500},
        )
        food = next(row for row in result["alerts"] if row["category"] == "Food")
        self.assertEqual(food["budget"], 1000)
        self.assertEqual(food["actual_spending"], 1500)
        self.assertEqual(food["excess_amount"], 500)
        self.assertEqual(food["overspending_percentage"], 50)
        self.assertTrue(food["budget_overrun"])

    def test_flags_unusual_historical_spending_separately(self):
        result = detect_overspending(
            {"Food": 900}, {"Food": 2000}, historical_category_spending={"Food": 500}
        )
        food = result["alerts"][0]
        self.assertFalse(food["budget_overrun"])
        self.assertTrue(food["unusual_spending"])
        self.assertIn("unusual_vs_history", food["alert_reasons"])

    def test_handles_missing_budgets_and_categories_safely(self):
        result = detect_overspending({"Utilities": 300}, None)
        self.assertEqual(result["categories"][0]["budget"], None)
        self.assertEqual(result["categories"][0]["overspending_percentage"], None)
        self.assertEqual(result["alerts"], [])

    def test_uses_historical_analysis_for_transaction_frames(self):
        actual = pd.DataFrame([
            ("2026-04-01", "Zomato order", 900, "debit", "Food"),
            ("2026-04-02", "Salary", 5000, "credit", "Income"),
        ], columns=["date", "description", "amount", "type", "category"])
        history = pd.DataFrame([
            ("2026-01-01", "Lunch", 200, "debit", "Food"),
            ("2026-02-01", "Lunch", 300, "debit", "Food"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = detect_overspending(actual, {"Food": 1000}, historical_category_spending=history)
        self.assertEqual(result["categories"][0]["historical_monthly_average"], 250)
        self.assertTrue(result["categories"][0]["unusual_spending"])

    def test_actual_t14_summary_remains_total_for_budget_comparison(self):
        actual = {
            "category_wise_expenses": {"Food": 900},
            "monthly_summary": [{"month": "2026-01"}, {"month": "2026-02"}],
        }
        result = detect_overspending(actual, {"Food": 700})
        self.assertEqual(result["categories"][0]["actual_spending"], 900)
        self.assertEqual(result["categories"][0]["excess_amount"], 200)

    def test_invalid_budget_values_are_ignored(self):
        result = detect_overspending({"Food": 100}, {"Food": "invalid", "Rent": -2})
        self.assertEqual(result["categories"][0]["budget"], None)
        with self.assertRaises(ValueError):
            detect_overspending({}, {}, unusual_multiplier=1)

    def test_category_comparisons_ignore_case_and_keep_actual_display_name(self):
        result = detect_overspending(
            {"Food": 1200},
            {"fOoD": 1000},
            historical_category_spending={"FOOD": 500},
        )
        self.assertEqual(len(result["categories"]), 1)
        row = result["categories"][0]
        self.assertEqual(row["category"], "Food")
        self.assertEqual(row["budget"], 1000)
        self.assertTrue(row["budget_overrun"])
        self.assertTrue(row["unusual_spending"])


if __name__ == "__main__":
    unittest.main()
