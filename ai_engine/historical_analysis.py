"""Historical income and expense analysis for FinSight AI."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

try:  # Use the project's existing categorizer for rows without a category.
    from .categorization import categorize_transaction
except ImportError:  # Supports running this file directly from ai_engine/.
    from categorization import categorize_transaction


INCOME_TYPES = {"credit", "income", "inflow", "deposit"}
EXPENSE_TYPES = {"debit", "expense", "outflow", "withdrawal"}


def _empty_result() -> dict[str, Any]:
    """Return the same structured response when the input has no usable rows."""
    return {
        "total_income": 0.0,
        "total_expenses": 0.0,
        "net_cash_flow": 0.0,
        "average_monthly_income": 0.0,
        "average_monthly_expenses": 0.0,
        "monthly_summary": [],
        "category_wise_expenses": {},
        "expense_trend": "Stable",
    }


def _read_transactions(data: pd.DataFrame | str | Path) -> pd.DataFrame:
    """Read a DataFrame or CSV; treat an empty CSV as an empty transaction set."""
    if isinstance(data, pd.DataFrame):
        return data.copy()
    try:
        return pd.read_csv(data)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _transaction_kind(row: pd.Series) -> str | None:
    """Determine whether a row is income or expense from type/category/text."""
    transaction_type = str(row.get("type", "")).strip().lower()
    if transaction_type in INCOME_TYPES:
        return "income"
    if transaction_type in EXPENSE_TYPES:
        return "expense"

    category = row.get("category")
    if pd.notna(category) and str(category).strip():
        return "income" if str(category).strip().lower() == "income" else "expense"

    description = row.get("description", "")
    if pd.isna(description) or not str(description).strip():
        return None
    inferred_category = categorize_transaction(description)
    return "income" if inferred_category == "Income" else "expense"


def _expense_trend(monthly_expenses: list[float]) -> str:
    """Classify the direction using average change from first to last month.

    Changes of no more than 1% of the average monthly expense (or ₹1 for very
    small amounts) are treated as stable to avoid calling rounding noise a trend.
    """
    if len(monthly_expenses) < 2:
        return "Stable"
    average = sum(monthly_expenses) / len(monthly_expenses)
    average_monthly_change = (monthly_expenses[-1] - monthly_expenses[0]) / (len(monthly_expenses) - 1)
    tolerance = max(1.0, abs(average) * 0.01)
    if average_monthly_change > tolerance:
        return "Increasing"
    if average_monthly_change < -tolerance:
        return "Decreasing"
    return "Stable"


def analyze_historical_transactions(
    data: pd.DataFrame | str | Path,
    *,
    date_col: str = "date",
    amount_col: str = "amount",
    type_col: str = "type",
    category_col: str = "category",
    description_col: str = "description",
) -> dict[str, Any]:
    """Calculate totals, monthly summaries, categories, and expense direction.

    Invalid rows (missing/invalid dates or amounts) are skipped. The existing
    ``type`` column is used to distinguish credit from debit transactions.
    If ``type`` is absent or unrecognized, the category or existing description
    categorizer is used as a fallback. Month averages cover every calendar
    month between the earliest and latest valid transaction, including months
    with no transactions.
    """
    frame = _read_transactions(data)
    if frame.empty:
        return _empty_result()

    required = {date_col, amount_col}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        # A header-only file (or a file with unrelated columns) contains no
        # analyzable transaction records and receives a predictable empty result.
        if len(frame) == 0:
            return _empty_result()
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing_columns))}")

    frame = frame.copy()
    frame["_date"] = pd.to_datetime(frame[date_col], errors="coerce")
    frame["_amount"] = pd.to_numeric(frame[amount_col], errors="coerce").abs()
    finite_amount = frame["_amount"].map(
        lambda value: pd.notna(value) and math.isfinite(value)
    )
    frame = frame[frame["_date"].notna() & finite_amount].copy()
    if frame.empty:
        return _empty_result()

    # Normalize the column names expected by the classifier, including custom
    # column-name use cases, without changing the caller's original DataFrame.
    if type_col != "type":
        frame["type"] = frame[type_col] if type_col in frame.columns else ""
    if category_col != "category":
        frame["category"] = frame[category_col] if category_col in frame.columns else None
    if description_col != "description":
        frame["description"] = frame[description_col] if description_col in frame.columns else ""
    elif "description" not in frame.columns:
        frame["description"] = ""

    frame["_kind"] = frame.apply(_transaction_kind, axis=1)
    frame = frame[frame["_kind"].notna()].copy()
    if frame.empty:
        return _empty_result()

    frame["_month"] = frame["_date"].dt.to_period("M")
    frame["_category"] = frame.get("category", pd.Series(index=frame.index, dtype=object))
    missing_category = frame["_category"].isna() | frame["_category"].astype(str).str.strip().eq("")
    if missing_category.any():
        descriptions = frame.loc[missing_category, "description"].fillna("")
        frame.loc[missing_category, "_category"] = descriptions.map(categorize_transaction)

    income_rows = frame[frame["_kind"] == "income"]
    expense_rows = frame[frame["_kind"] == "expense"]
    total_income = float(income_rows["_amount"].sum())
    total_expenses = float(expense_rows["_amount"].sum())

    # Include zero-activity months between the first and last transaction so
    # averages and trends use a consistent calendar span.
    first_month = frame["_month"].min()
    last_month = frame["_month"].max()
    all_months = pd.period_range(first_month, last_month, freq="M")
    monthly_summary: list[dict[str, Any]] = []
    monthly_income_values: list[float] = []
    monthly_expense_values: list[float] = []
    for month in all_months:
        this_month = frame[frame["_month"] == month]
        month_income = float(this_month.loc[this_month["_kind"] == "income", "_amount"].sum())
        month_expenses = float(this_month.loc[this_month["_kind"] == "expense", "_amount"].sum())
        monthly_income_values.append(month_income)
        monthly_expense_values.append(month_expenses)
        monthly_summary.append({
            "month": str(month),
            "income": round(month_income, 2),
            "expenses": round(month_expenses, 2),
            "net_cash_flow": round(month_income - month_expenses, 2),
        })

    category_totals = (
        expense_rows.groupby("_category")["_amount"].sum().sort_index()
        if not expense_rows.empty else pd.Series(dtype=float)
    )
    monthly_count = len(all_months)
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_cash_flow": round(total_income - total_expenses, 2),
        "average_monthly_income": round(sum(monthly_income_values) / monthly_count, 2),
        "average_monthly_expenses": round(sum(monthly_expense_values) / monthly_count, 2),
        "monthly_summary": monthly_summary,
        "category_wise_expenses": {
            str(category): round(float(amount), 2)
            for category, amount in category_totals.items()
        },
        "expense_trend": _expense_trend(monthly_expense_values),
    }


def main() -> None:
    """Print a JSON-compatible historical analysis for a transaction CSV."""
    default_csv = Path(__file__).with_name("transactions.csv")
    parser = argparse.ArgumentParser(description="Analyze historical FinSight transactions.")
    parser.add_argument("csv_path", nargs="?", default=default_csv, type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze_historical_transactions(args.csv_path), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
