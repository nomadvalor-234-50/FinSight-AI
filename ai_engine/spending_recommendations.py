"""T24: evidence-based, non-prescriptive spending recommendations."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .categorization import categorize_transaction
    from .historical_analysis import analyze_historical_transactions
    from .overspending_detection import detect_overspending
    from .recurring_detection import detect_recurring_payments
except ImportError:  # pragma: no cover - direct script execution
    from categorization import categorize_transaction
    from historical_analysis import analyze_historical_transactions
    from overspending_detection import detect_overspending
    from recurring_detection import detect_recurring_payments


def _monthly_amount(amount: Any, frequency: Any) -> float:
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value) or value <= 0:
        return 0.0
    normalized = str(frequency).strip().lower()
    if normalized == "weekly":
        return value * 52 / 12
    if normalized == "monthly":
        return value
    if normalized == "yearly":
        return value / 12
    return 0.0


def _is_subscription(description: Any) -> bool:
    text = str(description or "").strip()
    lower = text.lower()
    return (
        categorize_transaction(text) == "Subscription"
        or any(word in lower for word in ("subscription", "streaming", "membership"))
    )


def _savings_target(row: dict[str, Any], multiplier: float) -> float:
    """Set conservative savings to half of budget excess or 25% of excess trend."""
    targets: list[float] = []
    if row.get("budget_overrun"):
        try:
            targets.append(max(0.0, float(row.get("excess_amount", 0))) * 0.5)
        except (TypeError, ValueError):
            pass
    if row.get("unusual_spending"):
        try:
            actual = float(row.get("actual_spending", 0))
            baseline = float(row.get("historical_monthly_average"))
            targets.append(max(0.0, actual - baseline * multiplier) * 0.25)
        except (TypeError, ValueError):
            pass
    return max(targets, default=0.0)


def generate_spending_recommendations(
    transactions: pd.DataFrame | str | Path | dict[str, Any],
    budgets: dict[str, Any] | None = None,
    *,
    overspending_result: dict[str, Any] | None = None,
    recurring_results: list[dict[str, Any]] | None = None,
    historical_category_spending: Any = None,
) -> dict[str, Any]:
    """Return monthly savings suggestions grounded in T14/T19/T10 evidence.

    A category recommendation targets 50% of a verified budget excess, or 25%
    of spending above a 1.5x historical norm. When a subscription category has
    such evidence, detected recurring subscriptions are suggested for review,
    never automatic cancellation; their combined savings estimate is capped
    by the category target and 25% of observed monthly subscription charges.
    """
    if isinstance(transactions, dict):
        history = transactions
        raw_transactions = None
    else:
        history = analyze_historical_transactions(transactions)
        raw_transactions = transactions

    month_count = max(1, len(history.get("monthly_summary", [])))
    actual_monthly = {
        category: amount / month_count
        for category, amount in history.get("category_wise_expenses", {}).items()
    }
    if overspending_result is None:
        overspending_result = detect_overspending(
            actual_monthly,
            budgets,
            historical_category_spending=historical_category_spending,
        )
    if not isinstance(overspending_result, dict):
        overspending_result = {}

    multiplier = overspending_result.get("unusual_multiplier", 1.5)
    try:
        multiplier = float(multiplier)
    except (TypeError, ValueError):
        multiplier = 1.5
    if not math.isfinite(multiplier) or multiplier <= 1:
        multiplier = 1.5

    alerts = overspending_result.get("alerts", [])
    alerts = alerts if isinstance(alerts, list) else []
    subscriptions = recurring_results
    if subscriptions is None and raw_transactions is not None:
        subscriptions = detect_recurring_payments(raw_transactions)
    subscriptions = subscriptions if isinstance(subscriptions, list) else []

    recommendations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        category = str(alert.get("category", "")).strip()
        if not category:
            continue
        budget_overrun = bool(alert.get("budget_overrun"))
        unusual = bool(alert.get("unusual_spending"))
        if not (budget_overrun or unusual):
            continue
        target = _savings_target(alert, multiplier)
        if target <= 0:
            continue

        category_subscriptions = [
            row for row in subscriptions
            if isinstance(row, dict)
            and row.get("is_recurring") is True
            and _is_subscription(row.get("description", ""))
        ] if category.lower() == "subscription" else []
        unique_subscriptions: dict[tuple[str, str, float], dict[str, Any]] = {}
        for row in category_subscriptions:
            cost = _monthly_amount(row.get("average_amount"), row.get("frequency"))
            key = (str(row.get("description", "")).strip().casefold(),
                   str(row.get("frequency", "")).strip().casefold(), round(cost, 2))
            unique_subscriptions.setdefault(key, row)
        category_subscriptions = list(unique_subscriptions.values())

        if category_subscriptions:
            costs = [
                _monthly_amount(row.get("average_amount"), row.get("frequency"))
                for row in category_subscriptions
            ]
            total_recurring_monthly = sum(costs)
            achievable_estimate = min(target, total_recurring_monthly * 0.25)
            if total_recurring_monthly > 0 and achievable_estimate > 0:
                for row, cost in zip(category_subscriptions, costs):
                    if cost <= 0:
                        continue
                    title = f"Review recurring subscription: {str(row.get('description', '')).strip()}"
                    key = (category.casefold(), title.casefold())
                    if key in seen:
                        continue
                    seen.add(key)
                    recommendations.append({
                        "title": title,
                        "category": category,
                        "explanation": (
                            f"{category} spending exceeded a detected threshold, and "
                            f"{row.get('description')} is a confirmed recurring payment."
                        ),
                        "suggested_action": (
                            "Review whether you still use this service; consider pausing it only if it is no longer needed."
                        ),
                        "estimated_monthly_savings": round(achievable_estimate * cost / total_recurring_monthly, 2),
                        "evidence": ["category_spending_threshold", "recurring_transaction"],
                        "savings_are_estimates": True,
                    })
                continue

        key = (category.casefold(), "category")
        if key in seen:
            continue
        seen.add(key)
        reasons = []
        if budget_overrun:
            reasons.append("spending exceeded the user-provided category budget")
        if unusual:
            reasons.append("spending was unusually high compared with historical category spending")
        recommendations.append({
            "title": f"Review {category} spending",
            "category": category,
            "explanation": f"{category} spending was flagged because " + " and ".join(reasons) + ".",
            "suggested_action": (
                f"Review recent {category.lower()} purchases and choose a practical reduction toward the budget or usual level."
            ),
            "estimated_monthly_savings": round(target, 2),
            "evidence": [reason for reason, flag in (
                ("budget_overrun", budget_overrun), ("unusual_vs_history", unusual)
            ) if flag],
            "savings_are_estimates": True,
        })

    recommendations.sort(key=lambda row: (row["category"].lower(), row["title"].lower()))
    return {
        "recommendations": recommendations,
        "estimated_monthly_savings": round(sum(row["estimated_monthly_savings"] for row in recommendations), 2),
        "savings_are_estimates": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate spending recommendations from JSON input.")
    parser.add_argument("input_json", type=Path, help="JSON with transactions path and optional budgets")
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    result = generate_spending_recommendations(
        data.get("transactions", "ai_engine/transactions.csv"),
        data.get("budgets"),
        overspending_result=data.get("overspending_result"),
        recurring_results=data.get("recurring_results"),
        historical_category_spending=data.get("historical_category_spending"),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
