"""FLOODRIX API v1 - Health and diagnostics endpoints."""

from fastapi import APIRouter, Request
from app.schemas import HealthResponse, ModelInfoResponse

router = APIRouter(tags=["Health & System Diagnostics"])


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    """Verify that backend is reachable and that ML flood model is loaded."""
    predictor = getattr(request.app.state, "predictor", None)
    is_loaded = predictor.is_loaded if predictor else False
    return HealthResponse(
        status="ok",
        service="FLOODRIX",
        version="1.0.0",
        model_loaded=is_loaded,
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info(request: Request) -> ModelInfoResponse:
    """Retrieve trained model metadata, test metrics, and feature configurations."""
    predictor = getattr(request.app.state, "predictor", None)
    meta = predictor.metadata if (predictor and predictor.is_loaded) else {}

    return ModelInfoResponse(
        model_name=meta.get("model_name", "FLOODRIX Calibrated Flood Hazard Predictor"),
        version=meta.get("version", "1.0.0"),
        feature_columns=meta.get("features", {}).get("feature_order", []),
        risk_bands=meta.get("risk_bands", {}),
        test_metrics=meta.get("test_metrics", {}),
        frameworks=meta.get("frameworks", {}),
        calibration_note=meta.get(
            "calibration_note",
            "Probabilities calibrated using held-out spatial blocks."
        ),
    )
