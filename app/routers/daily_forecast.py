from fastapi import APIRouter, Depends, HTTPException
from ..schemas import DailyForecastRequest, DailyForecastResponse, DailyForecastItem
from ..dependencies import ModelManager, get_model_manager
from ...src.features import generate_future_operating_dates

router = APIRouter(tags=["Daily Demand Forecasting"])


@router.post("/forecast/daily", response_model=DailyForecastResponse)
def forecast_daily_demand(
    req: DailyForecastRequest,
    manager: ModelManager = Depends(get_model_manager)
):
    if not manager.daily_forecaster:
        raise HTTPException(
            status_code=503,
            detail="Daily demand forecasting model artifact is not loaded."
        )

    # Generate sequence of future operating days
    operating_dates = generate_future_operating_dates(
        start_date_str=req.start_date,
        num_operating_days=req.number_of_operating_days
    )

    # Use recent history buffer from metadata for autoregressive initialization
    recent_history = manager.metadata.get("recent_history_buffer", [35.0] * 15)

    forecast_items = manager.daily_forecaster.autoregressive_rollout(
        operating_dates=operating_dates,
        recent_history=recent_history
    )

    total_predicted = sum(item["predicted_requests"] for item in forecast_items)

    formatted_items = [
        DailyForecastItem(
            date=item["date"],
            weekday=item["weekday"],
            predicted_requests=item["predicted_requests"],
            lower_bound_90=item["lower_bound_90"],
            upper_bound_90=item["upper_bound_90"]
        )
        for item in forecast_items
    ]

    return DailyForecastResponse(
        status="success",
        forecast=formatted_items,
        model_version=manager.daily_forecaster.model_version,
        start_date=req.start_date,
        total_operating_days=len(formatted_items),
        total_predicted_requests=total_predicted
    )

