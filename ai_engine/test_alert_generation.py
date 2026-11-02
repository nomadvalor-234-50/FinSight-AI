"""Tests for T21 alert generation from existing detector outputs."""

import unittest

try:
    from .alert_generation import generate_alerts
except ImportError:
    from alert_generation import generate_alerts


class AlertGenerationTests(unittest.TestCase):
    def test_generates_low_balance_alert_with_affected_date(self):
        alerts = generate_alerts(low_balance_result={"warnings": [{
            "start_date": "2026-11-03", "end_date": "2026-11-04",
            "lowest_predicted_balance": 500, "threshold": 1000,
        }]})
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["severity"], "HIGH")
        self.assertEqual(alerts[0]["affected_date"], "2026-11-03")
        self.assertTrue(alerts[0]["suggested_action"])

    def test_generates_overspending_with_medium_or_high_severity(self):
        alerts = generate_alerts(overspending_result={"alerts": [{
            "category": "Food", "actual_spending": 1500, "budget": 1000,
            "excess_amount": 500, "overspending_percentage": 50,
            "budget_overrun": True, "alert_reasons": ["budget_overrun"],
        }]})
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["severity"], "HIGH")
        self.assertIn("500.00", alerts[0]["reason"])

    def test_generates_negative_cash_flow_and_critical_risk_alerts(self):
        alerts = generate_alerts(
            forecast={"predicted_net_cash_flow": -250, "forecast": [
                {"date": "2026-11-05", "predicted_net_cash_flow": -10},
            ]},
            risk_result={"risk_level": "CRITICAL", "reasons": ["negative balance"]},
        )
        by_title = {alert["title"]: alert for alert in alerts}
        self.assertEqual(by_title["Negative forecast cash flow"]["severity"], "HIGH")
        self.assertEqual(by_title["Negative forecast cash flow"]["affected_date"], "2026-11-05")
        self.assertEqual(by_title["Critical financial risk"]["severity"], "CRITICAL")

    def test_deduplicates_same_event_and_ignores_undetected_conditions(self):
        low_event = {"start_date": "2026-11-03", "end_date": "2026-11-03",
                     "lowest_predicted_balance": 500, "threshold": 1000}
        overspend = {"category": "Food", "actual_spending": 1200, "budget": 1000,
                     "excess_amount": 200, "overspending_percentage": 20,
                     "budget_overrun": True, "alert_reasons": ["budget_overrun"]}
        alerts = generate_alerts(
            low_balance_result={"warnings": [low_event, low_event.copy()]},
            overspending_result={"alerts": [overspend, overspend.copy()]},
            forecast={"predicted_net_cash_flow": 50},
            risk_result={"risk_level": "LOW", "reasons": []},
        )
        self.assertEqual(len(alerts), 2)
        self.assertEqual({row["title"] for row in alerts}, {"Low balance warning", "Overspending in Food"})

    def test_negative_balance_low_alert_is_critical(self):
        alerts = generate_alerts(low_balance_result={"warnings": [{
            "start_date": "2026-11-03", "end_date": "2026-11-03",
            "lowest_predicted_balance": -20, "threshold": 1000,
        }]})
        self.assertEqual(alerts[0]["severity"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
