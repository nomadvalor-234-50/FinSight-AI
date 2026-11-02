"""T16: daily account-balance prediction using cash-flow forecasts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


def _number(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _date_string(value: Any) -> str | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return pd.Timestamp(parsed).strftime("%Y-%m-%d")


def _payment_rows(value: Any) -> Iterable[dict[str, Any]]:
    """Accept T12's list or its ``upcoming_payments`` response envelope."""
    if isinstance(value, dict):
        value = value.get("upcoming_payments", [])
    if isinstance(value, pd.DataFrame):
        value = value.to_dict(orient="records")
    return value if isinstance(value, (list, tuple)) else []


def predict_daily_balances(
    forecast: dict[str, Any] | pd.DataFrame,
    current_balance: float,
    *,
    upcoming_payments: Any = None,
) -> dict[str, Any]:
    """Accumulate forecast cash flows and dated recurring commitments.

    Forecasted expense values are treated as the baseline and T12 commitments
    are overlaid as separate payments. T15 explicitly reports that it excludes
    those commitments. Duplicate commitment rows with the same date,
    description, and amount are counted once.
    """
    starting_balance = _number(current_balance, default=math.nan)
    if not math.isfinite(starting_balance):
        raise ValueError("current_balance must be a finite number")
    if isinstance(forecast, pd.DataFrame):
        daily_rows = forecast.to_dict(orient="records")
        if upcoming_payments is None:
            upcoming_payments = []
    elif isinstance(forecast, dict):
        daily_rows = forecast.get("forecast", [])
        if upcoming_payments is None:
            upcoming_payments = forecast.get("upcoming_payments", [])
        # Allow a future forecaster to mark commitments already embedded in
        # daily expenses; in that case, do not overlay the same T12 rows again.
        commitments_already_included = forecast.get("includes_upcoming_payments") is True
    else:
        raise TypeError("forecast must be a T15 result dictionary or DataFrame")
    if isinstance(forecast, pd.DataFrame):
        commitments_already_included = False

    daily_by_date: dict[str, dict[str, float]] = {}
    if isinstance(daily_rows, list):
        for row in daily_rows:
            if not isinstance(row, dict):
                continue
            day = _date_string(row.get("date"))
            if day is None:
                continue
            daily_by_date[day] = {
                "income": max(0.0, _number(row.get("predicted_income"))),
                "expenses": max(0.0, _number(row.get("predicted_expenses"))),
            }

    payment_by_date: dict[str, list[dict[str, Any]]] = {}
    seen_payments: set[tuple[str, str, float]] = set()
    for payment in ([] if commitments_already_included else _payment_rows(upcoming_payments)):
        if not isinstance(payment, dict):
            continue
        day = _date_string(payment.get("expected_payment_date"))
        amount = _number(payment.get("expected_amount"), default=math.nan)
        description = str(payment.get("description", "")).strip()
        if day is None or not math.isfinite(amount) or amount < 0:
            continue
        key = (day, description.casefold(), round(amount, 2))
        if key in seen_payments:
            continue
        seen_payments.add(key)
        payment_by_date.setdefault(day, []).append({
            "description": description,
            "amount": round(amount, 2),
        })

    dates = sorted(set(daily_by_date) | set(payment_by_date))
    balance = starting_balance
    daily_balances: list[dict[str, Any]] = []
    for day in dates:
        daily = daily_by_date.get(day, {"income": 0.0, "expenses": 0.0})
        commitments = payment_by_date.get(day, [])
        commitment_total = sum(item["amount"] for item in commitments)
        opening_balance = balance
        total_expenses = daily["expenses"] + commitment_total
        balance = opening_balance + daily["income"] - total_expenses
        daily_balances.append({
            "date": day,
            "opening_balance": round(opening_balance, 2),
            "predicted_income": round(daily["income"], 2),
            "predicted_expenses": round(daily["expenses"], 2),
            "upcoming_payments": commitments,
            "upcoming_payment_total": round(commitment_total, 2),
            "expected_balance": round(balance, 2),
        })

    return {
        "starting_balance": round(starting_balance, 2),
        "daily_balances": daily_balances,
        "ending_balance": round(balance, 2),
        "includes_upcoming_payments": bool(commitments_already_included or payment_by_date),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict daily account balances from JSON input.")
    parser.add_argument("input_json", type=Path, help="JSON with forecast and optional upcoming_payments")
    parser.add_argument("--current-balance", type=float, required=True)
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        result = predict_daily_balances(json.load(file), args.current_balance)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
