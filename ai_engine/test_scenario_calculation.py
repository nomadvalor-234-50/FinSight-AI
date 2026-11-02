"""Tests for T27 hypothetical scenario calculations."""

import unittest

import pandas as pd

try:
    from .scenario_calculation import calculate_scenario
except ImportError:
    from scenario_calculation import calculate_scenario


class ScenarioCalculationTests(unittest.TestCase):
    def setUp(self):
        self.forecast = {
            "forecast_days": 30, "total_predicted_income": 3000,
            "total_predicted_expenses": 2000, "forecast": [],
        }

    def test_income_and_expense_percentage_scenario(self):
        result = calculate_scenario(self.forecast, current_balance=1000,
                                    income_change_percent=10, expense_change_percent=-10)
        self.assertEqual(result["modified"]["total_income"], 3300)
        self.assertEqual(result["modified"]["total_expenses"], 1800)
        self.assertEqual(result["modified"]["net_cash_flow"], 1500)
        self.assertEqual(result["difference"]["projected_balance"], 500)

    def test_amount_changes_and_one_time_transactions(self):
        result = calculate_scenario(
            self.forecast, current_balance=500,
            income_change_amount=200, expense_change_amount=-100,
            additional_one_time_income=300, additional_one_time_expenses=50,
        )
        self.assertEqual(result["modified"]["total_income"], 3500)
        self.assertEqual(result["modified"]["total_expenses"], 1950)
        self.assertEqual(result["modified"]["net_cash_flow"], 1550)
        self.assertEqual(result["difference"]["net_cash_flow"], 550)

    def test_category_specific_change_uses_history_without_mutating_input(self):
        transactions = pd.DataFrame([
            ("2026-01-01", "Salary", 3000, "credit", "Income"),
            ("2026-01-03", "Groceries", 600, "debit", "Food"),
            ("2026-01-04", "Bus pass", 400, "debit", "Transport"),
        ], columns=["date", "description", "amount", "type", "category"])
        original_copy = transactions.copy(deep=True)
        result = calculate_scenario(
            self.forecast, transactions=transactions, current_balance=500,
            category_expense_changes={"Food": {"percent": -50}},
        )
        self.assertEqual(result["modified"]["total_expenses"], 1400)
        self.assertEqual(result["difference"]["total_expenses"], -600)
        pd.testing.assert_frame_equal(transactions, original_copy)

    def test_can_build_forecast_from_transactions_when_not_supplied(self):
        transactions = pd.DataFrame([
            ("2026-01-01", "Salary", 3000, "credit", "Income"),
            ("2026-01-03", "Groceries", 1000, "debit", "Food"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = calculate_scenario(transactions=transactions, forecast_days=7,
                                    forecast_start_date="2026-02-01", current_balance=500,
                                    income_change_amount=100)
        self.assertEqual(result["forecast_days"], 7)
        self.assertGreater(result["original"]["total_income"], 0)
        self.assertTrue(result["scenario_type"].startswith("Hypothetical"))

    def test_rejects_invalid_percentages_amounts_and_ambiguous_changes(self):
        with self.assertRaises(ValueError):
            calculate_scenario(self.forecast, current_balance=100, income_change_percent=-101)
        with self.assertRaises(ValueError):
            calculate_scenario(self.forecast, current_balance=100,
                               income_change_percent=10, income_change_amount=5)
        with self.assertRaises(ValueError):
            calculate_scenario(self.forecast, current_balance=100, additional_one_time_expenses=-1)
        transactions = pd.DataFrame(columns=["date", "description", "amount", "type"])
        with self.assertRaises(ValueError):
            calculate_scenario(self.forecast, current_balance=100, transactions=transactions,
                               category_expense_changes={"Unknown": {"percent": -10}})

    def test_compares_original_and_modified_forecast(self):
        result = calculate_scenario(
            self.forecast, current_balance=1000,
            original_balance_prediction={"ending_balance": 2450},
            additional_one_time_income=100,
        )
        self.assertEqual(result["original"]["projected_balance"], 2450)
        self.assertEqual(result["modified"]["projected_balance"], 2550)
        self.assertEqual(result["difference"], {
            "total_income": 100, "total_expenses": 0, "net_cash_flow": 100,
            "projected_balance": 100,
        })


if __name__ == "__main__":
    unittest.main()
