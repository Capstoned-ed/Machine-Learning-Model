from datetime import datetime, timedelta
import calendar
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import MonthlyWorkloadRequest, MonthlyWorkloadResponse
from ..dependencies import ModelManager, get_model_manager
from ...src.features import generate_future_operating_dates

router = APIRouter(tags=["Monthly Workload Forecasting"])


@router.post("/forecast/monthly-workload", response_model=MonthlyWorkloadResponse)
def forecast_monthly_workload(
    req: MonthlyWorkloadRequest,
    manager: ModelManager = Depends(get_model_manager)
):
    if not manager.daily_forecaster:
        raise HTTPException(
            status_code=503,
            detail="Daily demand forecasting model artifact is not loaded."
        )

    # Determine target month
    if req.target_month:
        year, month = map(int, req.target_month.split("-"))
    else:
        now = datetime.now()
        # Default to next month
        if now.month == 12:
            year, month = now.year + 1, 1
        else:
            year, month = now.year, now.month + 1

    target_month_str = f"{year:04d}-{month:02d}"

    # Get all operating days in that target month
    num_days_in_month = calendar.monthrange(year, month)[1]
    operating_dates = []
    for day in range(1, num_days_in_month + 1):
        dt = datetime(year, month, day)
        if dt.weekday() < 5:  # Monday to Friday
            operating_dates.append(dt.strftime("%Y-%m-%d"))

    if not operating_dates:
        raise HTTPException(status_code=400, detail="No operating days found for target month.")

    recent_history = manager.metadata.get("recent_history_buffer", [35.0] * 15)

    forecast_items = manager.daily_forecaster.autoregressive_rollout(
        operating_dates=operating_dates,
        recent_history=recent_history
    )

    predicted_total = sum(item["predicted_requests"] for item in forecast_items)
    num_op_days = len(operating_dates)
    daily_avg = round(predicted_total / num_op_days, 1) if num_op_days > 0 else 0.0

    # Classification using thresholds from metadata or defaults
    thresholds = manager.metadata.get("monthly_workload_thresholds", {
        "light_max": 500,
        "moderate_max": 850,
        "heavy_max": 1150
    })

    if predicted_total < thresholds.get("light_max", 500):
        level = "Light"
        desc = "Demand is anticipated to be below typical operational capacity."
    elif predicted_total <= thresholds.get("moderate_max", 850):
        level = "Moderate"
        desc = "Demand is in line with standard registrar operational capacity."
    elif predicted_total <= thresholds.get("heavy_max", 1150):
        level = "Heavy"
        desc = "High volume anticipated. Consider preparing additional verification personnel."
    else:
        level = "Very Heavy"
        desc = "Peak volume anticipated (e.g. enrollment/graduation surge). Maximum staffing recommended."

    explanation = (
        f"Forecasted {predicted_total} total credential requests across {num_op_days} operating days "
        f"(average {daily_avg} requests/day). Classified as '{level}' based on 2025 historical monthly demand quartiles. {desc}"
    )

    return MonthlyWorkloadResponse(
        status="success",
        month=target_month_str,
        predicted_total_requests=predicted_total,
        operating_days=num_op_days,
        average_daily_requests=daily_avg,
        workload_level=level,
        classification_basis="historical_demand",
        model_version=manager.daily_forecaster.model_version,
        explanation=explanation
    )

