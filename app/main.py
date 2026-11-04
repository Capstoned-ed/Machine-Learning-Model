"""
RegQuest Machine Learning Microservice.
FastAPI Application Entrypoint.
Provides endpoints for:
1. Document processing turnaround duration prediction
2. Daily incoming credential request forecasting
3. Monthly workload volume forecasting and classification
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import PROJECT_NAME, VERSION
from .dependencies import ModelManager
from .routers import health, processing_time, daily_forecast, monthly_workload

app = FastAPI(
    title=PROJECT_NAME,
    description="Machine Learning Microservice for RegQuest Credential Management System",
    version=VERSION,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(processing_time.router)
app.include_router(daily_forecast.router)
app.include_router(monthly_workload.router)

# Preload models
ModelManager.get_instance()


@app.get("/", tags=["Root"])
def root():
    return {
        "service": PROJECT_NAME,
        "version": VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ML.app.main:app", host="0.0.0.0", port=8001, reload=True)
