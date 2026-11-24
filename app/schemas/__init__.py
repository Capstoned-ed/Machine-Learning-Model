"""Pydantic schemas for the RegQuest ML microservice."""

from .forecasting import (
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
