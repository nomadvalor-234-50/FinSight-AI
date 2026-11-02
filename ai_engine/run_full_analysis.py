"""Run the FinSight AI engine in dependency order for one transaction CSV."""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .categorization import categorize_transaction
    from .recurring_detection import detect_recurring_payments
    from .upcoming_payment import estimate_upcoming_payments
    from .historical_analysis import analyze_historical_transactions
    from .forecasting import forecast_cash_flow, SUPPORTED_FORECAST_DAYS
    from .balance_prediction import predict_daily_balances
    from .low_balance_detection import detect_low_balance
    from .overspending_detection import detect_overspending
    from .financial_risk import classify_financial_risk
    from .alert_generation import generate_alerts
    from .spending_recommendations import generate_spending_recommendations
    from .savings_analysis import analyze_savings
    from .scenario_calculation import calculate_scenario
    from .insight_generation import generate_insights
    from .recommendation_engine import build_recommendations
    from .forecast_accuracy import calculate_forecast_accuracy
except ImportError:  # Supports running this file directly as a script.
    from categorization import categorize_transaction
    from recurring_detection import detect_recurring_payments
    from upcoming_payment import estimate_upcoming_payments
    from historical_analysis import analyze_historical_transactions
    from forecasting import forecast_cash_flow, SUPPORTED_FORECAST_DAYS
    from balance_prediction import predict_daily_balances
    from low_balance_detection import detect_low_balance
    from overspending_detection import detect_overspending
    from financial_risk import classify_financial_risk
    from alert_generation import generate_alerts
    from spending_recommendations import generate_spending_recommendations
    from savings_analysis import analyze_savings
    from scenario_calculation import calculate_scenario
    from insight_generation import generate_insights
    from recommendation_engine import build_recommendations
    from forecast_accuracy import calculate_forecast_accuracy


TRANSACTION_COLUMNS = ["date", "description", "amount", "type"]
EXPENSE_TYPES = {"debit", "expense", "outflow", "withdrawal"}
INCOME_TYPES = {"credit", "income", "inflow", "deposit"}
DESCRIPTION_FILLER_WORDS = {
    "payment", "paid", "purchase", "transaction", "debit", "bill", "bills",
    "subscription", "monthly", "weekly", "yearly", "annual", "autopay",
    "standing", "instruction", "online", "pos", "charge", "premium",
}


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a finite number") from None
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _read_csv(path: str | Path, *, actual_data: bool = False) -> pd.DataFrame:
    """Load a CSV; represent a zero-byte file as an empty standard table."""
    source = Path(path).expanduser()
    try:
        frame = pd.read_csv(source)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

    if frame.empty:
        # Header-only and zero-row files should pass safely through the modules.
        for column in TRANSACTION_COLUMNS:
            if column not in frame.columns:
                frame[column] = pd.Series(dtype="object")
        return frame

    if actual_data:
        has_transaction_data = {"date", "type", "amount"}.issubset(frame.columns)
        has_balance_data = "date" in frame.columns and bool(
            {"actual_balance", "balance", "account_balance"} & set(frame.columns)
        )
        if "date" not in frame.columns or not (has_transaction_data or has_balance_data):
            raise ValueError("Actual CSV needs date plus transaction type/amount or an account-balance column")
    else:
        required = {"date", "description", "amount"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"Transaction CSV is missing required column(s): {', '.join(sorted(missing))}")
        if "type" not in frame.columns:
            frame["type"] = ""
        if "description" not in frame.columns:
            frame["description"] = ""
    return frame


def _categorize(frame: pd.DataFrame) -> pd.DataFrame:
    """Create a categorized working copy without changing source data."""
    result = frame.copy()
    if "description" not in result:
        result["description"] = ""
    result["category"] = result["description"].apply(categorize_transaction)
    return result


def _merchant_key(value: Any) -> str:
    """Normalize description text consistently for recurring-row matching."""
    words = re.findall(r"[a-z0-9]+", str(value or "").lower())
    return " ".join(word for word in words if word not in DESCRIPTION_FILLER_WORDS)


def _matches_recurring_description(value: Any, recurring_description: Any) -> bool:
    left = _merchant_key(value)
    right = _merchant_key(recurring_description)
    if not left or not right:
        return False
    if left == right:
        return True
    left_words, right_words = set(left.split()), set(right.split())
    if left_words & right_words and len(left_words & right_words) / min(len(left_words), len(right_words)) >= 0.75:
        return True
    return difflib.SequenceMatcher(None, left, right).ratio() >= 0.82


