from datetime import date, timedelta
from decimal import Decimal

from app.services.recurring_detector import (
    detect_recurring_transactions
)


def forecast_cash_flow(
    transactions,
    starting_balance,
    forecast_days=60
):

    # 1. Set forecast period
    today = date.today()
    forecast_end = today + timedelta(days=forecast_days)

    balance = Decimal(str(starting_balance))

    starting_balance = balance

    forecast_events = []

    # 2. Detect recurring transactions
    recurring_payments = detect_recurring_transactions(
        transactions
    )

    # 3. Generate upcoming payment events
    for payment in recurring_payments:

        interval = max(
            1,
            round(payment["average_interval_days"])
        )

        next_date = date.fromisoformat(
            payment["next_expected_date"]
        )

        # Move past dates into the future
        while next_date < today:
            next_date += timedelta(days=interval)

        # Generate future occurrences
        while next_date <= forecast_end:

            amount = Decimal(
                str(payment["average_amount"])
            )

            if payment["transaction_type"] == "expense":
                signed_amount = -amount
            else:
                signed_amount = amount

            forecast_events.append({
                "date": next_date,
                "description": payment["description"],
                "category": payment["category"],
                "transaction_type": payment["transaction_type"],
                "frequency": payment["frequency"],
                "amount": signed_amount
            })

            next_date += timedelta(days=interval)

    # 4. Sort events chronologically
    forecast_events.sort(
        key=lambda event: event["date"]
    )

    # 5. Calculate projected balances
    forecast_results = []

    lowest_balance = balance

    for event in forecast_events:

        balance += event["amount"]

        lowest_balance = min(
            lowest_balance,
            balance
        )

        forecast_results.append({
            "date": event["date"].isoformat(),
            "description": event["description"],
            "category": event["category"],
            "transaction_type": event["transaction_type"],
            "amount": float(event["amount"]),
            "projected_balance": float(balance)
        })

    # 6. Generate financial warning
    if lowest_balance < 0:
        warning = "Potential cash shortage detected."
        risk_level = "high"

    elif lowest_balance < starting_balance * Decimal("0.2"):
        warning = "Your projected balance may become low."
        risk_level = "medium"

    else:
        warning = "No cash shortage detected from known recurring payments."
        risk_level = "low"

    # 7. Calculate final summary
    return {
        "forecast_start_date": today.isoformat(),
        "forecast_end_date": forecast_end.isoformat(),
        "forecast_days": forecast_days,
        "starting_balance": float(starting_balance),
        "projected_closing_balance": float(balance),
        "lowest_projected_balance": float(lowest_balance),
        "total_forecasted_events": len(forecast_results),
        "risk_level": risk_level,
        "warning": warning,
        "forecast_events": forecast_results
    }