"""Tests for T20 explainable risk rules and pipeline integration."""

import unittest

import pandas as pd

try:
    from .balance_prediction import predict_daily_balances
    from .financial_risk import classify_financial_risk
    from .forecasting import forecast_cash_flow
    from .low_balance_detection import detect_low_balance
    from .overspending_detection import detect_overspending
except ImportError:
    from balance_prediction import predict_daily_balances
    from financial_risk import classify_financial_risk
    from forecasting import forecast_cash_flow
    from low_balance_detection import detect_low_balance
    from overspending_detection import detect_overspending


class FinancialRiskTests(unittest.TestCase):
    def test_low_risk_when_no_rules_are_triggered(self):
        result = classify_financial_risk()
        self.assertEqual(result["risk_level"], "LOW")
        self.assertEqual(result["risk_score"], 0)
        self.assertTrue(result["reasons"])

    def test_medium_risk_for_negative_forecast_cash_flow(self):
        result = classify_financial_risk(forecast={"predicted_net_cash_flow": -100})
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertEqual(result["risk_score"], 20)

    def test_high_risk_for_low_balance_and_negative_cash_flow(self):
        result = classify_financial_risk(
            forecast={"predicted_net_cash_flow": -100},
            low_balance_result={"warning_count": 1, "warnings": [{}]},
        )
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertEqual(result["risk_score"], 45)

    def test_critical_risk_when_a_predicted_balance_is_negative(self):
        result = classify_financial_risk(balance_prediction={
            "daily_balances": [{"date": "2026-01-01", "expected_balance": -1}],
        })
        self.assertEqual(result["risk_level"], "CRITICAL")
        self.assertGreaterEqual(result["risk_score"], 70)
        self.assertIn("below zero", result["reasons"][0])

    def test_critical_risk_checks_ending_balance_even_without_daily_rows(self):
        result = classify_financial_risk(balance_prediction={"ending_balance": -25})
        self.assertEqual(result["risk_level"], "CRITICAL")

    def test_overspending_contributes_to_score_and_reason(self):
        result = classify_financial_risk(overspending_result={"alerts": [
            {"budget_overrun": True, "unusual_spending": True},
        ]})
        self.assertEqual(result["risk_score"], 20)
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertEqual(len(result["reasons"]), 2)

    def test_end_to_end_t15_to_t20_integration(self):
        transactions = pd.DataFrame([
            ("2026-01-05", "Salary", 3000, "credit", "Income"),
            ("2026-01-10", "Food", 500, "debit", "Food"),
            ("2026-02-05", "Salary", 3000, "credit", "Income"),
            ("2026-02-10", "Food", 500, "debit", "Food"),
        ], columns=["date", "description", "amount", "type", "category"])
        forecast = forecast_cash_flow(transactions, forecast_days=7, forecast_start_date="2026-03-01")
        payment_result = {"upcoming_payments": [{
            "description": "Rent", "expected_amount": 2500,
            "frequency": "Monthly", "expected_payment_date": "2026-03-03",
        }]}
        balances = predict_daily_balances(forecast, current_balance=1000,
                                          upcoming_payments=payment_result)
        low_balances = detect_low_balance(balances, minimum_balance=0)
        overspending = detect_overspending(
            {"Food": 700}, {"Food": 500}, historical_category_spending={"Food": 300}
        )
        risk = classify_financial_risk(forecast, balances, low_balances, overspending)
        self.assertEqual(len(forecast["forecast"]), 7)
        self.assertEqual(balances["daily_balances"][1]["upcoming_payment_total"], 2500)
        self.assertGreaterEqual(low_balances["warning_count"], 1)
        self.assertIn(risk["risk_level"], {"LOW", "MEDIUM", "HIGH", "CRITICAL"})
        self.assertTrue(risk["reasons"])
        self.assertIn("rule-based", risk["classification_method"])


if __name__ == "__main__":
    unittest.main()
