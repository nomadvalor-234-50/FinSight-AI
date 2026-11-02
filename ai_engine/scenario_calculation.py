"""T27: calculate hypothetical cash-flow scenarios without changing history."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .forecasting import AVERAGE_DAYS_PER_MONTH, forecast_cash_flow
    from .historical_analysis import analyze_historical_transactions
except ImportError:  # pragma: no cover - direct script execution
    from forecasting import AVERAGE_DAYS_PER_MONTH, forecast_cash_flow
    from historical_analysis import analyze_historical_transactions


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a finite number") from None
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _forecast_totals(forecast: dict[str, Any]) -> tuple[float, float, int]:
    """Read forecast aggregate fields or sum its daily rows."""
    rows = forecast.get("forecast", [])
    try:
        income = float(forecast.get("total_predicted_income"))
    except (TypeError, ValueError):
        income = math.nan
    try:
        expenses = float(forecast.get("total_predicted_expenses"))
    except (TypeError, ValueError):
        expenses = math.nan
    if not math.isfinite(income) and isinstance(rows, list):
        income = sum(max(0.0, _safe_number(row.get("predicted_income"))) for row in rows if isinstance(row, dict))
    if not math.isfinite(expenses) and isinstance(rows, list):
        expenses = sum(max(0.0, _safe_number(row.get("predicted_expenses"))) for row in rows if isinstance(row, dict))
    if not math.isfinite(income) or not math.isfinite(expenses) or income < 0 or expenses < 0:
        raise ValueError("original forecast must contain finite non-negative income and expense totals")
    days = forecast.get("forecast_days")
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = len(rows) if isinstance(rows, list) and rows else 30
    return income, expenses, max(1, days)


def _safe_number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def _change_value(value: Any, name: str, *, percentage: bool = False) -> float:
    number = _finite(value, name)
    if percentage and number < -100:
        raise ValueError(f"{name} cannot be less than -100 percent")
    return number


def calculate_scenario(
    original_forecast: dict[str, Any] | None = None,
    *,
    transactions: pd.DataFrame | str | Path | None = None,
    forecast_days: int = 30,
    forecast_start_date: str | date | datetime | pd.Timestamp | None = None,
    current_balance: float | None = None,
    original_balance_prediction: dict[str, Any] | None = None,
    income_change_percent: float = 0,
    income_change_amount: float = 0,
    expense_change_percent: float = 0,
    expense_change_amount: float = 0,
    category_expense_changes: dict[str, Any] | None = None,
    additional_one_time_income: float = 0,
    additional_one_time_expenses: float = 0,
) -> dict[str, Any]:
    """Return original and modified outcomes for a hypothetical scenario.

    Global income/expense changes accept either a percentage or signed amount
    (not both at once). Category adjustments accept ``{"Food": {"percent":
    -10}}``, ``{"Food": {"amount": -50}}``, or a signed numeric amount.
    Category baseline values are estimated from T14 category totals and scaled
    to the T15 forecast horizon and total predicted expenses. One-time entries
    are non-negative horizon totals. This is a hypothetical simulation, not a
    guaranteed prediction, and input transaction data is never mutated.
    """
    if original_forecast is None:
        if transactions is None:
            raise ValueError("Provide original_forecast or transactions")
        original_forecast = forecast_cash_flow(
            transactions, forecast_days=forecast_days, forecast_start_date=forecast_start_date
        )
    if not isinstance(original_forecast, dict):
        raise TypeError("original_forecast must be a T15 result dictionary")
    original_income, original_expenses, horizon_days = _forecast_totals(original_forecast)

    income_percent = _change_value(income_change_percent, "income_change_percent", percentage=True)
    income_amount = _change_value(income_change_amount, "income_change_amount")
    expense_percent = _change_value(expense_change_percent, "expense_change_percent", percentage=True)
    expense_amount = _change_value(expense_change_amount, "expense_change_amount")
    if income_percent and income_amount:
        raise ValueError("Choose either income_change_percent or income_change_amount")
    if expense_percent and expense_amount:
        raise ValueError("Choose either expense_change_percent or expense_change_amount")
    one_time_income = _change_value(additional_one_time_income, "additional_one_time_income")
    one_time_expenses = _change_value(additional_one_time_expenses, "additional_one_time_expenses")
    if one_time_income < 0 or one_time_expenses < 0:
        raise ValueError("Additional one-time income and expenses must be non-negative")

    modified_income = original_income * (1 + income_percent / 100) + income_amount + one_time_income
    if modified_income < 0:
        raise ValueError("Income changes cannot reduce projected income below zero")

    global_expenses = original_expenses * (1 + expense_percent / 100) + expense_amount
    if global_expenses < 0:
        raise ValueError("Expense changes cannot reduce projected expenses below zero")

    category_changes = category_expense_changes or {}
    if not isinstance(category_changes, dict):
        raise ValueError("category_expense_changes must be a category-to-change dictionary")
    category_adjustment_total = 0.0
    category_projection: dict[str, float] = {}
    if category_changes:
        if transactions is None:
            raise ValueError("transactions are required to estimate category-specific forecast changes")
        analysis = analyze_historical_transactions(transactions)
        month_count = max(1, len(analysis.get("monthly_summary", [])))
        monthly_by_category = {
            str(category): max(0.0, _safe_number(amount)) / month_count
            * horizon_days / AVERAGE_DAYS_PER_MONTH
            for category, amount in analysis.get("category_wise_expenses", {}).items()
        }
        category_total = sum(monthly_by_category.values())
        if category_total > 0:
            category_projection = {
                category: amount * global_expenses / category_total
                for category, amount in monthly_by_category.items()
            }
        else:
            category_projection = {category: 0.0 for category in monthly_by_category}

        name_map = {category.casefold(): category for category in category_projection}
        for requested_category, change in category_changes.items():
            canonical = name_map.get(str(requested_category).strip().casefold())
            if canonical is None:
                raise ValueError(f"No historical expense data found for category: {requested_category}")
            if isinstance(change, dict):
                percent_value = change.get("percent", change.get("change_percent", 0))
                amount_value = change.get("amount", change.get("change_amount", 0))
                percent = _change_value(percent_value, f"{requested_category} percent", percentage=True)
                amount = _change_value(amount_value, f"{requested_category} amount")
                if percent and amount:
                    raise ValueError(f"Choose either percent or amount for category {requested_category}")
            else:
                percent = 0.0
                amount = _change_value(change, f"{requested_category} amount")
            before = category_projection[canonical]
            after = before * (1 + percent / 100) + amount
            if after < 0:
                raise ValueError(f"Category changes cannot reduce {requested_category} expenses below zero")
            category_projection[canonical] = after
            category_adjustment_total += after - before

    modified_expenses = global_expenses + category_adjustment_total + one_time_expenses
    original_net = original_income - original_expenses
    modified_net = modified_income - modified_expenses

    if isinstance(original_balance_prediction, dict):
        base_balance = _finite(original_balance_prediction.get("ending_balance"), "ending balance")
    elif current_balance is not None:
        base_balance = _finite(current_balance, "current_balance") + original_net
    else:
        raise ValueError("Provide current_balance or original_balance_prediction")
    modified_balance = base_balance + (modified_net - original_net)

    original = {
        "total_income": round(original_income, 2),
        "total_expenses": round(original_expenses, 2),
        "net_cash_flow": round(original_net, 2),
        "projected_balance": round(base_balance, 2),
    }
    modified = {
        "total_income": round(modified_income, 2),
        "total_expenses": round(modified_expenses, 2),
        "net_cash_flow": round(modified_net, 2),
        "projected_balance": round(modified_balance, 2),
    }
    return {
        "scenario_type": "Hypothetical simulation; not a guaranteed prediction",
        "forecast_days": horizon_days,
        "original": original,
        "modified": modified,
        "difference": {
            key: round(modified[key] - original[key], 2)
            for key in original
        },
        "category_expense_projection": {
            category: round(amount, 2) for category, amount in category_projection.items()
        },
        "assumptions": [
            "Global changes apply to the forecast horizon totals.",
            "Category changes use historical category shares scaled to the forecast expense total.",
            "One-time amounts are added once within the forecast horizon.",
            "Upcoming recurring commitments are reflected only if they were included in the supplied T16 ending balance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate a hypothetical scenario from JSON input.")
    parser.add_argument("input_json", type=Path, help="JSON containing forecast, assumptions, and balance")
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    result = calculate_scenario(
        data.get("original_forecast"), transactions=data.get("transactions"),
        current_balance=data.get("current_balance"),
        original_balance_prediction=data.get("original_balance_prediction"),
        **data.get("assumptions", {}),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
