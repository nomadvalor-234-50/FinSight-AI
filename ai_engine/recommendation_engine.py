"""T31: merge existing recommendations into a prioritized action list."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_TO_PRIORITY = {"CRITICAL": "URGENT", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}


def _amount(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _risk_priority(risk_result: dict[str, Any]) -> str:
    level = str(risk_result.get("risk_level", "LOW")).strip().upper()
    return SEVERITY_TO_PRIORITY.get(level, "LOW")


def build_recommendations(
    spending_recommendations: dict[str, Any] | list[dict[str, Any]] | None = None,
    savings_analysis: dict[str, Any] | None = None,
    risk_result: dict[str, Any] | None = None,
    alerts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Combine T24/T25/T20/T21 outputs without fabricating benefits.

    More urgent alert severity sets priority; ties sort by estimated monthly
    benefit. T25 contributes a general savings action only when T24 has no
    itemized recommendations, preventing the same benefit being listed twice.
    Benefits are estimates and never described as guaranteed.
    """
    if isinstance(spending_recommendations, dict):
        source_rows = spending_recommendations.get("recommendations", [])
    elif isinstance(spending_recommendations, list):
        source_rows = spending_recommendations
    else:
        source_rows = []
    savings_analysis = savings_analysis if isinstance(savings_analysis, dict) else {}
    risk_result = risk_result if isinstance(risk_result, dict) else {}
    alerts = alerts if isinstance(alerts, list) else []
    base_priority = _risk_priority(risk_result)

    alert_by_category: dict[str, str] = {}
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        title = str(alert.get("title", "")).lower()
        category = str(alert.get("category", "")).strip().casefold()
        severity = str(alert.get("severity", "")).strip().upper()
        if category and "overspend" in title:
            priority = SEVERITY_TO_PRIORITY.get(severity, "LOW")
            current = alert_by_category.get(category, "LOW")
            if PRIORITY_ORDER[priority] < PRIORITY_ORDER[current]:
                alert_by_category[category] = priority

    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(row: dict[str, Any], dedupe_key: tuple[str, str]) -> None:
        if dedupe_key not in seen:
            seen.add(dedupe_key)
            candidates.append(row)

    for row in source_rows if isinstance(source_rows, list) else []:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title", "")).strip()
        category = str(row.get("category", "")).strip()
        action = str(row.get("suggested_action", "")).strip()
        description = str(row.get("explanation", "")).strip()
        if not title or not action:
            continue
        benefit = _amount(row.get("estimated_monthly_savings"))
        priority = alert_by_category.get(category.casefold(), base_priority)
        if str(risk_result.get("risk_level", "")).upper() == "CRITICAL" and priority == "LOW":
            priority = "HIGH"
        add({
            "title": title,
            "description": description,
            "priority": priority,
            "suggested_action": action,
            "estimated_financial_benefit": benefit,
            "benefit_period": "monthly" if benefit is not None else None,
            "benefit_is_guaranteed": False,
            "category": category or None,
        }, (category.casefold(), title.casefold()))

    low_balance_alerts = [
        alert for alert in alerts if isinstance(alert, dict)
        and "low balance" in str(alert.get("title", "")).lower()
    ]
    for alert in low_balance_alerts:
        title = str(alert.get("title", "Protect your projected balance")).strip()
        date = alert.get("affected_date")
        action = str(alert.get("suggested_action", "Review near-term payments and preserve funds for essential costs."))
        severity = str(alert.get("severity", "HIGH")).upper()
        priority = SEVERITY_TO_PRIORITY.get(severity, "HIGH")
        add({
            "title": "Protect your balance" + (f" before {date}" if date else ""),
            "description": str(alert.get("message", "A low-balance event was detected.")),
            "priority": priority,
            "suggested_action": action,
            "estimated_financial_benefit": None,
            "benefit_period": None,
            "benefit_is_guaranteed": False,
            "category": None,
        }, ("low_balance", str(date or title).casefold()))

    potential = _amount(savings_analysis.get("potential_additional_monthly_savings"))
    if not candidates and potential is not None and potential > 0:
        add({
            "title": "Put identified savings opportunities into a monthly plan",
            "description": "The savings analysis estimates this amount from the available recommendations.",
            "priority": base_priority,
            "suggested_action": "Choose the recommendations that fit your needs and direct any realized savings toward your priorities.",
            "estimated_financial_benefit": potential,
            "benefit_period": "monthly",
            "benefit_is_guaranteed": False,
            "category": None,
        }, ("savings", "monthly plan"))

    # Avoid adding generic risk advice when a more specific alert already has
    # an action. Otherwise use T20's actual risk result to prompt a review.
    risk_level = str(risk_result.get("risk_level", "")).strip().upper()
    if risk_level in {"HIGH", "CRITICAL"} and not any(
        row["priority"] in {"URGENT", "HIGH"} for row in candidates
    ):
        reasons = risk_result.get("reasons", [])
        reason_text = "; ".join(str(reason) for reason in reasons) if isinstance(reasons, list) else str(reasons)
        add({
            "title": "Review the financial risk signals",
            "description": reason_text or f"The supplied risk assessment is {risk_level.lower()}.",
            "priority": SEVERITY_TO_PRIORITY[risk_level],
            "suggested_action": "Review the projected cash flow and prioritize essential payments before discretionary spending.",
            "estimated_financial_benefit": None,
            "benefit_period": None,
            "benefit_is_guaranteed": False,
            "category": None,
        }, ("risk", risk_level.lower()))

    candidates.sort(key=lambda row: (
        PRIORITY_ORDER.get(row["priority"], 3),
        -(row["estimated_financial_benefit"] or 0),
        row["title"].lower(),
    ))
    return {
        "recommendations": candidates,
        "recommendation_count": len(candidates),
        "priority_order": ["URGENT", "HIGH", "MEDIUM", "LOW"],
        "estimated_benefits_are_guaranteed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prioritize T20/T21/T24/T25 results from JSON input.")
    parser.add_argument("input_json", type=Path)
    args = parser.parse_args()
    with args.input_json.open(encoding="utf-8") as file:
        data = json.load(file)
    print(json.dumps(build_recommendations(
        data.get("spending_recommendations"), data.get("savings_analysis"),
        data.get("risk_result"), data.get("alerts"),
    ), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