def _history_without_recurring_expenses(
    frame: pd.DataFrame,
    history: dict[str, Any],
    recurring_payments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Remove T10-detected recurring charges from T15 baseline expenses.

    T16 adds upcoming T12 payments on their expected dates. Removing their
    historical charges from the smooth baseline prevents the same commitments
    being represented both as daily average spending and as dated payments.
    The original T14 result remains untouched for reports and other modules.
    """
    recurring_descriptions = [
        item.get("description") for item in recurring_payments
        if isinstance(item, dict) and item.get("is_recurring") is True
    ]
    if not recurring_descriptions:
        return history

    dates = pd.to_datetime(frame.get("date", pd.Series(dtype="object")), errors="coerce")
    amounts = pd.to_numeric(frame.get("amount", pd.Series(dtype="object")), errors="coerce")
    finite_amount = amounts.map(lambda value: pd.notna(value) and math.isfinite(value))
    types = frame.get("type", pd.Series("", index=frame.index)).fillna("").astype(str).str.strip().str.lower()
    categories = frame.get("category", pd.Series("Other", index=frame.index)).fillna("Other").astype(str)

    recurring_by_month: dict[str, float] = {}
    for index in frame.index:
        if pd.isna(dates.loc[index]) or not finite_amount.loc[index]:
            continue
        category = categories.loc[index].strip()
        if types.loc[index] in INCOME_TYPES or (types.loc[index] not in EXPENSE_TYPES and category.casefold() == "income"):
            continue
        description = frame.at[index, "description"] if "description" in frame.columns else ""
        if any(_matches_recurring_description(description, recurring) for recurring in recurring_descriptions):
            month_key = str(dates.loc[index].to_period("M"))
            recurring_by_month[month_key] = recurring_by_month.get(month_key, 0.0) + abs(float(amounts.loc[index]))

    if not recurring_by_month:
        return history
    adjusted = dict(history)
    adjusted_months: list[dict[str, Any]] = []
    for row in history.get("monthly_summary", []):
        if not isinstance(row, dict):
            continue
        month_row = dict(row)
        removed = recurring_by_month.get(str(row.get("month", "")), 0.0)
        month_row["expenses"] = round(max(0.0, float(row.get("expenses", 0)) - removed), 2)
        month_row["net_cash_flow"] = round(float(month_row.get("income", 0)) - month_row["expenses"], 2)
        adjusted_months.append(month_row)

    removed_total = sum(recurring_by_month.values())
    adjusted["monthly_summary"] = adjusted_months
    adjusted["total_expenses"] = round(max(0.0, float(history.get("total_expenses", 0)) - removed_total), 2)
    adjusted["net_cash_flow"] = round(float(history.get("total_income", 0)) - adjusted["total_expenses"], 2)
    adjusted["average_monthly_expenses"] = round(
        sum(float(row["expenses"]) for row in adjusted_months) / max(1, len(adjusted_months)), 2
    )
    adjusted["recurring_expenses_removed_for_forecast"] = round(removed_total, 2)
    return adjusted


def _latest_month_expenses(frame: pd.DataFrame) -> tuple[dict[str, float], str | None]:
    """Get expense totals for the newest valid transaction month for T19 budgets."""
    dates = pd.to_datetime(frame.get("date", pd.Series(dtype="object")), errors="coerce")
    amounts = pd.to_numeric(frame.get("amount", pd.Series(dtype="object")), errors="coerce")
    valid_amount = amounts.map(lambda value: pd.notna(value) and math.isfinite(value))
    valid = dates.notna() & valid_amount
    if not valid.any():
        return {}, None

    latest_month = dates[valid].dt.to_period("M").max()
    total_by_category: dict[str, float] = {}
    for index in frame.index[valid & (dates.dt.to_period("M") == latest_month)]:
        row_type = str(frame.at[index, "type"] if "type" in frame.columns else "").strip().lower()
        category = str(frame.at[index, "category"] if "category" in frame.columns else "Other").strip() or "Other"
        if row_type in INCOME_TYPES or (row_type not in EXPENSE_TYPES and category.casefold() == "income"):
            continue
        amount = float(amounts.loc[index])
        total_by_category[category] = total_by_category.get(category, 0.0) + abs(amount)
    return total_by_category, str(latest_month)


def _actual_dates_with_values(frame: pd.DataFrame) -> set[str]:
    """Return dates with a usable observed measure for T32 date-overlap gating."""
    dates = pd.to_datetime(frame.get("date", pd.Series(dtype="object")), errors="coerce")
    result: set[str] = set()
    for index, row in frame.iterrows():
        date_value = dates.loc[index]
        if pd.isna(date_value):
            continue
        amount = pd.to_numeric(pd.Series([row.get("amount")]), errors="coerce").iloc[0]
        transaction_type = str(row.get("type", "")).strip().lower()
        observed = pd.notna(amount) and math.isfinite(float(amount)) and transaction_type in (INCOME_TYPES | EXPENSE_TYPES)
        for balance_key in ("actual_balance", "balance", "account_balance"):
            value = pd.to_numeric(pd.Series([row.get(balance_key)]), errors="coerce").iloc[0]
            if pd.notna(value) and math.isfinite(float(value)):
                observed = True
        if observed:
            result.add(pd.Timestamp(date_value).normalize().strftime("%Y-%m-%d"))
    return result


def run_full_analysis(
    transaction_csv: str | Path,
    *,
    current_balance: float,
    minimum_balance: float,
    budgets: dict[str, Any] | None = None,
    forecast_days: int = 30,
    forecast_start_date: str | None = None,
    actual_csv: str | Path | None = None,
    scenario_assumptions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the existing engine modules and return one JSON-compatible result.

    Category budgets are interpreted as budgets for the newest transaction
    month. Forecasts use T15's historical daily run rate. T12 commitments are
    added only by T16 because T15 explicitly excludes them. Accuracy is only
    computed when a separately supplied actual CSV has usable values on dates
    present in the forecast; historical input rows are never treated as future
    actuals by default.
    """
    starting_balance = _finite_number(current_balance, "current_balance")
    balance_floor = _finite_number(minimum_balance, "minimum_balance")
    if forecast_days not in SUPPORTED_FORECAST_DAYS:
        raise ValueError(f"forecast_days must be one of {sorted(SUPPORTED_FORECAST_DAYS)}")
    if budgets is not None and not isinstance(budgets, dict):
        raise ValueError("budgets must be a category-to-amount dictionary or None")
    if scenario_assumptions is not None and not isinstance(scenario_assumptions, dict):
        raise ValueError("scenario_assumptions must be a dictionary or None")

    # T15 treats the supplied date as the balance snapshot and forecasts the
    # following day through start + forecast_days. Normalize once so T12 uses
    # that exact same set of dates, even if the request crosses midnight.
    if forecast_start_date is None:
        forecast_start = pd.Timestamp.now().normalize()
    else:
        forecast_start = pd.to_datetime(forecast_start_date, errors="coerce")
        if pd.isna(forecast_start):
            raise ValueError("forecast_start_date must be a valid date")
        forecast_start = pd.Timestamp(forecast_start)
        if forecast_start.tzinfo is not None:
            forecast_start = forecast_start.tz_localize(None)
        forecast_start = forecast_start.normalize()

    raw_transactions = _read_csv(transaction_csv)
    categorized = _categorize(raw_transactions)

    # T07 → T10/T11 → T12.
    recurring_payments = detect_recurring_payments(categorized)
    upcoming_result = estimate_upcoming_payments(
        recurring_payments,
        horizon_days=forecast_days - 1,
        as_of_date=forecast_start + pd.Timedelta(days=1),
    )

    # T14 → T15 → T16 → T18. The same categorized data and cached T14 result
    # are passed downstream rather than repeatedly re-running historical work.
    historical_summary = analyze_historical_transactions(categorized)
    forecast_history = _history_without_recurring_expenses(categorized, historical_summary, recurring_payments)
    forecast = forecast_cash_flow(
        categorized,
        forecast_days=forecast_days,
        forecast_start_date=forecast_start,
        historical_result=forecast_history,
    )
    forecast["recurring_payments_excluded_from_baseline"] = forecast_history is not historical_summary
    balance_prediction = predict_daily_balances(
        forecast,
        starting_balance,
        upcoming_payments=upcoming_result,
    )
    low_balance_result = detect_low_balance(balance_prediction, balance_floor)

    # T19 compares this month's spending with monthly budgets and the T14
    # historical monthly averages. Category labels remain in original case.
    latest_month_spending, spending_period = _latest_month_expenses(categorized)
    overspending_result = detect_overspending(
        latest_month_spending,
        budgets,
        historical_category_spending=historical_summary,
    )
    overspending_result["period"] = spending_period

    # T20 → T21 → T24 → T25.
    risk_result = classify_financial_risk(
        forecast=forecast,
        balance_prediction=balance_prediction,
        low_balance_result=low_balance_result,
        overspending_result=overspending_result,
    )
    alerts = generate_alerts(
        low_balance_result=low_balance_result,
        overspending_result=overspending_result,
        forecast=forecast,
        risk_result=risk_result,
    )
    spending_recommendations = generate_spending_recommendations(
        historical_summary,
        budgets,
        overspending_result=overspending_result,
        recurring_results=recurring_payments,
    )
    savings_analysis = analyze_savings(historical_summary, spending_recommendations)

    # T27 consumes already calculated T15/T16 results. Default assumptions
    # produce a neutral baseline scenario; supplied assumptions remain explicit.
    scenario_results = calculate_scenario(
        forecast,
        transactions=categorized,
        current_balance=starting_balance,
        original_balance_prediction=balance_prediction,
        **(scenario_assumptions or {}),
    )

    # T30 → T31 summarize, but do not recalculate, upstream results.
    insights = generate_insights(
        historical_analysis=historical_summary,
        forecast=forecast,
        balance_prediction=balance_prediction,
        risk_result=risk_result,
        low_balance_result=low_balance_result,
        overspending_result=overspending_result,
    )
    prioritized_recommendations = build_recommendations(
        spending_recommendations=spending_recommendations,
        savings_analysis=savings_analysis,
        risk_result=risk_result,
        alerts=alerts,
    )

    forecast_accuracy = None
    accuracy_status = "Not calculated: no separate actual-data CSV was supplied."
    if actual_csv is not None:
        actual_transactions = _read_csv(actual_csv, actual_data=True)
        predicted_dates = {row["date"] for row in forecast.get("forecast", []) if isinstance(row, dict)}
        actual_dates = _actual_dates_with_values(actual_transactions)
        if predicted_dates & actual_dates:
            forecast_accuracy = calculate_forecast_accuracy(
                forecast,
                actual_transactions,
                predicted_balances=balance_prediction,
            )
            accuracy_status = "Calculated on exact dates shared by predictions and actual data."
        else:
            accuracy_status = "Not calculated: actual data has no usable measure on a forecast date."

    category_counts = categorized["category"].value_counts().to_dict() if not categorized.empty else {}
    return {
        "transaction_count": int(len(categorized)),
        "categorized_category_counts": {str(category): int(count) for category, count in category_counts.items()},
        "historical_summary": historical_summary,
        "recurring_payments": recurring_payments,
        "upcoming_payments": upcoming_result["upcoming_payments"],
        "upcoming_payment_total": upcoming_result["total_expected_amount"],
        "cash_flow_forecast": forecast,
        "balance_prediction": balance_prediction,
        "daily_predicted_balances": balance_prediction["daily_balances"],
        "low_balance_warnings": low_balance_result,
        "overspending_results": overspending_result,
        "financial_risk": risk_result,
        "alerts": alerts,
        "spending_recommendations": spending_recommendations,
        "savings_analysis": savings_analysis,
        "scenario_results": scenario_results,
        "ai_insights": insights,
        "prioritized_recommendations": prioritized_recommendations,
        "forecast_accuracy": forecast_accuracy,
        "forecast_accuracy_status": accuracy_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete FinSight AI analysis pipeline.")
    parser.add_argument("transaction_csv", type=Path)
    parser.add_argument("--current-balance", type=float, required=True)
    parser.add_argument("--minimum-balance", type=float, required=True)
    parser.add_argument("--budgets-json", type=Path, help="Optional JSON object mapping category to monthly budget")
    parser.add_argument("--actual-csv", type=Path, help="Optional actual transactions/balances for date-matched T32")
    parser.add_argument("--forecast-days", type=int, choices=sorted(SUPPORTED_FORECAST_DAYS), default=30)
    parser.add_argument("--forecast-start-date", help="YYYY-MM-DD; defaults to today")
    parser.add_argument("--scenario-json", type=Path, help="Optional JSON object of T27 scenario assumptions")
    args = parser.parse_args()

    budgets = None
    if args.budgets_json:
        with args.budgets_json.open(encoding="utf-8") as file:
            budgets = json.load(file)
    assumptions = None
    if args.scenario_json:
        with args.scenario_json.open(encoding="utf-8") as file:
            assumptions = json.load(file)

    result = run_full_analysis(
        args.transaction_csv,
        current_balance=args.current_balance,
        minimum_balance=args.minimum_balance,
        budgets=budgets,
        forecast_days=args.forecast_days,
        forecast_start_date=args.forecast_start_date,
        actual_csv=args.actual_csv,
        scenario_assumptions=assumptions,
    )
    # ASCII-escaped JSON avoids failures on Windows consoles using legacy
    # code pages while decoding to the same Unicode text for JSON consumers.
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    main()
