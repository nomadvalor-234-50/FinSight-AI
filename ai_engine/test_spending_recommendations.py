"""Tests for T24 evidence-based spending recommendations."""

import unittest

import pandas as pd

try:
    from .spending_recommendations import generate_spending_recommendations
except ImportError:
    from spending_recommendations import generate_spending_recommendations


class SpendingRecommendationTests(unittest.TestCase):
    def test_recommends_reduction_from_actual_budget_overrun(self):
        transactions = pd.DataFrame([
            ("2026-01-05", "Groceries", 1200, "debit", "Food"),
            ("2026-01-10", "Salary", 3000, "credit", "Income"),
        ], columns=["date", "description", "amount", "type", "category"])
        result = generate_spending_recommendations(transactions, {"Food": 1000})
        recommendation = result["recommendations"][0]
        self.assertEqual(recommendation["category"], "Food")
        self.assertEqual(recommendation["estimated_monthly_savings"], 100)
        self.assertIn("budget", recommendation["explanation"])

    def test_budget_and_historical_spend_are_distinct_evidence(self):
        history = {
            "total_income": 3000, "total_expenses": 1000,
            "average_monthly_income": 3000, "average_monthly_expenses": 1000,
            "monthly_summary": [{"month": "2026-01"}],
            "category_wise_expenses": {"Food": 1000},
        }
        result = generate_spending_recommendations(
            history, {"Food": 1500}, historical_category_spending={"Food": 400}
        )
        self.assertEqual(len(result["recommendations"]), 1)
        self.assertIn("unusual_vs_history", result["recommendations"][0]["evidence"])

    def test_subscription_recommendation_requires_budget_evidence_and_recurrence(self):
        transactions = pd.DataFrame([
            (f"2026-{month:02d}-05", "Netflix monthly subscription", 649, "debit", "Subscription")
            for month in (1, 2, 3)
        ], columns=["date", "description", "amount", "type", "category"])
        recurring = [{
            "description": "Netflix monthly subscription", "average_amount": 649,
            "frequency": "Monthly", "occurrences": 3, "is_recurring": True,
        }]
        result = generate_spending_recommendations(
            transactions, {"Subscription": 500}, recurring_results=recurring + [recurring[0].copy()]
        )
        self.assertEqual(len(result["recommendations"]), 1)
        row = result["recommendations"][0]
        self.assertIn("Review recurring subscription", row["title"])
        self.assertIn("recurring_transaction", row["evidence"])
        self.assertNotIn("cancel", row["suggested_action"].lower())
        self.assertLessEqual(row["estimated_monthly_savings"], 149)

    def test_does_not_claim_subscription_is_unnecessary_without_evidence(self):
        transactions = pd.DataFrame([
            (f"2026-{month:02d}-05", "Spotify", 119, "debit", "Subscription")
            for month in (1, 2, 3)
        ], columns=["date", "description", "amount", "type", "category"])
        recurring = [{"description": "Spotify", "average_amount": 119,
                      "frequency": "Monthly", "is_recurring": True}]
        result = generate_spending_recommendations(transactions, {}, recurring_results=recurring)
        self.assertEqual(result["recommendations"], [])

    def test_deduplicates_category_recommendations(self):
        history = {"monthly_summary": [{"month": "2026-01"}], "category_wise_expenses": {"Food": 500}}
        alert = {"category": "Food", "actual_spending": 700, "budget": 500,
                 "excess_amount": 200, "budget_overrun": True}
        result = generate_spending_recommendations(
            history, overspending_result={"alerts": [alert, alert.copy()]}
        )
        self.assertEqual(len(result["recommendations"]), 1)

    def test_empty_history_returns_no_recommendations(self):
        result = generate_spending_recommendations(pd.DataFrame(
            columns=["date", "description", "amount", "type"]
        ), budgets=None)
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(result["estimated_monthly_savings"], 0)


if __name__ == "__main__":
    unittest.main()
