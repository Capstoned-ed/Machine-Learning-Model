"""API route definitions."""
from .daily_forecast import router as daily_forecast_router
from .monthly_workload import router as monthly_workload_router
from .health import router as health_router

__all__ = [
    "daily_forecast_router",
    "monthly_workload_router",
    "health_router",
]
