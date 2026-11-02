"""Automated tests for upcoming recurring payment estimates."""

import unittest

try:  # Support both package-style and local test execution.
    from .upcoming_payment import (
        calculate_total_expected_amount,
        estimate_upcoming_payments,
        get_upcoming_payments,
    )
except ImportError:
    from upcoming_payment import (
        calculate_total_expected_amount,
        estimate_upcoming_payments,
        get_upcoming_payments,
    )


def recurring(description, amount, frequency, next_date, is_recurring=True):
    """Make a compact detector-style result for tests."""
    return {
        "description": description,
        "average_amount": amount,
        "frequency": frequency,
        "recurrence_interval_days": 30,
        "occurrences": 3,
        "next_payment_date": next_date,
        "is_recurring": is_recurring,
    }


class UpcomingPaymentTests(unittest.TestCase):
    def test_monthly_upcoming_payment(self):
        result = get_upcoming_payments(
            [recurring("House Rent", 10000, "Monthly", "2026-11-01")],
            horizon_days=30,
            as_of_date="2026-11-02",
        )
        self.assertEqual(result[0]["expected_payment_date"], "2026-12-01")
        self.assertEqual(result[0]["expected_amount"], 10000)

    def test_weekly_upcoming_payment(self):
        result = get_upcoming_payments(
            [recurring("Weekly transfer", 200, "Weekly", "2026-11-03")],
            horizon_days=8,
            as_of_date="2026-11-02",
        )
        self.assertEqual([row["expected_payment_date"] for row in result], ["2026-11-03", "2026-11-10"])

    def test_yearly_upcoming_payment(self):
        result = get_upcoming_payments(
            [recurring("Annual membership", 1200, "Yearly", "2027-01-10")],
            horizon_days=90,
            as_of_date="2026-11-02",
        )
        self.assertEqual(result[0]["expected_payment_date"], "2027-01-10")
        self.assertEqual(result[0]["frequency"], "Yearly")

    def test_multiple_payments_are_chronologically_sorted(self):
        results = [
            recurring("House Rent", 10000, "Monthly", "2026-11-01"),
            recurring("Netflix", 649, "Monthly", "2026-11-05"),
        ]
        forecast = estimate_upcoming_payments(results, horizon_days=35, as_of_date="2026-11-02")
        payments = forecast["upcoming_payments"]
        self.assertEqual(
            [row["expected_payment_date"] for row in payments],
            ["2026-11-05", "2026-12-01", "2026-12-05"],
        )

    def test_total_expected_payment_calculation(self):
        payments = [
            {"expected_amount": 10000},
            {"expected_amount": 649},
        ]
        self.assertEqual(calculate_total_expected_amount(payments), 10649)
        forecast = estimate_upcoming_payments(
            [
                recurring("House Rent", 10000, "Monthly", "2026-11-05"),
                recurring("Netflix", 649, "Monthly", "2026-11-06"),
            ],
            horizon_days=5,
            as_of_date="2026-11-02",
        )
        self.assertEqual(forecast["total_expected_amount"], 10649)

    def test_horizon_excludes_payments_after_window(self):
        result = get_upcoming_payments(
            [recurring("Netflix", 649, "Monthly", "2026-11-05")],
            horizon_days=2,
            as_of_date="2026-11-02",
        )
        self.assertEqual(result, [])

    def test_invalid_dates_and_amounts_are_skipped(self):
        results = [
            recurring("Bad date", 20, "Monthly", "not-a-date"),
            recurring("Bad amount", "NaN", "Monthly", "2026-11-05"),
            recurring("Missing amount", None, "Weekly", "2026-11-05"),
            recurring("Good record", 50, "Weekly", "2026-11-05"),
        ]
        payments = get_upcoming_payments(results, horizon_days=7, as_of_date="2026-11-02")
        self.assertTrue(payments)
        self.assertTrue(all(row["description"] == "Good record" for row in payments))

    def test_non_recurring_and_irregular_results_are_excluded(self):
        results = [
            recurring("Irregular transfer", 500, "Irregular", None, is_recurring=False),
            recurring("Unconfirmed", 200, "Weekly", "2026-11-05", is_recurring=False),
        ]
        self.assertEqual(
            get_upcoming_payments(results, horizon_days=30, as_of_date="2026-11-02"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
