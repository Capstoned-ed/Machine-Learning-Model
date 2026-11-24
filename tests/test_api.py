"""
API Integration and Schema Validation Tests for RegQuest ML Microservice.
Tests forecasting request/response models, endpoint functions, validations, and edge cases.
"""

import unittest
from pydantic import ValidationError
from app.dependencies import ModelManager
from app.schemas import (
    DailyForecastRequest,
    DailyForecastResponse,
    MonthlyWorkloadRequest,
    MonthlyWorkloadResponse,
    HealthCheckResponse
)
from app.routers.health import health_check
from app.routers.daily_forecast import forecast_daily_demand
from app.routers.monthly_workload import forecast_monthly_workload


class TestMLAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.manager = ModelManager.get_instance()

    def test_health_check(self):
        resp = health_check(self.manager)
        self.assertIsInstance(resp, HealthCheckResponse)
        self.assertEqual(resp.status, "ok")
        self.assertTrue(resp.model_availability["daily_forecaster"])
        self.assertIn("daily_forecaster", resp.model_versions)

    def test_forecast_daily_demand(self):
        req = DailyForecastRequest(
            start_date="2026-11-09",
            number_of_operating_days=10
        )
        resp = forecast_daily_demand(req, self.manager)
        self.assertIsInstance(resp, DailyForecastResponse)
        self.assertEqual(resp.status, "success")
        self.assertEqual(len(resp.forecast), 10)
        self.assertGreater(resp.total_predicted_requests, 0)

        for item in resp.forecast:
            self.assertGreaterEqual(item.predicted_requests, 0)
            self.assertLessEqual(item.lower_bound_90, item.predicted_requests)
            self.assertGreaterEqual(item.upper_bound_90, item.predicted_requests)

    def test_forecast_monthly_workload(self):
        req = MonthlyWorkloadRequest(target_month="2026-12")
        resp = forecast_monthly_workload(req, self.manager)
        self.assertIsInstance(resp, MonthlyWorkloadResponse)
        self.assertEqual(resp.status, "success")
        self.assertEqual(resp.month, "2026-12")
        self.assertGreater(resp.predicted_total_requests, 0)
        self.assertGreater(resp.operating_days, 15)
        self.assertIn(resp.workload_level, ["Light", "Moderate", "Heavy"])
        self.assertEqual(resp.classification_basis, "historical_demand")
        self.assertIn("explanation", resp.model_dump())

    def test_invalid_operating_days_range(self):
        with self.assertRaises(ValidationError):
            DailyForecastRequest(
                start_date="2026-11-09",
                number_of_operating_days=150  # Exceeds max 60
            )

    def test_invalid_monthly_format(self):
        with self.assertRaises(ValidationError):
            MonthlyWorkloadRequest(
                target_month="2026/12"  # Bad format
            )


if __name__ == "__main__":
    unittest.main()
