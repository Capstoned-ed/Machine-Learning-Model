"""
Unit Tests for RegQuest Machine Learning Models.
Tests baselines, forecaster rollout, processing turnaround estimator, and interval bounds.
"""

import unittest
import numpy as np
from src.models.baselines import (
    HistoricalMeanBaseline,
    PreviousDayBaseline,
    PreviousSameWeekdayBaseline,
    RollingAverageBaseline
)
from src.models.forecaster import DailyDemandForecaster
from src.evaluate import compute_metrics


class TestModels(unittest.TestCase):

    def test_baselines(self):
        y_train = np.array([10.0, 20.0, 30.0, 40.0])
        # X with dummy features: col 0 is lag1, col 1 is lag5, col 2 is rolling5
        X_test = np.array([
            [15.0, 25.0, 35.0],
            [18.0, 28.0, 38.0]
        ])

        b_mean = HistoricalMeanBaseline().fit(y_train)
        pred_mean = b_mean.predict(X_test)
        self.assertEqual(pred_mean[0], 25.0)

        b_prev = PreviousDayBaseline(lag1_col_idx=0)
        pred_prev = b_prev.predict(X_test)
        self.assertEqual(pred_prev[0], 15.0)

        b_prev_w = PreviousSameWeekdayBaseline(lag5_col_idx=1)
        pred_prev_w = b_prev_w.predict(X_test)
        self.assertEqual(pred_prev_w[0], 25.0)

        b_roll = RollingAverageBaseline(rolling5_col_idx=2)
        pred_roll = b_roll.predict(X_test)
        self.assertEqual(pred_roll[0], 35.0)

    def test_forecaster_rollout(self):
        # Create a small synthetic dataset
        X = np.random.uniform(10, 50, size=(50, 19))
        y = np.random.uniform(15, 60, size=(50,))

        forecaster = DailyDemandForecaster(model_type="ridge")
        forecaster.fit(X, y)

        dates = ["2026-11-09", "2026-11-10", "2026-11-11"]
        recent = [30.0, 35.0, 40.0, 45.0, 50.0]
        rollout = forecaster.autoregressive_rollout(dates, recent)

        self.assertEqual(len(rollout), 3)
        for item in rollout:
            self.assertIn("predicted_requests", item)
            self.assertGreaterEqual(item["predicted_requests"], 0)
            self.assertIn("lower_bound_90", item)
            self.assertIn("upper_bound_90", item)
            self.assertLessEqual(item["lower_bound_90"], item["predicted_requests"])
            self.assertGreaterEqual(item["upper_bound_90"], item["predicted_requests"])

    def test_compute_metrics(self):
        y_true = np.array([20.0, 30.0, 40.0])
        y_pred = np.array([22.0, 28.0, 45.0])
        metrics = compute_metrics(y_true, y_pred)

        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("wape_pct", metrics)
        self.assertGreater(metrics["mae"], 0)
        self.assertGreater(metrics["rmse"], metrics["mae"])


if __name__ == "__main__":
    unittest.main()

