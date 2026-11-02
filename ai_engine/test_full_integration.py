"""End-to-end tests for the FinSight AI module integration runner."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

try:
    from .run_full_analysis import run_full_analysis
except ImportError:
    from run_full_analysis import run_full_analysis


class FullIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.transactions_path = self.root / "transactions.csv"
        self.transactions = pd.DataFrame([
            ("2026-01-01", "Monthly Salary", 5000, "credit"),
            ("2026-02-01", "Monthly Salary", 5000, "credit"),
            ("2026-03-01", "Monthly Salary", 5000, "credit"),
            ("2026-01-10", "House rent", 2500, "debit"),
            ("2026-02-10", "House rent", 2500, "debit"),
            ("2026-03-10", "House rent", 2500, "debit"),
            ("2026-01-05", "Netflix subscription", 649, "debit"),
            ("2026-02-05", "Netflix subscription", 649, "debit"),
            ("2026-03-05", "Netflix subscription", 649, "debit"),
            ("2026-01-12", "Zomato order", 300, "debit"),
            ("2026-02-12", "Zomato order", 700, "debit"),
            ("2026-03-12", "Zomato order", 1200, "debit"),
            ("2026-01-15", "BESCOM electricity bill", 300, "debit"),
            ("2026-02-15", "BESCOM electricity bill", 350, "debit"),
            ("2026-03-15", "BESCOM electricity bill", 400, "debit"),
        ], columns=["date", "description", "amount", "type"])
        self.transactions.to_csv(self.transactions_path, index=False)

    def tearDown(self):
        self.directory.cleanup()

    def run_pipeline(self, **kwargs):
        return run_full_analysis(
            self.transactions_path,
            current_balance=kwargs.pop("current_balance", 1000),
            minimum_balance=kwargs.pop("minimum_balance", 1000),
            forecast_days=kwargs.pop("forecast_days", 30),
            forecast_start_date=kwargs.pop("forecast_start_date", "2026-04-01"),
            **kwargs,
        )

    def test_complete_pipeline_and_data_flow(self):
        result = self.run_pipeline(budgets={"Food": 500, "subscription": 500})
        self.assertEqual(result["categorized_category_counts"]["Food"], 3)
        recurring = {row["description"]: row for row in result["recurring_payments"]}
        self.assertIn("Netflix subscription", recurring)
        self.assertIn("House rent", recurring)
        self.assertTrue(all(row["is_recurring"] for row in recurring.values()))
        self.assertGreater(result["upcoming_payment_total"], 0)
        self.assertEqual(len(result["cash_flow_forecast"]["forecast"]), 30)
        self.assertTrue(result["cash_flow_forecast"]["recurring_payments_excluded_from_baseline"])
        forecast_dates = {row["date"] for row in result["cash_flow_forecast"]["forecast"]}
        self.assertTrue(all(
            row["expected_payment_date"] in forecast_dates
            for row in result["upcoming_payments"]
        ))
        # Dated recurring charges are removed from T15's smooth run rate, then
        # represented by T12/T16 on their expected dates exactly once.
        self.assertLess(
            result["cash_flow_forecast"]["total_predicted_expenses"],
            result["historical_summary"]["average_monthly_expenses"],
        )

        rent_day = next(row for row in result["daily_predicted_balances"] if row["date"] == "2026-04-10")
        # Rent is represented once through its dated T12/T16 commitment.
        self.assertEqual(rent_day["upcoming_payment_total"], 2500)
        self.assertTrue(result["low_balance_warnings"]["warnings"])
        self.assertEqual(result["financial_risk"]["risk_level"], "CRITICAL")
        self.assertTrue(any(row["severity"] == "CRITICAL" for row in result["alerts"]))
        self.assertTrue(result["spending_recommendations"]["recommendations"])
        self.assertGreater(result["savings_analysis"]["potential_additional_monthly_savings"], 0)
        self.assertEqual(result["scenario_results"]["modified"], result["scenario_results"]["original"])
        self.assertTrue(result["ai_insights"]["insights"])
        self.assertTrue(result["prioritized_recommendations"]["recommendations"])
        self.assertIsNone(result["forecast_accuracy"])
        json.dumps(result, allow_nan=False)

    def test_empty_transactions_and_missing_budgets_are_safe(self):
        empty_path = self.root / "empty.csv"
        empty_path.write_text("", encoding="utf-8")
        result = run_full_analysis(
            empty_path, current_balance=400, minimum_balance=500,
            budgets=None, forecast_days=7, forecast_start_date="2026-04-01",
        )
        self.assertEqual(result["transaction_count"], 0)
        self.assertEqual(result["historical_summary"]["total_income"], 0)
        self.assertEqual(result["recurring_payments"], [])
        self.assertEqual(result["upcoming_payments"], [])
        self.assertEqual(len(result["cash_flow_forecast"]["forecast"]), 7)
        self.assertIsNone(result["forecast_accuracy"])
        json.dumps(result, allow_nan=False)

    def test_invalid_current_balance_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_pipeline(current_balance=float("nan"))
        with self.assertRaises(ValueError):
            self.run_pipeline(current_balance=float("inf"))

    def test_category_budgets_can_be_omitted(self):
        result = self.run_pipeline(budgets=None)
        self.assertIsInstance(result["overspending_results"]["categories"], list)
        self.assertTrue(all(row["budget"] is None for row in result["overspending_results"]["categories"]))
        self.assertFalse(any(row["budget_overrun"] for row in result["overspending_results"]["categories"]))

    def test_payment_on_balance_snapshot_date_is_outside_forecast_window(self):
        # The prediction starts the day after the current balance snapshot.
        # T12 must not add a payment due on the snapshot date as an extra day.
        result = self.run_pipeline(forecast_start_date="2026-04-05")
        forecast_dates = {row["date"] for row in result["cash_flow_forecast"]["forecast"]}
        self.assertNotIn("2026-04-05", forecast_dates)
        self.assertTrue(all(
            row["expected_payment_date"] in forecast_dates
            for row in result["upcoming_payments"]
        ))

    def test_accuracy_runs_only_with_actual_values_on_matching_forecast_dates(self):
        matching = self.root / "actual_matching.csv"
        pd.DataFrame([
            ("2026-04-02", "Salary", 5000, "credit"),
        ], columns=["date", "description", "amount", "type"]).to_csv(matching, index=False)
        matching_result = self.run_pipeline(actual_csv=matching)
        self.assertIsNotNone(matching_result["forecast_accuracy"])
        self.assertEqual(matching_result["forecast_accuracy"]["income"]["sample_count"], 1)

        mismatched = self.root / "actual_mismatched.csv"
        pd.DataFrame([
            ("2026-03-31", "Salary", 5000, "credit"),
        ], columns=["date", "description", "amount", "type"]).to_csv(mismatched, index=False)
        mismatched_result = self.run_pipeline(actual_csv=mismatched)
        self.assertIsNone(mismatched_result["forecast_accuracy"])
        self.assertIn("no usable measure", mismatched_result["forecast_accuracy_status"])

    def test_t32_accepts_actual_balance_only_csv_when_dates_match(self):
        actual_balance_path = self.root / "actual_balance.csv"
        pd.DataFrame([
            ("2026-04-02", 900),
        ], columns=["date", "balance"]).to_csv(actual_balance_path, index=False)
        result = self.run_pipeline(actual_csv=actual_balance_path)
        self.assertIsNotNone(result["forecast_accuracy"])
        self.assertEqual(result["forecast_accuracy"]["balance"]["sample_count"], 1)
        self.assertEqual(result["forecast_accuracy"]["income"]["sample_count"], 0)

    def test_direct_cli_emits_valid_json_on_legacy_windows_console(self):
        project_root = Path(__file__).resolve().parents[1]
        runner_path = project_root / "ai_engine" / "run_full_analysis.py"
        process = subprocess.run(
            [
                sys.executable, str(runner_path), str(self.transactions_path),
                "--current-balance", "1000", "--minimum-balance", "500",
                "--forecast-days", "7", "--forecast-start-date", "2026-04-01",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        result = json.loads(process.stdout)
        self.assertEqual(result["transaction_count"], len(self.transactions))


if __name__ == "__main__":
    unittest.main()
