# RegQuest Machine Learning Microservice

A production-ready Machine Learning microservice for the **RegQuest** Credential Request Management System.

---

## 1. Capabilities Overview

### A. Document Processing Time Prediction (`/predict/processing-time`)
- **Objective:** Estimates the processing turnaround duration (in operating days) of an individual credential request.
- **Features:** Credential Type (`TOR`, `HD`, `CAV`, `COE`, `CAR`, etc.), Request Purpose, Submission Weekday, Submission Month, Multi-Document Package Flag, Number of Documents.
- **Model:** Defensible administrative standard and scheduled duration baseline (`processing-time-baseline-v1`).
- **Data Limitation Notice:** In the historical 2025 registrar logbooks, only 2.7% of rows recorded turnaround duration, and all recorded entries represented scheduled target lead times rather than physical printing/completion times. In accordance with strict development principles, the service explicitly returns `is_empirical: false` with explanatory disclaimers.

### B. Daily Incoming Request Forecasting (`/forecast/daily`)
- **Objective:** Forecasts incoming credential requests expected on upcoming registrar operating days (Monday–Friday).
- **Features:** Calendar day of week, day of month, month, academic seasonality indicators (peak enrollment/graduation vs. recess), backward-looking autoregressive lags ($t-1, t-2, t-3, t-5, t-10$), and 5-day / 10-day rolling averages and volatility.
- **Model:** Walk-forward validated count regression pipeline (`StandardScaler` + `Ridge` / `PoissonRegressor` / `GradientBoostingRegressor`).
- **Validation:** 4-split expanding-window chronological cross-validation achieving MAE of 23.66 requests/day, MedAE of 20.37 requests/day, and RMSE of 30.18 requests/day (outperforming naive and historical mean baselines).
- **Inference:** Autoregressive rollout engine generating point estimates and 90% prediction intervals.

### C. Monthly Workload Forecasting (`/forecast/monthly-workload`)
- **Objective:** Forecasts total expected monthly request volume and classifies registrar workload into operational tiers.
- **Formula:** $\text{Monthly Forecast} = \sum_{t \in \text{Operating Days}} \hat{y}_t$
- **Workload Classification Tiers (Derived from 2025 Historical Quartiles):**
  - **Light:** $< 500$ requests/month (e.g., December, October)
  - **Moderate:** $500 - 850$ requests/month (e.g., April, November, February, May)
  - **Heavy:** $850 - 1,150$ requests/month (e.g., July, September, January)
  - **Very Heavy:** $> 1,150$ requests/month (e.g., June graduation, August enrollment peaks)

---

## 2. Directory Structure

```
D:\Capstone\ML\
├── app/
│   ├── main.py                     # FastAPI entrypoint
│   ├── config.py                   # Port, host, and path configuration
│   ├── schemas.py                  # Pydantic v2 input/output validation models
│   ├── dependencies.py             # ModelManager artifact loader
│   └── routers/
│       ├── health.py               # GET /health
│       ├── processing_time.py      # POST /predict/processing-time
│       ├── daily_forecast.py       # POST /forecast/daily
│       └── monthly_workload.py     # POST /forecast/monthly-workload
├── artifacts/
│   ├── daily_forecaster.joblib     # Serialized candidate forecaster
│   ├── processing_baseline.joblib  # Serialized turnaround baseline
│   ├── metadata.json               # Model versioning, metrics, and thresholds
│   └── evaluation_report.json      # Chronological walk-forward validation report
├── data/
│   ├── raw/                        # Original 12 monthly CSV logbooks (untouched)
│   ├── processed/
│   │   ├── cleaned_requests.csv    # 9,265 validated tabular records
│   │   ├── rejected_records.csv    # Unresolved records log (0 records)
│   │   └── daily_time_series.csv   # 245 daily aggregate observations
│   └── reports/
│       └── data_quality_report.json # Comprehensive audit log of 228 repaired dates
├── src/
│   ├── pipeline.py                 # Pure Python data loading & validation pipeline
│   ├── features.py                 # Backward-looking lag & calendar feature extractors
│   ├── evaluate.py                 # Chronological walk-forward evaluator
│   ├── train.py                    # Master model training & artifact builder
│   ├── retrain.py                  # Retraining workflow with champion-challenger gating
│   └── models/
│       ├── baselines.py            # Historical mean, naive, and rolling mean baselines
│       ├── forecaster.py           # Count regressors and autoregressive rollout
│       └── processing_time.py      # Processing turnaround baseline model
├── tests/
│   ├── test_pipeline.py            # Data loading, date repair, and credential tests
│   ├── test_models.py              # Baseline, forecaster, and interval tests
│   └── test_api.py                 # FastAPI endpoints and schema tests
├── Dockerfile                      # Production multi-stage Docker build
├── docker-compose.yml              # Local container deployment
├── requirements.txt                # ML service dependencies
└── README.md                       # Microservice documentation
```

