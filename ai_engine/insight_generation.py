"""T30: create concise rule-based explanations from FinSight analysis outputs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _money(value: float) -> str:
    return f"₹{value:,.2f}"


def generate_insights(
    historical_analysis: dict[str, Any] | None = None,
    forecast: dict[str, Any] | None = None,
    balance_prediction: dict[str, Any] | None = None,
    risk_result: dict[str, Any] | None = None,
    low_balance_result: dict[str, Any] | None = None,
    overspending_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Explain signals present in T14/T15/T16/T18/T19/T20 outputs.

    Text is generated from deterministic templates and supplied values. No
    language model is called, and no trend or risk condition is inferred when
    its source result is absent.
    """
    historical_analysis = historical_analysis if isinstance(historical_analysis, dict) else {}
    forecast = forecast if isinstance(forecast, dict) else {}
    balance_prediction = balance_prediction if isinstance(balance_prediction, dict) else {}
    risk_result = risk_result if isinstance(risk_result, dict) else {}
    low_balance_result = low_balance_result if isinstance(low_balance_result, dict) else {}
    overspending_result = overspending_result if isinstance(overspending_result, dict) else {}

    insights: list[dict[str, Any]] = []

    def add(kind: str, title: str, message: str, *, severity: str = "INFO",
            amount: float | None = None, date: str | None = None,
            category: str | None = None) -> None:
        insights.append({
            "type": kind,
            "title": title,
            "message": message,
            "severity": severity,
            "amount": round(amount, 2) if amount is not None else None,
            "date": date,
            "category": category,
        })

    level = str(risk_result.get("risk_level", "")).strip().upper()
    valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    if level in valid_levels:
        score = _number(risk_result.get("risk_score"))
        score_text = f" (score {score:.0f}/100)" if score is not None else ""
        reasons = risk_result.get("reasons", [])
        reason_text = "; ".join(str(reason) for reason in reasons if str(reason).strip()) if isinstance(reasons, list) else ""
        level_messages = {
            "LOW": "The supplied risk assessment found few or no material warning signals.",
            "MEDIUM": "The supplied risk assessment found a warning that is worth monitoring.",
            "HIGH": "The supplied risk assessment found significant pressure on the forecast.",
            "CRITICAL": "The supplied risk assessment found an urgent financial risk signal.",
        }
        message = f"Financial risk is {level}{score_text}. {level_messages[level]}"
        if reason_text:
            message += f" Reason: {reason_text}"
        add("risk", f"{level.title()} financial risk", message, severity=level)

    for warning in low_balance_result.get("warnings", []) if isinstance(low_balance_result.get("warnings", []), list) else []:
        if not isinstance(warning, dict):
            continue
        lowest = _number(warning.get("lowest_predicted_balance"))
        threshold = _number(warning.get("threshold"))
        date = warning.get("start_date")
        if lowest is None or not date:
            continue
        message = f"The predicted balance falls to {_money(lowest)} beginning {date}."
        if threshold is not None:
            message += f" This is below the configured minimum of {_money(threshold)}."
        add("low_balance", "Predicted low balance", message,
            severity="CRITICAL" if lowest < 0 else "HIGH", amount=lowest, date=str(date))

    ending_balance = _number(balance_prediction.get("ending_balance"))
    daily_balances = balance_prediction.get("daily_balances", [])
    balance_date = (
        daily_balances[-1].get("date")
        if isinstance(daily_balances, list) and daily_balances and isinstance(daily_balances[-1], dict)
        else None
    )
    if ending_balance is not None:
        message = f"The predicted ending account balance is {_money(ending_balance)}."
        if balance_date:
            message += f" This estimate is for {balance_date}."
        add("balance_prediction", "Projected ending balance", message,
            severity="CRITICAL" if ending_balance < 0 else "INFO",
            amount=ending_balance, date=balance_date)

    for row in overspending_result.get("alerts", []) if isinstance(overspending_result.get("alerts", []), list) else []:
        if not isinstance(row, dict):
            continue
        category = str(row.get("category", "")).strip()
        if not category:
            continue
        reasons = row.get("alert_reasons", [])
        reasons = reasons if isinstance(reasons, list) else []
        parts = []
        actual = _number(row.get("actual_spending"))
        budget = _number(row.get("budget"))
        if row.get("budget_overrun") or "budget_overrun" in reasons:
            if actual is not None and budget is not None:
                parts.append(f"actual spending was {_money(actual)} against a {_money(budget)} budget")
            else:
                parts.append("spending exceeded its configured budget")
        if row.get("unusual_spending") or "unusual_vs_history" in reasons:
            baseline = _number(row.get("historical_monthly_average"))
            parts.append(
                f"spending was unusually high compared with the {_money(baseline)} monthly historical average"
                if baseline is not None else "spending was unusually high compared with history"
            )
        if parts:
            add("overspending", f"{category} spending needs review", f"In {category}, " + " and ".join(parts) + ".",
                severity="MEDIUM", amount=actual, date=row.get("period_end_date"), category=category)

    net = _number(forecast.get("predicted_net_cash_flow"))
    if net is not None:
        days = _number(forecast.get("forecast_days"))
        period = f"over the next {int(days)} days" if days is not None and days > 0 else "over the forecast period"
        total_income = _number(forecast.get("total_predicted_income"))
        total_expenses = _number(forecast.get("total_predicted_expenses"))
        message = f"Predicted net cash flow is {_money(net)} {period}."
        if total_income is not None and total_expenses is not None:
            message += f" The forecast includes {_money(total_income)} income and {_money(total_expenses)} expenses."

        monthly_rows = historical_analysis.get("monthly_summary", [])
        latest = monthly_rows[-1] if isinstance(monthly_rows, list) and monthly_rows else None
        if isinstance(latest, dict) and days is not None and days > 0:
            last_net = _number(latest.get("net_cash_flow"))
            if last_net is not None:
                prior_scaled = last_net * days / (365.2425 / 12)
                change = net - prior_scaled
                direction = "higher" if change > 0 else "lower" if change < 0 else "about the same"
                message += (
                    f" Compared with the latest historical month's net cash flow scaled to this period, "
                    f"the forecast is {_money(abs(change))} {direction}."
                )
        add("cash_flow_forecast", "Cash-flow outlook", message,
            severity="HIGH" if net < 0 else "INFO", amount=net,
            date=forecast.get("forecast_end_date"))

    trend = str(historical_analysis.get("expense_trend", "")).strip().capitalize()
    if trend in {"Increasing", "Decreasing", "Stable"}:
        monthly_rows = historical_analysis.get("monthly_summary", [])
        message = f"Historical expenses are {trend.lower()} across the analyzed period."
        if isinstance(monthly_rows, list) and len(monthly_rows) >= 2:
            first = _number(monthly_rows[0].get("expenses")) if isinstance(monthly_rows[0], dict) else None
            last = _number(monthly_rows[-1].get("expenses")) if isinstance(monthly_rows[-1], dict) else None
            if first is not None and last is not None:
                message += f" They changed from {_money(first)} to {_money(last)}."
        add("expense_trend", f"{trend} expense trend", message,
            severity="MEDIUM" if trend == "Increasing" else "INFO")

    if not insights and not any((historical_analysis, forecast, balance_prediction,
                                 risk_result, low_balance_result, overspending_result)):
        overview = "No analysis results were supplied, so there are no financial insights to summarize."
    elif not insights:
        overview = "The supplied results contain no supported insight signals."
    else:
        overview = f"Generated {len(insights)} insight(s) from the supplied analysis results."
    return {
        "summary": overview,
        "insights": insights,
        "generation_method": "Rule-based templates; no trained model or external language model used",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate insights from FinSight analysis JSON.")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    print(json.dumps(generate_insights(
        data.get("historical_analysis"), data.get("forecast"), data.get("balance_prediction"),
        data.get("risk_result"), data.get("low_balance_result"), data.get("overspending_result"),
    ), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
