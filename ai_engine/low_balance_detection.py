"""T18: detect contiguous low-balance warning events."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


def detect_low_balance(
    balance_prediction: dict[str, Any] | pd.DataFrame,
    minimum_balance: float,
) -> dict[str, Any]:
    """Group consecutive forecast dates below a configurable balance floor.

    One warning is returned per contiguous below-threshold spell, preventing
    duplicate daily alerts for a single event while retaining all affected
    dates and balances inside that warning.
    """
    try:
        threshold = float(minimum_balance)
    except (TypeError, ValueError):
        raise ValueError("minimum_balance must be a finite number") from None
    if not math.isfinite(threshold):
        raise ValueError("minimum_balance must be a finite number")

    if isinstance(balance_prediction, pd.DataFrame):
        rows = balance_prediction.to_dict(orient="records")
    elif isinstance(balance_prediction, dict):
        rows = balance_prediction.get("daily_balances", [])
    else:
        raise TypeError("balance_prediction must be a T16 result dictionary or DataFrame")

    valid_rows: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        day = pd.to_datetime(row.get("date"), errors="coerce")
        try:
            balance = float(row.get("expected_balance"))
        except (TypeError, ValueError):
            continue
        if pd.isna(day) or not math.isfinite(balance):
            continue
        valid_rows.append({"date": pd.Timestamp(day).normalize(), "balance": balance})
    # Repeated input rows for one calendar day should not create two alerts.
    by_date: dict[pd.Timestamp, float] = {}
    for row in valid_rows:
        by_date[row["date"]] = min(by_date.get(row["date"], math.inf), row["balance"])
    valid_rows = [
        {"date": day, "balance": balance}
        for day, balance in sorted(by_date.items(), key=lambda item: item[0])
    ]

    warnings: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []

    def finish_event() -> None:
        if not active:
            return
        affected = [
            {"date": row["date"].strftime("%Y-%m-%d"), "predicted_balance": round(row["balance"], 2)}
            for row in active
        ]
        warnings.append({
            "start_date": affected[0]["date"],
            "end_date": affected[-1]["date"],
            "affected_dates": affected,
            "lowest_predicted_balance": min(row["predicted_balance"] for row in affected),
            "threshold": round(threshold, 2),
        })
        active.clear()

    previous_date: pd.Timestamp | None = None
    for row in valid_rows:
        below = row["balance"] < threshold
        consecutive = previous_date is None or row["date"] == previous_date + pd.Timedelta(days=1)
        if not below or (active and not consecutive):
            finish_event()
        if below:
            active.append(row)
        previous_date = row["date"]
    finish_event()

    return {
        "minimum_balance": round(threshold, 2),
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Find low-balance events in T16 JSON output.")
    parser.add_argument("balance_json", type=Path)
    parser.add_argument("--minimum-balance", type=float, required=True)
    args = parser.parse_args()
    with args.balance_json.open(encoding="utf-8") as file:
        result = detect_low_balance(json.load(file), args.minimum_balance)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
