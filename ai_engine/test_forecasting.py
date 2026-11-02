"""Tests for T15 cash-flow forecasting."""

import unittest

import pandas as pd

try:
    from .forecasting import forecast_cash_flow
except ImportError:
    from forecasting import forecast_cash_flow


class ForecastingTests(unittest.TestCase):
    def setUp(self):
        self.transactions = pd.DataFrame([
            ("2026-01-05", "Salary", 3100, "credit", "Income"),
            ("2026-01-10", "Rent", 310, "debit", "Housing"),
            ("2026-02-05", "Salary", 6200, "credit", "Income"),
            ("2026-02-10", "Rent", 620, "debit", "Housing"),
            ("2026-03-05", "Salary", 9300, "credit", "Income"),
            ("2026-03-10", "Rent", 930, "debit", "Housing"),
        ], columns=["date", "description", "amount", "type", "category"])

    def test_forecast_uses_recent_monthly_average_and_returns_values(self):
        result = forecast_cash_flow(self.transactions, forecast_days=7, forecast_start_date="2026-04-01")
        self.assertEqual(len(result["forecast"]), 7)
        self.assertEqual(result["forecast"][0]["date"], "2026-04-02")
        self.assertGreater(result["total_predicted_income"], 0)
        self.assertLess(result["total_predicted_expenses"], result["total_predicted_income"])
        self.assertEqual(result["predicted_net_cash_flow"], round(
            result["total_predicted_income"] - result["total_predicted_expenses"], 2
        ))
        self.assertFalse(result["insufficient_history"])

    def test_supports_7_30_and_90_day_horizons(self):
        for days in (7, 30, 90):
            with self.subTest(days=days):
                result = forecast_cash_flow(self.transactions, forecast_days=days,
                                            forecast_start_date="2026-04-01")
                self.assertEqual(len(result["forecast"]), days)

    def test_empty_and_invalid_history_return_safe_forecasts(self):
        empty = forecast_cash_flow(pd.DataFrame(columns=["date", "description", "amount", "type"]),
                                   forecast_days=7, forecast_start_date="2026-04-01")
        invalid = forecast_cash_flow(pd.DataFrame([
            ("bad-date", "Bad date", 400, "debit"),
            ("2026-04-01", "Bad amount", "unknown", "debit"),
        ], columns=["date", "description", "amount", "type"]),
            forecast_days=7, forecast_start_date="2026-04-01")
        self.assertTrue(empty["insufficient_history"])
        self.assertEqual(empty["total_predicted_income"], 0)
        self.assertTrue(invalid["insufficient_history"])
        self.assertEqual(invalid["total_predicted_expenses"], 0)

    def test_missing_history_columns_are_treated_as_insufficient(self):
        result = forecast_cash_flow(pd.DataFrame([{"unrelated": "value"}]),
                                    forecast_days=7, forecast_start_date="2026-04-01")
        self.assertTrue(result["insufficient_history"])
        self.assertEqual(result["total_predicted_income"], 0)

    def test_rejects_unsupported_horizon_and_invalid_start(self):
        with self.assertRaises(ValueError):
            forecast_cash_flow(self.transactions, forecast_days=14)
        with self.assertRaises(ValueError):
            forecast_cash_flow(self.transactions, forecast_start_date="not-a-date")


if __name__ == "__main__":
    unittest.main()
