"""Prediction endpoints for batch segments and route-level flood hazard scoring."""

import time
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas import (
    BatchSegmentsRequest,
    BatchSegmentsResponse,
    RoutePredictRequest,
    RoutePredictResponse,
    SegmentInput,
    SegmentPrediction,
)

router = APIRouter(tags=["Flood Predictions"])


def get_predictor_from_app(request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    if not predictor or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Flood prediction model is not loaded or initialized.",
        )
    return predictor


@router.post("/predict/segments", response_model=BatchSegmentsResponse)
def predict_batch_segments(
    payload: BatchSegmentsRequest,
    request: Request,
) -> BatchSegmentsResponse:
    """Score a batch of road segments and return calibrated flood probabilities and risk bands."""
    predictor = get_predictor_from_app(request)
    predictions, elapsed_ms = predictor.predict_segments(payload.segments)

    return BatchSegmentsResponse(
        segments=predictions,
        total_segments=len(predictions),
        latency_ms=elapsed_ms,
    )


@router.post("/predict/route", response_model=RoutePredictResponse)
def predict_route_risk(
    payload: RoutePredictRequest,
    request: Request,
) -> RoutePredictResponse:
    """Predict flood hazard across ordered segments of a logistics route and determine routing decision."""
    predictor = get_predictor_from_app(request)
    return predictor.predict_route(payload.route_id, payload.segments)


# =========================================================================
# Aliases / Endpoints matching FLOODRIX Mobile API Specification (v1)
# =========================================================================

@router.post("/prediction/flood", response_model=SegmentPrediction)
def predict_single_point(
    payload: SegmentInput,
    request: Request,
) -> SegmentPrediction:
    """Predict flood probability for a single geographic location."""
    predictor = get_predictor_from_app(request)
    predictions, _ = predictor.predict_segments([payload])
    return predictions[0]


@router.post("/prediction/route", response_model=RoutePredictResponse)
def predict_route_risk_alias(
    payload: RoutePredictRequest,
    request: Request,
) -> RoutePredictResponse:
    """Predict flood hazard for route segments matching Mobile App API spec."""
    predictor = get_predictor_from_app(request)
    return predictor.predict_route(payload.route_id, payload.segments)
