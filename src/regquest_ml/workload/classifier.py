"""
Monthly Workload Volume Forecasting and 4-Tier Operational Classifier.
Derived from daily Random Forest rollout aggregations.
"""

from typing import Dict, Any, List

WORKLOAD_THRESHOLDS = {
    "light_max": 40,
    "moderate_max": 70
}

WORKLOAD_DESCRIPTIONS = {
    "Light": "Low transaction volume; standard registrar staffing is sufficient.",
    "Moderate": "Normal academic operational load; standard queue distribution.",
    "Heavy": "High transaction volume; recommend expedited processing shifts.",
    "Very Heavy": "Peak volume (enrollment / graduation); recommend temporary counter expansion."
}


def classify_workload_tier(total_volume: float, operating_days: int = 1) -> str:
    """
    Classifies request volume into operational workload tier based on daily rate.
    Light: <= 40 requests/day
    Moderate: 41 - 70 requests/day
    Heavy: > 70 requests/day
    """
    daily_rate = total_volume / max(1, operating_days)
    if daily_rate <= WORKLOAD_THRESHOLDS["light_max"]:
        return "Light"
    elif daily_rate <= WORKLOAD_THRESHOLDS["moderate_max"]:
        return "Moderate"
    else:
        return "Heavy"


def calculate_monthly_workload(
    daily_predictions: List[Dict[str, Any]],
    target_month: str = "2026-11"
) -> Dict[str, Any]:
    """
    Sums daily request predictions across operating days to derive monthly workload.
    """
    total_predicted = sum(p["predicted_requests"] for p in daily_predictions)
    op_days = len(daily_predictions)
    daily_avg = round(total_predicted / max(1, op_days), 1)

    tier = classify_workload_tier(total_predicted, op_days)
    desc = WORKLOAD_DESCRIPTIONS.get(tier, "Normal operations.")

    # Capacity utilization based on nominal threshold of (70 * op_days) requests/month
    nominal_cap = float(WORKLOAD_THRESHOLDS["moderate_max"] * max(1, op_days))
    capacity_pct = round((total_predicted / max(1.0, nominal_cap)) * 100.0, 1)

    return {
        "forecast_month": target_month,
        "total_predicted_requests": int(round(total_predicted)),
        "operating_days_count": op_days,
        "average_daily_requests": daily_avg,
        "workload_classification": tier,
        "workload_description": desc,
        "capacity_utilization_pct": capacity_pct,
        "source": "ml_service"
    }
