"""
Model Artifact Manager and Dependency Injection Provider for FastAPI.
Loads serialized models and metadata at startup with graceful fallback.
"""

import os
import sys
import json
import time
from typing import Optional, Dict, Any
import joblib

from .config import ARTIFACTS_DIR

BASE_ML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_ML_DIR not in sys.path:
    sys.path.insert(0, BASE_ML_DIR)

START_TIME = time.time()


class ModelManager:
    _instance = None

    def __init__(self):
        self.daily_forecaster = None
        self.processing_baseline = None
        self.metadata = {}
        self.is_loaded = False
        self.load_artifacts()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def load_artifacts(self):
        meta_path = os.path.join(ARTIFACTS_DIR, "metadata.json")
        forecaster_path = os.path.join(ARTIFACTS_DIR, "daily_forecaster.joblib")
        baseline_path = os.path.join(ARTIFACTS_DIR, "processing_baseline.joblib")

        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as fp:
                    self.metadata = json.load(fp)
            except Exception as e:
                print(f"Warning: Failed to load metadata: {e}")

        if os.path.exists(forecaster_path):
            try:
                self.daily_forecaster = joblib.load(forecaster_path)
            except Exception as e:
                print(f"Warning: Failed to load daily forecaster: {e}")

        if os.path.exists(baseline_path):
            try:
                self.processing_baseline = joblib.load(baseline_path)
            except Exception as e:
                print(f"Warning: Failed to load processing baseline: {e}")

        self.is_loaded = bool(self.daily_forecaster and self.processing_baseline)

    def get_status(self) -> Dict[str, Any]:
        return {
            "daily_forecaster_available": self.daily_forecaster is not None,
            "processing_baseline_available": self.processing_baseline is not None,
            "metadata_available": bool(self.metadata),
            "versions": {
                "daily_forecaster": self.metadata.get("daily_forecaster", {}).get("version", "unknown"),
                "processing_time": self.metadata.get("processing_time_baseline", {}).get("version", "unknown")
            },
            "uptime_seconds": round(time.time() - START_TIME, 1)
        }


def get_model_manager() -> ModelManager:
    return ModelManager.get_instance()

