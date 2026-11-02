"""Tests for T16 daily balance prediction."""

import unittest

try:
    from .balance_prediction import predict_daily_balances
except ImportError:
    from balance_prediction import predict_daily_balances


class BalancePredictionTests(unittest.TestCase):
    def test_applies_income_expenses_and_upcoming_payments(self):
        forecast = {"forecast": [
            {"date": "2026-11-01", "predicted_income": 100, "predicted_expenses": 20},
            {"date": "2026-11-02", "predicted_income": 100, "predicted_expenses": 20},
        ], "includes_upcoming_payments": False}
        payments = {"upcoming_payments": [
            {"description": "Rent", "expected_amount": 250, "expected_payment_date": "2026-11-02"},
        ]}
        result = predict_daily_balances(forecast, 1000, upcoming_payments=payments)
        self.assertEqual(result["daily_balances"][0]["expected_balance"], 1080)
        self.assertEqual(result["daily_balances"][1]["expected_balance"], 910)
        self.assertEqual(result["ending_balance"], 910)

    def test_duplicate_commitment_is_only_counted_once(self):
        forecast = {"forecast": [{
            "date": "2026-11-02", "predicted_income": 0, "predicted_expenses": 0,
        }]}
        payment = {"description": "Rent", "expected_amount": 250,
                   "expected_payment_date": "2026-11-02"}
        result = predict_daily_balances(forecast, 1000, upcoming_payments=[payment, payment.copy()])
        self.assertEqual(result["daily_balances"][0]["upcoming_payment_total"], 250)
        self.assertEqual(result["ending_balance"], 750)

    def test_does_not_overlay_commitments_already_in_forecast(self):
        forecast = {"forecast": [{
            "date": "2026-11-02", "predicted_income": 0, "predicted_expenses": 250,
        }], "includes_upcoming_payments": True}
        payment = {"description": "Rent", "expected_amount": 250,
                   "expected_payment_date": "2026-11-02"}
        result = predict_daily_balances(forecast, 1000, upcoming_payments=[payment])
        self.assertEqual(result["ending_balance"], 750)
        self.assertEqual(result["daily_balances"][0]["upcoming_payment_total"], 0)

    def test_invalid_forecast_rows_and_payments_are_skipped(self):
        result = predict_daily_balances({"forecast": [
            {"date": "bad-date", "predicted_income": 900, "predicted_expenses": 0},
            {"date": "2026-11-02", "predicted_income": "bad", "predicted_expenses": 10},
        ]}, 500, upcoming_payments=[{
            "description": "Broken", "expected_amount": "NaN", "expected_payment_date": "2026-11-02",
        }])
        self.assertEqual(result["ending_balance"], 490)
        self.assertEqual(len(result["daily_balances"]), 1)

    def test_invalid_starting_balance_is_rejected(self):
        with self.assertRaises(ValueError):
            predict_daily_balances({"forecast": []}, "not-a-balance")


if __name__ == "__main__":
    unittest.main()
