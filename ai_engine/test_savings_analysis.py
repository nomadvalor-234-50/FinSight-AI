"""Tests for T25 current and potential savings calculations."""

import unittest

try:
    from .savings_analysis import analyze_savings
except ImportError:
    from savings_analysis import analyze_savings


class SavingsAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.history = {
            "total_income": 6000, "total_expenses": 4000, "net_cash_flow": 2000,
            "average_monthly_income": 3000, "average_monthly_expenses": 2000,
            "monthly_summary": [{"month": "2026-01"}, {"month": "2026-02"}],
            "category_wise_expenses": {"Food": 1000, "Transport": 3000},
        }

    def test_calculates_surplus_rates_and_monthly_yearly_potential(self):
        recommendations = {"recommendations": [{
            "title": "Review food spend", "category": "Food", "estimated_monthly_savings": 100,
        }]}
        result = analyze_savings(self.history, recommendations)
        self.assertEqual(result["total_income"], 6000)
        self.assertEqual(result["total_expenses"], 4000)
        self.assertEqual(result["current_surplus"], 2000)
        self.assertEqual(result["current_savings_rate_percentage"], 33.33)
        self.assertEqual(result["potential_additional_monthly_savings"], 100)
        self.assertEqual(result["potential_additional_yearly_savings"], 1200)
        self.assertEqual(result["projected_savings_rate_percentage"], 36.67)

    def test_zero_income_has_no_rate_and_negative_surplus_is_preserved(self):
        history = {
            "total_income": 0, "total_expenses": 500, "monthly_summary": [{"month": "2026-01"}],
            "average_monthly_income": 0, "average_monthly_expenses": 500,
            "category_wise_expenses": {"Food": 500},
        }
        result = analyze_savings(history, [{
            "title": "Reduce food", "category": "Food", "estimated_monthly_savings": 700,
        }])
        self.assertEqual(result["current_surplus"], -500)
        self.assertIsNone(result["current_savings_rate_percentage"])
        self.assertIsNone(result["projected_savings_rate_percentage"])
        self.assertEqual(result["potential_additional_monthly_savings"], 500)

    def test_duplicate_and_overlapping_savings_are_capped_by_category_spend(self):
        recommendations = [
            {"title": "Trim groceries", "category": "Food", "estimated_monthly_savings": 350},
            {"title": "Trim groceries", "category": "Food", "estimated_monthly_savings": 350},
            {"title": "Reduce takeaway", "category": "Food", "estimated_monthly_savings": 350},
        ]
        result = analyze_savings(self.history, recommendations)
        self.assertEqual(len(result["recommendation_breakdown"]), 2)
        self.assertEqual(result["potential_additional_monthly_savings"], 500)
        self.assertFalse(result["potential_savings_are_guaranteed"])

    def test_empty_data_returns_safe_zero_result(self):
        result = analyze_savings({
            "total_income": 0, "total_expenses": 0, "monthly_summary": [],
            "category_wise_expenses": {},
        })
        self.assertEqual(result["current_surplus"], 0)
        self.assertEqual(result["potential_additional_yearly_savings"], 0)
        self.assertIsNone(result["current_savings_rate_percentage"])


if __name__ == "__main__":
    unittest.main()
