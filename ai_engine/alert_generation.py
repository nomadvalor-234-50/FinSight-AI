"""T21: convert existing risk-analysis results into actionable alerts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _money(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def generate_alerts(
    low_balance_result: dict[str, Any] | None = None,
    overspending_result: dict[str, Any] | None = None,
    forecast: dict[str, Any] | None = None,
    risk_result: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build one structured alert per detected condition/event.

    Inputs are the existing T15/T18/T19/T20 return dictionaries. This function
    only emits alerts for positive detector results; it does not infer new
    conditions from raw transactions.
    """
    low_balance_result = low_balance_result if isinstance(low_balance_result, dict) else {}
    overspending_result = overspending_result if isinstance(overspending_result, dict) else {}
    forecast = forecast if isinstance(forecast, dict) else {}
    risk_result = risk_result if isinstance(risk_result, dict) else {}

    alerts: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def add(alert: dict[str, Any], key: tuple[Any, ...]) -> None:
        if key not in seen:
            seen.add(key)
            alerts.append(alert)

    warnings = low_balance_result.get("warnings", [])
    for warning in warnings if isinstance(warnings, list) else []:
        if not isinstance(warning, dict):
            continue
        start_date = warning.get("start_date")
        end_date = warning.get("end_date", start_date)
        lowest = _money(warning.get("lowest_predicted_balance"))
        if not start_date or lowest is None:
            continue
        threshold = _money(warning.get("threshold"))
        severity = "CRITICAL" if lowest < 0 else "HIGH"
        reason = f"Predicted balance of {lowest:.2f} is below the configured threshold"
        if threshold is not None:
            reason += f" of {threshold:.2f}"
        reason += "."
        add({
            "title": "Low balance warning",
            "severity": severity,
            "message": f"Your predicted balance is below the minimum from {start_date} to {end_date}.",
            "reason": reason,
            "affected_date": start_date,
            "suggested_action": "Review upcoming payments and consider moving non-essential spending or adding funds.",
        }, ("low_balance", str(start_date), str(end_date)))

    rows = overspending_result.get("alerts", [])
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        category = str(row.get("category", "")).strip()
        actual = _money(row.get("actual_spending"))
        if not category or actual is None:
            continue
        reasons = row.get("alert_reasons", [])
        reasons = reasons if isinstance(reasons, list) else []
        budget_overrun = bool(row.get("budget_overrun")) or "budget_overrun" in reasons
        unusual = bool(row.get("unusual_spending")) or "unusual_vs_history" in reasons
        if not (budget_overrun or unusual):
            continue
        percentage = _money(row.get("overspending_percentage"))
        if budget_overrun and percentage is not None and percentage >= 50:
            severity = "HIGH"
        elif budget_overrun:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        reason_parts = []
        if budget_overrun:
            budget = _money(row.get("budget"))
            excess = _money(row.get("excess_amount"))
            reason_parts.append(
                f"Spending was {excess:.2f} over the {budget:.2f} budget"
                if budget is not None and excess is not None
                else "Spending exceeded the configured category budget"
            )
        if unusual:
            baseline = _money(row.get("historical_monthly_average"))
            reason_parts.append(
                f"spending was unusually high versus its historical monthly average of {baseline:.2f}"
                if baseline is not None else "spending was unusually high versus history"
            )
        add({
            "title": f"Overspending in {category}",
            "severity": severity,
            "message": f"{category} spending is above a detected budget or historical threshold.",
            "reason": "; ".join(reason_parts) + ".",
            "affected_date": row.get("period_end_date"),
            "suggested_action": f"Review recent {category.lower()} purchases and adjust the category budget or spending plan.",
        }, ("overspending", category.casefold()))

    net_cash_flow = _money(forecast.get("predicted_net_cash_flow"))
    if net_cash_flow is not None and net_cash_flow < 0:
        daily = forecast.get("forecast", [])
        negative_dates = [
            row.get("date") for row in daily
            if isinstance(row, dict) and (_money(row.get("predicted_net_cash_flow")) or 0) < 0
        ] if isinstance(daily, list) else []
        add({
            "title": "Negative forecast cash flow",
            "severity": "HIGH",
            "message": "Forecast expenses exceed forecast income over the selected period.",
            "reason": f"Predicted net cash flow is {net_cash_flow:.2f}.",
            "affected_date": negative_dates[0] if negative_dates else forecast.get("forecast_end_date"),
            "suggested_action": "Review planned expenses and upcoming commitments, then consider postponing non-essential costs.",
        }, ("negative_cash_flow",))

    if str(risk_result.get("risk_level", "")).strip().upper() == "CRITICAL":
        reasons = risk_result.get("reasons", [])
        reason_text = "; ".join(str(reason) for reason in reasons) if isinstance(reasons, list) else str(reasons)
        if not reason_text:
            reason_text = "The T20 risk classifier assigned CRITICAL risk."
        add({
            "title": "Critical financial risk",
            "severity": "CRITICAL",
            "message": "The combined financial risk assessment is critical and needs prompt review.",
            "reason": reason_text,
            "affected_date": None,
            "suggested_action": "Review the projected balance, near-term payments, and spending alerts promptly.",
        }, ("critical_risk",))

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return sorted(alerts, key=lambda alert: (severity_order[alert["severity"]], alert["title"].lower()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate alerts from T15/T18/T19/T20 result JSON.")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    print(json.dumps(generate_alerts(data.get("low_balance_result"),
                                     data.get("overspending_result"),
                                     data.get("forecast"), data.get("risk_result")), indent=2))


if __name__ == "__main__":
    main()
