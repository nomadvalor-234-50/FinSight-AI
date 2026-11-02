from collections import defaultdict
from datetime import timedelta
from statistics import mean


def detect_recurring_transactions(transactions):

    groups = defaultdict(list)

    # 1. Group transactions
    for transaction in transactions:

        description = " ".join(
            transaction.description.strip().casefold().split()
        )

        category = (
            transaction.category.strip().casefold()
            if transaction.category
            else ""
        )

        key = (
            description,
            category,
            transaction.transaction_type
        )

        groups[key].append(transaction)

    recurring_payments = []

    # 2. Analyze each group
    for key, records in groups.items():

        if len(records) < 3:
            continue

        records.sort(
            key=lambda item: item.transaction_date
        )

        dates = [
            item.transaction_date
            for item in records
        ]

        amounts = [
            float(item.amount)
            for item in records
        ]

        # 3. Calculate intervals
        intervals = [
            (dates[i] - dates[i - 1]).days
            for i in range(1, len(dates))
        ]

        average_interval = mean(intervals)

        # 4. Identify payment frequency
        if 6 <= average_interval <= 8:
            frequency = "Weekly"

        elif 25 <= average_interval <= 35:
            frequency = "Monthly"

        else:
            continue

        # Check consistency of intervals
        if frequency == "Weekly":
            consistent = all(
                6 <= interval <= 8
                for interval in intervals
            )

        else:
            consistent = all(
                25 <= interval <= 35
                for interval in intervals
            )

        if not consistent:
            continue

        # 5. Calculate average amount
        average_amount = round(
            mean(amounts), 2
        )

        # 6. Estimate next payment date
        next_payment_date = (
            dates[-1] + timedelta(
                days=round(average_interval)
            )
        )

        recurring_payments.append({
            "description": records[-1].description,
            "category": records[-1].category,
            "transaction_type": records[-1].transaction_type,
            "frequency": frequency,
            "average_amount": average_amount,
            "occurrences": len(records),
            "average_interval_days": round(
                average_interval, 1
            ),
            "last_payment_date": dates[-1].isoformat(),
            "next_expected_date": (
                next_payment_date.isoformat()
            )
        })

    return recurring_payments