---

## 3. Quick Start & Execution

### Running the Data Pipeline
```powershell
& "D:\Capstone\ML\venv\Scripts\python.exe" D:\Capstone\ML\src\pipeline.py
```

### Training & Walk-Forward Validation
```powershell
& "D:\Capstone\ML\venv\Scripts\python.exe" -m ML.src.train
```

### Running Automated Test Suites
```powershell
& "D:\Capstone\ML\venv\Scripts\python.exe" -m pytest ML/tests/ -v
```

### Starting the FastAPI Server
```powershell
& "D:\Capstone\ML\venv\Scripts\python.exe" -m uvicorn ML.app.main:app --host 0.0.0.0 --port 8001 --reload
```
Interactive API docs are available at: `http://localhost:8001/docs`

---

## 4. API Endpoints Reference

### `GET /health`
Returns microservice status, artifact availability, versions, and uptime.

### `POST /predict/processing-time`
Request:
```json
{
  "credential_type": "TOR",
  "purpose": "Employment",
  "date_requested": "2026-11-05",
  "num_documents": 1
}
```
Response:
```json
{
  "status": "success",
  "predicted_processing_time": 6.0,
  "unit": "operating_days",
  "model_version": "processing-time-baseline-v1",
  "basis": "administrative_standard",
  "is_empirical": false,
  "disclaimer": "Notice: Estimated processing duration reflects administrative registrar guidelines and scheduled turnaround. Actual empirical processing timestamps are not yet recorded in sufficient historical volume."
}
```

### `POST /forecast/daily`
Request:
```json
{
  "start_date": "2026-11-09",
  "number_of_operating_days": 5
}
```
Response:
```json
{
  "status": "success",
  "forecast": [
    {
      "date": "2026-11-09",
      "weekday": "Monday",
      "predicted_requests": 46,
      "lower_bound_90": 7,
      "upper_bound_90": 85
    }
  ],
  "model_version": "daily-forecaster-ridge-v1",
  "start_date": "2026-11-09",
  "total_operating_days": 5,
  "total_predicted_requests": 234
}
```

### `POST /forecast/monthly-workload`
Request:
```json
{
  "target_month": "2026-12"
}
```
Response:
```json
{
  "status": "success",
  "month": "2026-12",
  "predicted_total_requests": 366,
  "operating_days": 23,
  "average_daily_requests": 15.9,
  "workload_level": "Light",
  "classification_basis": "historical_demand",
  "model_version": "daily-forecaster-ridge-v1",
  "explanation": "Forecasted 366 total credential requests across 23 operating days (average 15.9 requests/day). Classified as 'Light' based on 2025 historical monthly demand quartiles."
}
```

---

## 5. Django Backend Integration & Security

The Django backend (`Capstone-Backend`) integrates with the ML microservice via a non-blocking service layer (`credentials/ml_client.py`):
- **Role-Based Access Control:**
  - Students can access processing turnaround estimates (`/api/credentials/predict-turnaround/`).
  - Daily and monthly workload forecasting endpoints (`/api/credentials/forecast/daily/` and `/api/credentials/forecast/monthly-workload/`) strictly require `STAFF`, `REGISTRAR`, or `ADMIN` roles; students receive `403 Forbidden`.
- **Fault Tolerance:** If the FastAPI microservice is offline, Django automatically falls back to database master data (`CredentialType.processing_days`), returning `is_fallback: true` so user credential requests never fail.

---

## 6. Retraining & Rollback Workflow

When new operational records become available:
1. Place new monthly CSV logbooks in `ML/data/raw/`.
2. Run the automated retraining script:
   ```powershell
   & "D:\Capstone\ML\venv\Scripts\python.exe" -m ML.src.retrain
   ```
3. The script:
   - Cleans and validates the extended historical dataset.
   - Evaluates candidate models (Poisson, Ridge, Gradient Boosting) using 4 expanding-window chronological splits.
   - Compares the best candidate against the deployed production model's validation MAE.
   - If the candidate demonstrates equivalent or improved performance, it backs up the current model to `artifacts/backups/daily_forecaster_<timestamp>.joblib` and promotes the new champion artifact.
   - If the candidate performs worse, promotion is aborted and previous models are preserved.

