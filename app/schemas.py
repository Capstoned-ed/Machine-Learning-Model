"""
Backward-compatibility re-export module for app.schemas.
"""

from .schemas.forecasting import (
    HealthCheckResponse,
    DailyForecastRequest,
    DailyForecastItem,
    DailyForecastResponse,
    MonthlyWorkloadRequest,
    MonthlyWorkloadResponse,
)

__all__ = [
    "HealthCheckResponse",
    "DailyForecastRequest",
    "DailyForecastItem",
    "DailyForecastResponse",
    "MonthlyWorkloadRequest",
    "MonthlyWorkloadResponse",
]
