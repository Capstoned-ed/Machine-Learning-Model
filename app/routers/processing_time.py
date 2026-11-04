from fastapi import APIRouter, Depends, HTTPException
from ..schemas import ProcessingTimeRequest, ProcessingTimeResponse
from ..dependencies import ModelManager, get_model_manager

router = APIRouter(tags=["Processing Time"])


@router.post("/predict/processing-time", response_model=ProcessingTimeResponse)
def predict_processing_time(
    req: ProcessingTimeRequest,
    manager: ModelManager = Depends(get_model_manager)
):
    if not manager.processing_baseline:
        raise HTTPException(
            status_code=503,
            detail="Processing time estimation model artifact is not loaded."
        )

    prediction = manager.processing_baseline.predict_one(
        credential_type=req.credential_type,
        purpose=req.purpose,
        num_docs=req.num_documents or 1
    )

    return ProcessingTimeResponse(
        status="success",
        predicted_processing_time=prediction["predicted_processing_time"],
        unit=prediction["unit"],
        model_version=prediction["model_version"],
        basis=prediction["basis"],
        is_empirical=prediction["is_empirical"],
        disclaimer=prediction.get("disclaimer")
    )

