"""Tests for T14 historical transaction analysis."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

try:
    from .historical_analysis import analyze_historical_transactions
except ImportError:
    from historical_analysis import analyze_historical_transactions


class HistoricalAnalysisTests(unittest.TestCase):
    def test_totals_and_net_cash_flow(self):
        transactions = pd.DataFrame([
            ("2026-01-05", "Salary", 5000, "credit", "Income"),
            ("2026-01-07", "Groceries", 1200, "debit", "Food"),
            ("2026-02-05", "Salary", 5200, "credit", "Income"),
            ("2026-02-08", "Bus pass", 300, "debit", "Transportation"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = analyze_historical_transactions(transactions)
        self.assertEqual(result["total_income"], 10200)
        self.assertEqual(result["total_expenses"], 1500)
        self.assertEqual(result["net_cash_flow"], 8700)

    def test_monthly_summaries_and_averages(self):
        transactions = pd.DataFrame([
            ("2026-01-05", "Salary", 5000, "credit", "Income"),
            ("2026-01-07", "Groceries", 1000, "debit", "Food"),
            ("2026-02-05", "Salary", 7000, "credit", "Income"),
            ("2026-02-08", "Utilities", 3000, "debit", "Utilities"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = analyze_historical_transactions(transactions)
        self.assertEqual(result["monthly_summary"], [
            {"month": "2026-01", "income": 5000.0, "expenses": 1000.0, "net_cash_flow": 4000.0},
            {"month": "2026-02", "income": 7000.0, "expenses": 3000.0, "net_cash_flow": 4000.0},
        ])
        self.assertEqual(result["average_monthly_income"], 6000)
        self.assertEqual(result["average_monthly_expenses"], 2000)

    def test_category_wise_expense_totals(self):
        transactions = pd.DataFrame([
            ("2026-01-01", "Lunch", 200, "debit", "Food"),
            ("2026-01-02", "Dinner", 300, "debit", "Food"),
            ("2026-01-03", "Cab", 150, "debit", "Transportation"),
            ("2026-01-04", "Salary", 1000, "credit", "Income"),
        ], columns=["date", "description", "amount", "type", "category"])
        self.assertEqual(
            analyze_historical_transactions(transactions)["category_wise_expenses"],
            {"Food": 500.0, "Transportation": 150.0},
        )

    def test_increasing_decreasing_and_stable_expense_trends(self):
        def analyze_monthly_expenses(amounts):
            rows = [
                (f"2026-{month:02d}-10", "Utility bill", amount, "debit", "Utilities")
                for month, amount in enumerate(amounts, start=1)
            ]
            frame = pd.DataFrame(rows, columns=["date", "description", "amount", "type", "category"])
            return analyze_historical_transactions(frame)["expense_trend"]

        self.assertEqual(analyze_monthly_expenses([100, 200, 300]), "Increasing")
        self.assertEqual(analyze_monthly_expenses([300, 200, 100]), "Decreasing")
        self.assertEqual(analyze_monthly_expenses([200, 200, 200]), "Stable")

    def test_empty_csv_returns_zeroed_result(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "empty.csv"
            csv_path.write_text("", encoding="utf-8")
            result = analyze_historical_transactions(csv_path)
        self.assertEqual(result["total_income"], 0)
        self.assertEqual(result["total_expenses"], 0)
        self.assertEqual(result["monthly_summary"], [])
        self.assertEqual(result["expense_trend"], "Stable")

    def test_invalid_transaction_rows_are_skipped(self):
        transactions = pd.DataFrame([
            ("2026-01-01", "Salary", 1000, "credit", "Income"),
            ("bad-date", "Invalid date", 500, "debit", "Food"),
            ("2026-01-03", "Invalid amount", "not-money", "debit", "Food"),
            (None, "Missing date", 100, "debit", "Food"),
            ("2026-01-05", "Missing amount", None, "debit", "Food"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = analyze_historical_transactions(transactions)
        self.assertEqual(result["total_income"], 1000)
        self.assertEqual(result["total_expenses"], 0)
        self.assertEqual(len(result["monthly_summary"]), 1)

    def test_positive_and_negative_infinite_amounts_are_skipped(self):
        transactions = pd.DataFrame([
            ("2026-01-01", "Salary", 100, "credit", "Income"),
            ("2026-01-02", "Groceries", 20, "debit", "Food"),
            ("2026-01-03", "Infinite income", float("inf"), "credit", "Income"),
            ("2026-01-04", "Negative infinite expense", float("-inf"), "debit", "Food"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = analyze_historical_transactions(transactions)
        self.assertEqual(result["total_income"], 100)
        self.assertEqual(result["total_expenses"], 20)

    def test_raw_csv_uses_existing_description_categorizer(self):
        transactions = pd.DataFrame([
            ("2026-03-01", "Zomato order", 250, "debit"),
            ("2026-03-02", "Salary credited", 2000, "credit"),
        ], columns=["date", "description", "amount", "type"])
        result = analyze_historical_transactions(transactions)
        self.assertEqual(result["category_wise_expenses"], {"Food": 250.0})
        self.assertEqual(result["total_income"], 2000)


if __name__ == "__main__":
    unittest.main()
