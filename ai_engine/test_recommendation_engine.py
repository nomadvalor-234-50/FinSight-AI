"""Tests for T31 prioritization and deduplication."""

import unittest

try:
    from .recommendation_engine import build_recommendations
except ImportError:
    from recommendation_engine import build_recommendations


class RecommendationEngineTests(unittest.TestCase):
    def test_uses_financial_data_and_prioritizes_urgent_before_benefit(self):
        result = build_recommendations(
            spending_recommendations={"recommendations": [
                {"title": "Trim food spend", "category": "Food", "explanation": "Over budget",
                 "suggested_action": "Review purchases", "estimated_monthly_savings": 300},
                {"title": "Review transport", "category": "Transport", "explanation": "Above history",
                 "suggested_action": "Plan trips", "estimated_monthly_savings": 900},
            ]},
            risk_result={"risk_level": "MEDIUM"},
            alerts=[{"title": "Overspending in Food", "category": "Food", "severity": "CRITICAL"}],
        )
        self.assertEqual(result["recommendations"][0]["title"], "Trim food spend")
        self.assertEqual(result["recommendations"][0]["priority"], "URGENT")
        self.assertEqual(result["recommendations"][1]["priority"], "MEDIUM")
        self.assertEqual(result["recommendations"][0]["estimated_financial_benefit"], 300)

    def test_uses_savings_analysis_when_no_itemized_suggestion_exists(self):
        result = build_recommendations(
            savings_analysis={"potential_additional_monthly_savings": 250},
            risk_result={"risk_level": "LOW"},
        )
        self.assertEqual(len(result["recommendations"]), 1)
        self.assertEqual(result["recommendations"][0]["estimated_financial_benefit"], 250)
        self.assertFalse(result["recommendations"][0]["benefit_is_guaranteed"])

    def test_generates_low_balance_prevention_recommendation(self):
        result = build_recommendations(alerts=[{
            "title": "Low balance warning", "severity": "HIGH", "affected_date": "2026-11-10",
            "suggested_action": "Review upcoming payments", "message": "Balance below threshold",
        }])
        row = result["recommendations"][0]
        self.assertIn("2026-11-10", row["title"])
        self.assertEqual(row["priority"], "HIGH")
        self.assertIsNone(row["estimated_financial_benefit"])

    def test_duplicate_recommendations_and_alerts_are_deduplicated(self):
        recommendation = {"title": "Trim food spend", "category": "Food",
                          "suggested_action": "Review purchases", "estimated_monthly_savings": 100}
        alert = {"title": "Low balance warning", "severity": "HIGH", "affected_date": "2026-11-10"}
        result = build_recommendations(
            spending_recommendations={"recommendations": [recommendation, recommendation.copy()]},
            alerts=[alert, alert.copy()],
        )
        self.assertEqual(result["recommendation_count"], 2)
        self.assertEqual(sum(row["estimated_financial_benefit"] or 0 for row in result["recommendations"]), 100)

    def test_critical_risk_is_used_and_missing_data_is_safe(self):
        result = build_recommendations(risk_result={"risk_level": "CRITICAL", "reasons": ["negative balance"]})
        self.assertEqual(result["recommendations"][0]["priority"], "URGENT")
        empty = build_recommendations()
        self.assertEqual(empty["recommendations"], [])


if __name__ == "__main__":
    unittest.main()
