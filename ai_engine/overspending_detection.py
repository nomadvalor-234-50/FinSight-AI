"""T19: detect budget overruns and unusual category spending."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

try:
    from .historical_analysis import analyze_historical_transactions
except ImportError:  # pragma: no cover - direct script execution
    from historical_analysis import analyze_historical_transactions


def _category_amounts(data: Any, *, monthly_average: bool = False) -> dict[str, float]:
    """Get category expense totals from a T14 result, mapping, CSV, or frame."""
    if data is None:
        return {}
    if isinstance(data, dict):
        source = data.get("category_wise_expenses", data)
        if not isinstance(source, dict):
            return {}
        result: dict[str, float] = {}
        for category, value in source.items():
            try:
                amount = float(value)
            except (TypeError, ValueError):
                continue
            if str(category).strip() and math.isfinite(amount) and amount >= 0:
                result[str(category).strip()] = amount
        # T14 gives category totals across its analyzed month span. Convert to
        # monthly averages only when this mapping is historical comparison data.
        monthly_count = len(data.get("monthly_summary", []))
        if monthly_average and monthly_count > 0:
            result = {category: amount / monthly_count for category, amount in result.items()}
        return result

    analysis = analyze_historical_transactions(data)
    result = analysis["category_wise_expenses"]
    if monthly_average:
        months = max(1, len(analysis["monthly_summary"]))
        result = {category: amount / months for category, amount in result.items()}
    return result


def _budget_amounts(budgets: dict[str, Any] | None) -> dict[str, float]:
    """Keep valid non-negative category budget values; ignore missing/invalid."""
    if budgets is None:
        return {}
    if not isinstance(budgets, dict):
        raise ValueError("budgets must be a category-to-amount dictionary")
    result: dict[str, float] = {}
    for category, value in budgets.items():
        try:
            amount = float(value)
        except (TypeError, ValueError):
            continue
        if str(category).strip() and math.isfinite(amount) and amount >= 0:
            result[str(category).strip()] = amount
    return result


def _case_insensitive_values(values: dict[str, float], *, sum_duplicates: bool) -> tuple[dict[str, float], dict[str, str]]:
    """Index category values by casefolded name while retaining display labels."""
    normalized: dict[str, float] = {}
    display_names: dict[str, str] = {}
    for category, amount in values.items():
        key = category.strip().casefold()
        display_names.setdefault(key, category)
        if sum_duplicates:
            normalized[key] = normalized.get(key, 0.0) + amount
        else:
            # Conflicting budgets that differ only in capitalization resolve
            # to the first supplied value rather than being added together.
            normalized.setdefault(key, amount)
    return normalized, display_names


def detect_overspending(
    actual_spending: Any,
    budgets: dict[str, Any] | None,
    *,
    historical_category_spending: Any = None,
    unusual_multiplier: float = 1.5,
) -> dict[str, Any]:
    """Compare actual category totals with budgets and historical monthly norms.

    Actual spending may be a T14 analysis dictionary, a direct category-to-
    amount mapping, a transaction DataFrame, or a CSV path. Historical input
    accepts the same forms; transaction/T14 totals are converted to monthly
    averages. Only category alerts that exceed a budget or historical norm are
    included in ``alerts``. Missing budgets are represented as ``None``.
    """
    try:
        multiplier = float(unusual_multiplier)
    except (TypeError, ValueError):
        raise ValueError("unusual_multiplier must be greater than 1") from None
    if not math.isfinite(multiplier) or multiplier <= 1:
        raise ValueError("unusual_multiplier must be greater than 1")

    actual_original = _category_amounts(actual_spending)
    budget_original = _budget_amounts(budgets)
    historical_original = _category_amounts(historical_category_spending, monthly_average=True)
    actual, actual_names = _case_insensitive_values(actual_original, sum_duplicates=True)
    budget_map, budget_names = _case_insensitive_values(budget_original, sum_duplicates=False)
    historical, historical_names = _case_insensitive_values(historical_original, sum_duplicates=True)
    categories = sorted(set(actual) | set(budget_map) | set(historical))

    category_results: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    for category_key in categories:
        category = actual_names.get(category_key, budget_names.get(category_key, historical_names.get(category_key, category_key)))
        spent = actual.get(category_key, 0.0)
        budget = budget_map.get(category_key)
        has_budget = budget is not None
        budget_excess = max(0.0, spent - budget) if has_budget else 0.0
        budget_overrun = has_budget and budget_excess > 0
        budget_percentage = (
            round((budget_excess / budget) * 100, 2) if budget and budget_overrun
            else (None if budget == 0 and budget_overrun else 0.0 if has_budget else None)
        )

        baseline = historical.get(category_key)
        unusual = baseline is not None and spent > baseline * multiplier
        historical_excess = max(0.0, spent - baseline) if unusual and baseline is not None else 0.0
        reasons = []
        if budget_overrun:
            reasons.append("budget_overrun")
        if unusual:
            reasons.append("unusual_vs_history")
        row = {
            "category": category,
            "budget": round(budget, 2) if has_budget else None,
            "actual_spending": round(spent, 2),
            "excess_amount": round(budget_excess, 2),
            "overspending_percentage": budget_percentage,
            "budget_overrun": bool(budget_overrun),
            "historical_monthly_average": round(baseline, 2) if baseline is not None else None,
            "unusual_spending": bool(unusual),
            "unusual_excess_amount": round(historical_excess, 2),
            "alert_reasons": reasons,
        }
        category_results.append(row)
        if reasons:
            alerts.append(row)

    return {
        "unusual_multiplier": multiplier,
        "categories": category_results,
        "alerts": alerts,
        "alert_count": len(alerts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check spending against budgets in JSON input.")
    parser.add_argument("input_json", type=Path, help="JSON with actual_spending and budgets")
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    result = detect_overspending(
        data.get("actual_spending", {}),
        data.get("budgets", {}),
        historical_category_spending=data.get("historical_category_spending"),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
