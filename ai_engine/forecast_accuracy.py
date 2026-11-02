"""T32: evaluate numerical forecast error on exactly matching dates."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


INCOME_TYPES = {"credit", "income", "inflow", "deposit"}
EXPENSE_TYPES = {"debit", "expense", "outflow", "withdrawal"}


def _rows(source: Any) -> list[dict[str, Any]]:
    """Convert common T15/T16/CSV inputs to rows; empty inputs return none."""
    if source is None:
        return []
    if isinstance(source, pd.DataFrame):
        return source.to_dict(orient="records")
    if isinstance(source, (str, Path)):
        try:
            return pd.read_csv(source).to_dict(orient="records")
        except pd.errors.EmptyDataError:
            return []
    if isinstance(source, dict):
        for key in ("forecast", "daily_balances", "records", "transactions"):
            value = source.get(key)
            if isinstance(value, list):
                return value
        return [source] if "date" in source else []
    if isinstance(source, list):
        return source
    return []


def _day(value: Any) -> str | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    parsed = pd.Timestamp(parsed)
    if parsed.tzinfo is not None:
        parsed = parsed.tz_localize(None)
    return parsed.normalize().strftime("%Y-%m-%d")


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _prediction_series(source: Any, measure: str) -> dict[str, float]:
    records = _rows(source)
    keys = {
        "income": ("predicted_income", "income"),
        "expenses": ("predicted_expenses", "expenses", "predicted_expense"),
        "balance": ("expected_balance", "predicted_balance", "actual_balance", "account_balance", "balance"),
    }[measure]
    result: dict[str, float] = {}
    for row in records:
        if not isinstance(row, dict):
            continue
        day = _day(row.get("date"))
        if day is None:
            continue
        value = next((_number(row.get(key)) for key in keys if _number(row.get(key)) is not None), None)
        if value is not None:
            result[day] = value
    return result


def _actual_transaction_series(source: Any) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Aggregate transaction rows by date, or accept already daily totals."""
    income: dict[str, float] = {}
    expenses: dict[str, float] = {}
    balances: dict[str, float] = {}
    records = _rows(source)
    for row in records:
        if not isinstance(row, dict):
            continue
        day = _day(row.get("date"))
        if day is None:
            continue

        transaction_type = str(row.get("type", "")).strip().lower()
        amount = _number(row.get("amount"))
        if amount is not None and transaction_type in INCOME_TYPES:
            income[day] = income.get(day, 0.0) + abs(amount)
        elif amount is not None and transaction_type in EXPENSE_TYPES:
            expenses[day] = expenses.get(day, 0.0) + abs(amount)
        else:
            actual_income = _number(row.get("actual_income", row.get("income")))
            actual_expenses = _number(row.get("actual_expenses", row.get("expenses")))
            if actual_income is not None:
                income[day] = income.get(day, 0.0) + actual_income
            if actual_expenses is not None:
                expenses[day] = expenses.get(day, 0.0) + actual_expenses

        actual_balance = next((
            _number(row.get(key)) for key in ("actual_balance", "balance", "account_balance")
            if _number(row.get(key)) is not None
        ), None)
        if actual_balance is not None:
            # For multiple same-day transaction rows, the last supplied actual
            # balance represents the day's final observed balance.
            balances[day] = actual_balance
    return income, expenses, balances


def _metrics(predicted: dict[str, float], actual: dict[str, float]) -> dict[str, Any]:
    matched_dates = sorted(set(predicted) & set(actual))
    errors = [predicted[day] - actual[day] for day in matched_dates]
    if errors:
        mae = sum(abs(error) for error in errors) / len(errors)
        rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    else:
        mae = rmse = None
    return {
        "sample_count": len(errors),
        "mae": round(mae, 4) if mae is not None else None,
        "rmse": round(rmse, 4) if rmse is not None else None,
        "matched_dates": matched_dates,
        "unmatched_prediction_count": len(set(predicted) - set(actual)),
        "unmatched_actual_count": len(set(actual) - set(predicted)),
    }


def calculate_forecast_accuracy(
    predicted_forecast: Any,
    actual_transactions: Any,
    *,
    predicted_balances: Any = None,
    actual_balances: Any = None,
) -> dict[str, Any]:
    """Return MAE/RMSE for income, expenses, and optionally account balance.

    Actual transactions may be T14-style transaction rows (summed by date) or
    daily totals. Balance data can be carried in the same rows or supplied as
    separate T16/actual-balance inputs. Only exact normalized calendar-date
    matches are scored; mismatched dates are reported and excluded.
    MAE/RMSE are error magnitudes in the input currency, not percentage accuracy.
    """
    actual_income, actual_expenses, embedded_actual_balance = _actual_transaction_series(actual_transactions)
    income_metrics = _metrics(_prediction_series(predicted_forecast, "income"), actual_income)
    expense_metrics = _metrics(_prediction_series(predicted_forecast, "expenses"), actual_expenses)

    predicted_balance_source = predicted_balances
    if predicted_balance_source is None and isinstance(predicted_forecast, dict):
        predicted_balance_source = predicted_forecast.get("daily_balances")
    actual_balance_source = actual_balances if actual_balances is not None else [
        {"date": day, "balance": amount} for day, amount in embedded_actual_balance.items()
    ]
    predicted_balance_series = _prediction_series(predicted_balance_source, "balance")
    actual_balance_series = _prediction_series(actual_balance_source, "balance")
    balance_metrics = _metrics(predicted_balance_series, actual_balance_series)

    return {
        "income": income_metrics,
        "expenses": expense_metrics,
        "balance": balance_metrics,
        "metric_note": "MAE and RMSE measure forecast error in the input currency; they are not percentage accuracy scores.",
        "date_matching": "Only exact calendar-date matches are included in the metrics.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate T32 forecast errors from JSON input.")
    parser.add_argument("input_json", type=Path, help="JSON with predicted_forecast and actual_transactions")
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    result = calculate_forecast_accuracy(
        data.get("predicted_forecast", {}), data.get("actual_transactions", []),
        predicted_balances=data.get("predicted_balances"),
        actual_balances=data.get("actual_balances"),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
