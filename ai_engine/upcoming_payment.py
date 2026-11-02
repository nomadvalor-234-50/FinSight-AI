"""Estimate upcoming commitments from recurring_detection.py results.

The functions in this module use only the recurring payment summaries already
produced by FinSight AI. They make no network or external AI calls.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

try:  # Works both as ``ai_engine.upcoming_payment`` and as a local script.
    from .recurring_detection import detect_recurring_payments
except ImportError:  # pragma: no cover - exercised by direct script execution
    from recurring_detection import detect_recurring_payments


SUPPORTED_FREQUENCIES = {"weekly", "monthly", "yearly"}


def _parse_date(value: Any) -> pd.Timestamp | None:
    """Parse a date safely and normalize it to a timezone-free calendar day."""
    if value is None or (not isinstance(value, (list, tuple, dict)) and pd.isna(value)):
        return None
    try:
        parsed = pd.Timestamp(value)
        if pd.isna(parsed):
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.tz_localize(None)
        return parsed.normalize()
    except (TypeError, ValueError, OverflowError):
        return None


def _is_recurring(value: Any) -> bool:
    """Recognize boolean and CSV-style true values without truthy-string bugs."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def _date_after(anchor: pd.Timestamp, frequency: str, step: int) -> pd.Timestamp:
    """Get a schedule date from its original anchor to avoid month-end drift."""
    if frequency == "weekly":
        return anchor + pd.Timedelta(days=7 * step)
    if frequency == "monthly":
        return anchor + pd.DateOffset(months=step)
    return anchor + pd.DateOffset(years=step)


def get_upcoming_payments(
    recurring_results: Iterable[dict[str, Any]] | pd.DataFrame,
    *,
    horizon_days: int = 30,
    as_of_date: str | date | datetime | pd.Timestamp | None = None,
) -> list[dict[str, Any]]:
    """Create payment records due from ``as_of_date`` through the horizon end.

    ``recurring_results`` is the list returned by
    ``detect_recurring_payments``. All scheduled instances in the requested
    window are returned, not just the first one. Dates on both the start and
    end of the window are included. Invalid records are skipped safely.
    """
    if not isinstance(horizon_days, int) or isinstance(horizon_days, bool) or horizon_days < 0:
        raise ValueError("horizon_days must be a non-negative integer")

    start = _parse_date(as_of_date) if as_of_date is not None else pd.Timestamp.now().normalize()
    if start is None:
        raise ValueError("as_of_date must be a valid date")
    end = start + pd.Timedelta(days=horizon_days)

    if isinstance(recurring_results, pd.DataFrame):
        records = recurring_results.to_dict(orient="records")
    else:
        records = recurring_results

    payments: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or not _is_recurring(record.get("is_recurring")):
            continue

        description = record.get("description")
        if description is None or pd.isna(description) or not str(description).strip():
            continue

        try:
            amount = float(record.get("average_amount"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(amount) or amount < 0:
            continue

        next_date = _parse_date(record.get("next_payment_date"))
        frequency = str(record.get("frequency", "")).strip().lower()
        if next_date is None or frequency not in SUPPORTED_FREQUENCIES:
            continue

        # Keep the detector's next date as the schedule anchor. Calculating
        # each date from this anchor avoids adding 1 month, then 2 months, etc.
        schedule_anchor = next_date

        # If the detector's next date is in the past, move forward along the
        # same schedule until it reaches today. The 10,000-step guard prevents
        # malformed/extremely old data from causing an endless loop.
        step = 0
        while next_date < start and step < 10_000:
            step += 1
            next_date = _date_after(schedule_anchor, frequency, step)
        if next_date < start:
            continue

        while next_date <= end:
            payments.append({
                "description": str(description).strip(),
                "expected_amount": round(amount, 2),
                "frequency": frequency.title(),
                "expected_payment_date": next_date.strftime("%Y-%m-%d"),
            })
            step += 1
            next_date = _date_after(schedule_anchor, frequency, step)

    return sorted(payments, key=lambda payment: (payment["expected_payment_date"], payment["description"].lower()))


def calculate_total_expected_amount(payments: Iterable[dict[str, Any]]) -> float:
    """Sum valid ``expected_amount`` values from upcoming payment records."""
    total = 0.0
    for payment in payments:
        if not isinstance(payment, dict):
            continue
        try:
            amount = float(payment.get("expected_amount"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(amount) and amount >= 0:
            total += amount
    return round(total, 2)


def estimate_upcoming_payments(
    recurring_results: Iterable[dict[str, Any]] | pd.DataFrame,
    *,
    horizon_days: int = 30,
    as_of_date: str | date | datetime | pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Return upcoming payment rows and their total for a forecast window."""
    payments = get_upcoming_payments(
        recurring_results,
        horizon_days=horizon_days,
        as_of_date=as_of_date,
    )
    return {
        "upcoming_payments": payments,
        "total_expected_amount": calculate_total_expected_amount(payments),
    }


def forecast_from_transactions(
    data: pd.DataFrame | str | Path,
    *,
    horizon_days: int = 30,
    as_of_date: str | date | datetime | pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Run T10 detection and estimate upcoming payments from the same input."""
    recurring_results = detect_recurring_payments(data)
    return estimate_upcoming_payments(
        recurring_results,
        horizon_days=horizon_days,
        as_of_date=as_of_date,
    )


def main() -> None:
    """Command-line entry point: analyze a transaction CSV and print JSON."""
    default_csv = Path(__file__).with_name("transactions.csv")
    parser = argparse.ArgumentParser(description="Estimate upcoming recurring payments.")
    parser.add_argument("csv_path", nargs="?", default=default_csv, type=Path)
    parser.add_argument("--horizon-days", type=int, default=30)
    parser.add_argument("--as-of", help="Forecast start date (YYYY-MM-DD); defaults to today.")
    args = parser.parse_args()
    forecast = forecast_from_transactions(
        args.csv_path,
        horizon_days=args.horizon_days,
        as_of_date=args.as_of,
    )
    print(json.dumps(forecast, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
