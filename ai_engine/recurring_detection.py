"""Explainable recurring-payment detection for FinSight AI.

The detector uses transaction text, amount similarity, and date intervals. It
does not call an external service. Pass a DataFrame or CSV path to
``detect_recurring_payments``; the returned list of dictionaries is JSON-ready.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


# These words describe the transaction, rather than the merchant, and are
# ignored when comparing descriptions (for example, "Netflix subscription").
GENERIC_WORDS = {
    "payment", "paid", "purchase", "transaction", "debit", "bill", "bills",
    "subscription", "monthly", "weekly", "yearly", "annual", "autopay",
    "standing", "instruction", "online", "pos", "charge", "premium",
}


def _description_key(value: Any) -> str:
    """Normalize a description into meaningful words for grouping."""
    if pd.isna(value):
        return ""
    words = re.findall(r"[a-z0-9]+", str(value).lower())
    return " ".join(word for word in words if word not in GENERIC_WORDS)


def _similar_text(left: str, right: str) -> bool:
    """Return true for the same merchant or a small spelling variation."""
    if not left or not right:
        return False
    if left == right:
        return True
    left_words, right_words = set(left.split()), set(right.split())
    # Shared, distinctive words are useful for descriptions with extra details.
    if left_words & right_words and len(left_words & right_words) / min(len(left_words), len(right_words)) >= 0.75:
        return True
    return difflib.SequenceMatcher(None, left, right).ratio() >= 0.82


def _amount_matches(amounts: pd.Series, tolerance: float = 0.25) -> pd.Series:
    """Keep amounts reasonably close to the group's median.

    A minimum allowance of ₹50 accommodates small bill changes; the percentage
    allowance scales for larger bills such as rent and utility charges.
    """
    median = float(amounts.median())
    allowed_difference = max(50.0, abs(median) * tolerance)
    return (amounts - median).abs() <= allowed_difference


def _frequency_for_dates(dates: pd.Series) -> tuple[str | None, float] | None:
    """Classify a date series and return the average gap in calendar days.

    A cadence is accepted when at least 75% of the gaps fall in its range.
    Otherwise the group is retained for reporting as an irregular pattern.
    """
    ordered = dates.sort_values().drop_duplicates()
    gaps = ordered.diff().dropna().dt.days.astype(float)
    if gaps.empty:
        return None

    # Ranges allow weekends, month lengths, and leap years to vary naturally.
    ranges = {
        "Weekly": (5, 9),
        "Monthly": (26, 35),
        "Yearly": (350, 380),
    }
    for frequency, (low, high) in ranges.items():
        matching = gaps.between(low, high)
        if float(matching.mean()) >= 0.75:
            return frequency, float(gaps.mean())
    return None, float(gaps.mean())


def _next_date(last_date: pd.Timestamp, frequency: str) -> pd.Timestamp:
    """Estimate the next calendar date, preserving month-end where relevant."""
    if frequency == "Weekly":
        return last_date + pd.Timedelta(days=7)
    if frequency == "Monthly":
        return last_date + pd.DateOffset(months=1)
    return last_date + pd.DateOffset(years=1)


def detect_recurring_payments(
    data: pd.DataFrame | str | Path,
    *,
    description_col: str = "description",
    amount_col: str = "amount",
    date_col: str = "date",
    type_col: str = "type",
    min_occurrences: int = 3,
    amount_tolerance: float = 0.25,
) -> list[dict[str, Any]]:
    """Detect repeated payments and return JSON-ready summary dictionaries.

    ``data`` can be an existing Pandas DataFrame or a CSV file path. Rows with
    missing descriptions, invalid dates, or invalid amounts are skipped. When a
    ``type`` column is present, credit/income rows are ignored so forecasts
    focus on outgoing payments.

    At least three dated occurrences are required by default. Set
    ``min_occurrences=2`` if an application prefers earlier, less certain
    detection.
    """
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.read_csv(data)
    required = {description_col, amount_col, date_col}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")
    if min_occurrences < 2:
        raise ValueError("min_occurrences must be at least 2")

    frame = frame.copy()
    frame["_description"] = frame[description_col].fillna("").astype(str).str.strip()
    frame["_key"] = frame[description_col].map(_description_key)
    frame["_date"] = pd.to_datetime(frame[date_col], errors="coerce")
    frame["_amount"] = pd.to_numeric(frame[amount_col], errors="coerce").abs()
    frame = frame[
        frame["_key"].ne("")
        & frame["_date"].notna()
        & frame["_amount"].map(lambda value: pd.notna(value) and math.isfinite(value))
    ].copy()

    if type_col in frame.columns:
        credits = frame[type_col].fillna("").astype(str).str.lower().str.strip()
        frame = frame[~credits.isin({"credit", "income", "inflow", "deposit"})]

    # Assign descriptions to the first sufficiently similar merchant key.
    representatives: list[str] = []
    key_to_group: dict[str, int] = {}
    for key in frame["_key"].drop_duplicates():
        group_id = next((i for i, representative in enumerate(representatives)
                         if _similar_text(key, representative)), None)
        if group_id is None:
            group_id = len(representatives)
            representatives.append(key)
        key_to_group[key] = group_id
    frame["_group"] = frame["_key"].map(key_to_group)

    results: list[dict[str, Any]] = []
    for _, group in frame.groupby("_group", sort=False):
        # Remove duplicate bank/import rows before calculating counts or means.
        # The same merchant can have distinct charges on the same day when the
        # amounts differ, so amount is part of the duplicate key.
        group = group.drop_duplicates(subset=["_date", "_amount"])

        # Filter amount outliers so an unrelated one-off charge from the same
        # merchant does not distort the recurrence interval or average.
        close_amounts = _amount_matches(group["_amount"], amount_tolerance)
        group = group[close_amounts].sort_values("_date")
        distinct_dates = group["_date"].drop_duplicates()
        if len(distinct_dates) < min_occurrences:
            continue

        cadence = _frequency_for_dates(distinct_dates)
        if cadence is None:
            continue
        frequency, average_interval = cadence
        last_date = distinct_dates.max()
        # Use the most common original description as the readable label.
        description = group["_description"].value_counts().index[0]
        results.append({
            "description": description,
            "average_amount": round(float(group["_amount"].mean()), 2),
            "frequency": frequency or "Irregular",
            "recurrence_interval_days": round(average_interval, 1),
            "occurrences": int(len(distinct_dates)),
            "next_payment_date": (
                _next_date(last_date, frequency).strftime("%Y-%m-%d")
                if frequency else None
            ),
            "is_recurring": frequency is not None,
        })

    return sorted(results, key=lambda payment: (payment["frequency"], payment["description"].lower()))


def main() -> None:
    """Command-line entry point for a quick local demo."""
    default_csv = Path(__file__).with_name("transactions.csv")
    parser = argparse.ArgumentParser(description="Detect recurring payments in a CSV file.")
    parser.add_argument("csv_path", nargs="?", default=default_csv, type=Path)
    args = parser.parse_args()
    payments = detect_recurring_payments(args.csv_path)
    print(json.dumps(payments, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
