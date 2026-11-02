"""T25: summarize current savings and estimated savings opportunities."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .historical_analysis import analyze_historical_transactions
except ImportError:  # pragma: no cover - direct script execution
    from historical_analysis import analyze_historical_transactions


def _finite(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def analyze_savings(
    historical_data: pd.DataFrame | str | Path | dict[str, Any],
    recommendations: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Calculate cash surplus, savings rates, and capped recommendation value.

    Recommendation amounts are estimates, not guaranteed savings. Duplicate
    title/category recommendations are counted once, and total savings within
    a category are capped at that category's average monthly expenses to avoid
    overlapping suggestions claiming more than the spending available.
    """
    if isinstance(historical_data, dict):
        history = historical_data
    else:
        history = analyze_historical_transactions(historical_data)

    total_income = _finite(history.get("total_income"))
    total_expenses = _finite(history.get("total_expenses"))
    current_surplus = total_income - total_expenses
    monthly_rows = history.get("monthly_summary", [])
    month_count = len(monthly_rows) if isinstance(monthly_rows, list) else 0
    average_income = _finite(history.get("average_monthly_income"))
    average_expenses = _finite(history.get("average_monthly_expenses"))
    if month_count == 0:
        average_income = 0.0
        average_expenses = 0.0

    categories = history.get("category_wise_expenses", {})
    categories = categories if isinstance(categories, dict) else {}
    category_monthly = {
        str(category): max(0.0, _finite(amount)) / max(month_count, 1)
        for category, amount in categories.items()
    }

    if isinstance(recommendations, dict):
        recommendation_rows = recommendations.get("recommendations", [])
    elif isinstance(recommendations, list):
        recommendation_rows = recommendations
    else:
        recommendation_rows = []

    seen: set[tuple[str, str]] = set()
    used_by_category: dict[str, float] = {}
    included_recommendations: list[dict[str, Any]] = []
    for row in recommendation_rows if isinstance(recommendation_rows, list) else []:
        if not isinstance(row, dict):
            continue
        category = str(row.get("category", "")).strip()
        title = str(row.get("title", "")).strip()
        amount = _finite(row.get("estimated_monthly_savings"))
        if not category or not title or amount <= 0:
            continue
        key = (category.casefold(), title.casefold())
        if key in seen:
            continue
        seen.add(key)
        # Without category expense evidence, do not claim category savings.
        category_key = next((key for key in category_monthly if key.casefold() == category.casefold()), None)
        if category_key is None:
            continue
        remaining = max(0.0, category_monthly[category_key] - used_by_category.get(category_key, 0.0))
        accepted = min(amount, remaining)
        if accepted <= 0:
            continue
        used_by_category[category_key] = used_by_category.get(category_key, 0.0) + accepted
        included_recommendations.append({
            "title": title,
            "category": category,
            "estimated_monthly_savings": round(accepted, 2),
        })

    potential_monthly = round(sum(used_by_category.values()), 2)
    current_monthly_surplus = round(average_income - average_expenses, 2)
    current_rate = round(current_surplus / total_income * 100, 2) if total_income > 0 else None
    potential_rate = (
        round((current_monthly_surplus + potential_monthly) / average_income * 100, 2)
        if average_income > 0 else None
    )
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "current_surplus": round(current_surplus, 2),
        "average_monthly_income": round(average_income, 2),
        "average_monthly_expenses": round(average_expenses, 2),
        "average_monthly_surplus": current_monthly_surplus,
        "current_savings_rate_percentage": current_rate,
        "potential_additional_monthly_savings": potential_monthly,
        "potential_additional_yearly_savings": round(potential_monthly * 12, 2),
        "projected_savings_rate_percentage": potential_rate,
        "recommendation_breakdown": included_recommendations,
        "potential_savings_are_guaranteed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze current and potential savings from JSON input.")
    parser.add_argument("input_json", type=Path, help="JSON with transactions and recommendations")
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    result = analyze_savings(data.get("transactions", "ai_engine/transactions.csv"),
                             data.get("recommendations"))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
