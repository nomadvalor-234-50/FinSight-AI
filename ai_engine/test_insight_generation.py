"""Tests for T30 rule-based financial insight generation."""

import unittest

try:
    from .insight_generation import generate_insights
except ImportError:
    from insight_generation import generate_insights


class InsightGenerationTests(unittest.TestCase):
    def test_explains_all_four_risk_levels_and_reasons(self):
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            with self.subTest(level=level):
                result = generate_insights(risk_result={
                    "risk_level": level, "risk_score": 30, "reasons": ["projected cash flow is negative"],
                })
                self.assertEqual(result["insights"][0]["severity"], level)
                self.assertIn("projected cash flow is negative", result["insights"][0]["message"])

    def test_explains_low_balance_and_overspending_with_details(self):
        result = generate_insights(
            low_balance_result={"warnings": [{
                "start_date": "2026-11-04", "lowest_predicted_balance": 450, "threshold": 1000,
            }]},
            overspending_result={"alerts": [{
                "category": "Food", "actual_spending": 1500, "budget": 1000,
                "budget_overrun": True, "alert_reasons": ["budget_overrun"],
            }]},
        )
        by_type = {row["type"]: row for row in result["insights"]}
        self.assertIn("2026-11-04", by_type["low_balance"]["message"])
        self.assertIn("Food", by_type["overspending"]["message"])
        self.assertIn("₹1,500.00", by_type["overspending"]["message"])

    def test_reports_spending_trend_and_forecast_change(self):
        result = generate_insights(
            historical_analysis={
                "expense_trend": "Increasing",
                "monthly_summary": [
                    {"month": "2026-01", "expenses": 1000, "net_cash_flow": 500},
                    {"month": "2026-02", "expenses": 1200, "net_cash_flow": 400},
                ],
            },
            forecast={
                "forecast_days": 30, "forecast_end_date": "2026-03-30",
                "predicted_net_cash_flow": 600, "total_predicted_income": 2000,
                "total_predicted_expenses": 1400,
            },
        )
        types = {row["type"] for row in result["insights"]}
        self.assertIn("expense_trend", types)
        self.assertIn("cash_flow_forecast", types)
        cash_flow = next(row for row in result["insights"] if row["type"] == "cash_flow_forecast")
        self.assertIn("higher", cash_flow["message"])

    def test_explains_predicted_ending_balance(self):
        result = generate_insights(balance_prediction={
            "ending_balance": 850, "daily_balances": [{"date": "2026-11-30", "expected_balance": 850}],
        })
        insight = result["insights"][0]
        self.assertEqual(insight["type"], "balance_prediction")
        self.assertIn("2026-11-30", insight["message"])

    def test_missing_and_empty_inputs_do_not_invent_insights(self):
        result = generate_insights()
        self.assertEqual(result["insights"], [])
        self.assertIn("No analysis results", result["summary"])
        empty = generate_insights(historical_analysis={"monthly_summary": [], "expense_trend": ""})
        self.assertEqual(empty["insights"], [])
        self.assertIn("no supported insight", empty["summary"])

    def test_unsupported_risk_level_is_not_reported_as_a_real_assessment(self):
        result = generate_insights(risk_result={"risk_level": "EXTREME", "risk_score": 900})
        self.assertEqual(result["insights"], [])


if __name__ == "__main__":
    unittest.main()
