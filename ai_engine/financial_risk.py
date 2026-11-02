"""T20: explainable rule-based financial risk classification."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

def _finite(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def classify_financial_risk(
    forecast: dict[str, Any] | None = None,
    balance_prediction: dict[str, Any] | None = None,
    low_balance_result: dict[str, Any] | None = None,
    overspending_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combine T15/T16/T18/T19 outputs into a scored risk level.

    Rules (additive and capped at 100): negative projected balance adds 70;
    at least one low-balance event adds 25; negative total projected net cash
    flow adds 20; each budget-overrun category adds 10 up to 20; and each
    unusual-spending category adds 10 up to 20. A negative predicted balance
    forces at least CRITICAL. Otherwise score bands are LOW 0-19, MEDIUM 20-39,
    HIGH 40-69, and CRITICAL 70-100. This is a transparent heuristic, not a
    trained machine-learning model.
    """
    forecast = forecast if isinstance(forecast, dict) else {}
    balance_prediction = balance_prediction if isinstance(balance_prediction, dict) else {}
    low_balance_result = low_balance_result if isinstance(low_balance_result, dict) else {}
    overspending_result = overspending_result if isinstance(overspending_result, dict) else {}

    reasons: list[str] = []
    score = 0

    balance_rows = balance_prediction.get("daily_balances", [])
    negative_daily_balance = any(
        isinstance(row, dict) and _finite(row.get("expected_balance"), math.inf) < 0
        for row in balance_rows if isinstance(balance_rows, list)
    )
    ending_balance = _finite(balance_prediction.get("ending_balance"), math.inf)
    negative_balance = negative_daily_balance or ending_balance < 0
    if negative_balance:
        score += 70
        reasons.append("At least one projected daily account balance is below zero.")

    low_events = low_balance_result.get("warnings", [])
    low_count = len(low_events) if isinstance(low_events, list) else 0
    low_count = max(low_count, int(_finite(low_balance_result.get("warning_count"))))
    if low_count:
        score += 25
        reasons.append(f"{low_count} projected low-balance warning event(s) were detected.")

    net_cash_flow = _finite(forecast.get("predicted_net_cash_flow"))
    if net_cash_flow < 0:
        score += 20
        reasons.append("Forecast net cash flow is negative over the selected horizon.")

    alerts = overspending_result.get("alerts", [])
    if not isinstance(alerts, list):
        alerts = []
    budget_overruns = sum(
        1 for row in alerts
        if isinstance(row, dict) and (row.get("budget_overrun") or "budget_overrun" in row.get("alert_reasons", []))
    )
    unusual_spending = sum(
        1 for row in alerts
        if isinstance(row, dict) and (row.get("unusual_spending") or "unusual_vs_history" in row.get("alert_reasons", []))
    )
    if budget_overruns:
        score += min(20, budget_overruns * 10)
        reasons.append(f"Budget overruns were detected in {budget_overruns} category/categories.")
    if unusual_spending:
        score += min(20, unusual_spending * 10)
        reasons.append(f"Unusual historical spending was detected in {unusual_spending} category/categories.")

    score = min(100, score)
    if negative_balance:
        level = "CRITICAL"
        score = max(70, score)
    elif score >= 70:
        level = "CRITICAL"
    elif score >= 40:
        level = "HIGH"
    elif score >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"
    if not reasons:
        reasons.append("No configured forecast, balance, or spending risk rules were triggered.")

    return {
        "risk_level": level,
        "risk_score": score,
        "reasons": reasons,
        "classification_method": "Explainable rule-based heuristic; not a trained ML model",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify risk from T15/T16/T18/T19 JSON results.")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    print(json.dumps(classify_financial_risk(
        data.get("forecast"), data.get("balance_prediction"),
        data.get("low_balance_result"), data.get("overspending_result"),
    ), indent=2))


if __name__ == "__main__":
    main()
