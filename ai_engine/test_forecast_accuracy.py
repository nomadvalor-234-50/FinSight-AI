"""Tests for T32 date-aligned forecast error metrics."""

import unittest

import pandas as pd

try:
    from .forecast_accuracy import calculate_forecast_accuracy
except ImportError:
    from forecast_accuracy import calculate_forecast_accuracy


class ForecastAccuracyTests(unittest.TestCase):
    def test_correct_mae_and_rmse(self):
        predicted = {"forecast": [
            {"date": "2026-01-01", "predicted_income": 100, "predicted_expenses": 50},
            {"date": "2026-01-02", "predicted_income": 200, "predicted_expenses": 80},
        ]}
        actual = pd.DataFrame([
            ("2026-01-01", "credit", 90), ("2026-01-01", "debit", 60),
            ("2026-01-02", "credit", 220), ("2026-01-02", "debit", 90),
        ], columns=["date", "type", "amount"])
        result = calculate_forecast_accuracy(predicted, actual)
        self.assertEqual(result["income"]["mae"], 15)
        self.assertEqual(result["income"]["rmse"], 15.8114)
        self.assertEqual(result["expenses"]["mae"], 10)
        self.assertEqual(result["expenses"]["rmse"], 10)
        self.assertEqual(result["income"]["sample_count"], 2)

    def test_calculates_account_balance_metrics(self):
        predicted = {"forecast": [{"date": "2026-02-01", "predicted_income": 100,
                                   "predicted_expenses": 50}]}
        predicted_balances = {"daily_balances": [
            {"date": "2026-02-01", "expected_balance": 1000},
            {"date": "2026-02-02", "expected_balance": 900},
        ]}
        actual = pd.DataFrame([
            ("2026-02-01", "credit", 100, 990),
            ("2026-02-02", "debit", 50, 910),
        ], columns=["date", "type", "amount", "actual_balance"])
        result = calculate_forecast_accuracy(predicted, actual, predicted_balances=predicted_balances)
        self.assertEqual(result["balance"]["sample_count"], 2)
        self.assertEqual(result["balance"]["mae"], 10)
        self.assertEqual(result["balance"]["rmse"], 10)

    def test_empty_inputs_return_zero_samples_and_no_error_metrics(self):
        result = calculate_forecast_accuracy([], [])
        for measure in ("income", "expenses", "balance"):
            self.assertEqual(result[measure]["sample_count"], 0)
            self.assertIsNone(result[measure]["mae"])
            self.assertIsNone(result[measure]["rmse"])

    def test_invalid_numbers_and_dates_are_skipped(self):
        predicted = {"forecast": [
            {"date": "2026-03-01", "predicted_income": "bad", "predicted_expenses": float("nan")},
            {"date": "invalid", "predicted_income": 100, "predicted_expenses": 20},
        ]}
        actual = pd.DataFrame([
            ("2026-03-01", "credit", 50),
            ("bad-date", "debit", 10),
        ], columns=["date", "type", "amount"])
        result = calculate_forecast_accuracy(predicted, actual)
        self.assertEqual(result["income"]["sample_count"], 0)
        self.assertEqual(result["expenses"]["sample_count"], 0)

    def test_mismatched_dates_are_not_compared(self):
        predicted = {"forecast": [{"date": "2026-04-01", "predicted_income": 100}]}
        actual = pd.DataFrame([("2026-04-02", "credit", 100)],
                              columns=["date", "type", "amount"])
        result = calculate_forecast_accuracy(predicted, actual)
        self.assertEqual(result["income"]["sample_count"], 0)
        self.assertEqual(result["income"]["unmatched_prediction_count"], 1)
        self.assertEqual(result["income"]["unmatched_actual_count"], 1)
        self.assertEqual(result["income"]["matched_dates"], [])

    def test_perfect_predictions_have_zero_error(self):
        predicted = {"forecast": [
            {"date": "2026-05-01", "predicted_income": 100, "predicted_expenses": 20},
        ]}
        actual = [{"date": "2026-05-01", "income": 100, "expenses": 20, "balance": 500}]
        result = calculate_forecast_accuracy(
            predicted, actual,
            predicted_balances=[{"date": "2026-05-01", "expected_balance": 500}],
        )
        for measure in ("income", "expenses", "balance"):
            self.assertEqual(result[measure]["mae"], 0)
            self.assertEqual(result[measure]["rmse"], 0)
        self.assertIn("not percentage accuracy", result["metric_note"])


if __name__ == "__main__":
    unittest.main()
