"""T15: simple, explainable cash-flow forecasting for limited history."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .historical_analysis import analyze_historical_transactions
except ImportError:  # pragma: no cover - direct script execution
    from historical_analysis import analyze_historical_transactions


SUPPORTED_FORECAST_DAYS = {7, 30, 90}
AVERAGE_DAYS_PER_MONTH = 365.2425 / 12


def _date_or_today(value: str | date | datetime | pd.Timestamp | None) -> pd.Timestamp:
    """Parse a forecast start date, defaulting to today's calendar date."""
    if value is None:
        return pd.Timestamp.now().normalize()
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError("forecast_start_date must be a valid date")
    parsed = pd.Timestamp(parsed)
    return parsed.tz_localize(None).normalize() if parsed.tzinfo else parsed.normalize()


def _finite_monthly_values(history: dict[str, Any], field: str) -> list[float]:
    """Extract usable monthly values from T14 historical analysis output."""
    values: list[float] = []
    for row in history.get("monthly_summary", []):
        if not isinstance(row, dict):
            continue
        try:
            number = float(row.get(field, 0))
        except (TypeError, ValueError):
            continue
        if math.isfinite(number) and number >= 0:
            values.append(number)
    return values


def forecast_cash_flow(
    transactions: pd.DataFrame | str | Path,
    *,
    forecast_days: int = 30,
    forecast_start_date: str | date | datetime | pd.Timestamp | None = None,
    historical_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Forecast daily income, expenses, and net cash flow for 7/30/90 days.

    Algorithm: analyze history with T14, take the mean of the latest up to
    three calendar-month totals, convert those means to daily amounts using
    the average calendar month length, and hold that daily run rate constant
    across the requested horizon. Known upcoming recurring payments are not
    added here; T16 overlays those as separate dated commitments to prevent
    double-counting against the historical baseline.

    With no usable history, daily forecasts are zero and
    ``insufficient_history`` is true. One usable month is forecastable but is
    still marked insufficient because there is no second month to compare.
    """
    if forecast_days not in SUPPORTED_FORECAST_DAYS:
        raise ValueError(f"forecast_days must be one of {sorted(SUPPORTED_FORECAST_DAYS)}")
    start = _date_or_today(forecast_start_date)
    if historical_result is not None:
        if not isinstance(historical_result, dict):
            raise ValueError("historical_result must be a historical-analysis dictionary")
        history = historical_result
    else:
        try:
            history = analyze_historical_transactions(transactions)
        except ValueError:
            # A file/frame with missing required history columns is treated as
            # insufficient evidence rather than breaking a forecast request.
            history = {"monthly_summary": []}
    monthly_rows = history.get("monthly_summary", [])
    recent_rows = [row for row in monthly_rows if isinstance(row, dict)][-3:]
    if recent_rows:
        recent_history = {"monthly_summary": recent_rows}
        incomes = _finite_monthly_values(recent_history, "income")
        expenses = _finite_monthly_values(recent_history, "expenses")
    else:
        incomes, expenses = [], []

    average_income_month = sum(incomes) / len(incomes) if incomes else 0.0
    average_expense_month = sum(expenses) / len(expenses) if expenses else 0.0
    daily_income = average_income_month / AVERAGE_DAYS_PER_MONTH
    daily_expense = average_expense_month / AVERAGE_DAYS_PER_MONTH

    daily_forecast: list[dict[str, Any]] = []
    for offset in range(1, forecast_days + 1):
        forecast_date = start + pd.Timedelta(days=offset)
        predicted_income = round(daily_income, 2)
        predicted_expenses = round(daily_expense, 2)
        daily_forecast.append({
            "date": forecast_date.strftime("%Y-%m-%d"),
            "predicted_income": predicted_income,
            "predicted_expenses": predicted_expenses,
            "predicted_net_cash_flow": round(predicted_income - predicted_expenses, 2),
        })

    total_income = round(sum(row["predicted_income"] for row in daily_forecast), 2)
    total_expenses = round(sum(row["predicted_expenses"] for row in daily_forecast), 2)
    return {
        "forecast_days": forecast_days,
        "forecast_start_date": start.strftime("%Y-%m-%d"),
        "forecast_end_date": (start + pd.Timedelta(days=forecast_days)).strftime("%Y-%m-%d"),
        "forecast": daily_forecast,
        "total_predicted_income": total_income,
        "total_predicted_expenses": total_expenses,
        "predicted_net_cash_flow": round(total_income - total_expenses, 2),
        "insufficient_history": len(monthly_rows) < 2,
        "algorithm": "Recent up to 3 calendar-month average, converted to a constant daily run rate",
        "includes_upcoming_payments": False,
    }


def main() -> None:
    default_csv = Path(__file__).with_name("transactions.csv")
    parser = argparse.ArgumentParser(description="Forecast future FinSight cash flow.")
    parser.add_argument("csv_path", nargs="?", default=default_csv, type=Path)
    parser.add_argument("--days", type=int, choices=sorted(SUPPORTED_FORECAST_DAYS), default=30)
    parser.add_argument("--start", help="Forecast start date (YYYY-MM-DD); defaults to today.")
    args = parser.parse_args()
    print(json.dumps(forecast_cash_flow(args.csv_path, forecast_days=args.days,
                                        forecast_start_date=args.start), indent=2))


if __name__ == "__main__":
    main()
